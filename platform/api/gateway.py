"""API Gateway -- main FastAPI application for Open Integration Platform by Pinquark.com."""

import time
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any

import httpx
import structlog
from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import flag_modified

from api.auth import generate_api_key, get_current_tenant
from api.schemas import (
    ApiKeyCreate,
    ApiKeyResponse,
    ConnectorInstanceCreate,
    ConnectorInstanceResponse,
    ConnectorResponse,
    CredentialStore,
    EventTrigger,
    FlowCreate,
    FlowExecutionDetailResponse,
    FlowExecutionResponse,
    FlowResponse,
    FlowUpdate,
    HealthResponse,
    TenantCreate,
    TenantResponse,
    WorkflowCreate,
    WorkflowExecutionDetailResponse,
    WorkflowExecutionResponse,
    WorkflowResponse,
    WorkflowTestRequest,
    WorkflowUpdate,
)
from config import settings
from core.action_dispatcher import dispatch_action, _ensure_email_account, _resolve_service_url
from core.pii_redactor import redact_execution_detail
from core.connector_registry import ConnectorRegistry
from core.credential_vault import CredentialVault
from core.flow_engine import FlowEngine
from core.mapping_resolver import MappingResolver
from core.redis_client import close_redis, get_redis, redis_health
from core.workflow_engine import WorkflowEngine
from db.base import async_session_factory, get_db
from db.models import ApiKey, ConnectorInstance, Credential, Flow, FlowExecution, Tenant, Workflow, WorkflowExecution
from middleware.rate_limiter import RateLimiterMiddleware

logger = structlog.get_logger()

_start_time = time.time()
registry = ConnectorRegistry(settings.connector_discovery_path)
vault = CredentialVault()
mapping_resolver = MappingResolver(settings.connector_discovery_path)
flow_engine = FlowEngine(mapping_resolver)
workflow_engine = WorkflowEngine()


@asynccontextmanager
async def lifespan(app: FastAPI):  # type: ignore[no-untyped-def]
    from db.base import Base, engine
    import db.models  # noqa: F401 — ensure all models are registered

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await logger.ainfo("database_tables_ready")

    await get_redis()
    await logger.ainfo("redis_connected")

    count = registry.discover()
    await logger.ainfo("connectors_discovered", count=count)

    async def _execute_connector_action(
        connector_name: str,
        action: str,
        payload: dict,
        tenant_id: Any,
        credential_name: str = "default",
    ) -> dict:
        credentials: dict[str, str] | None = None
        try:
            async with async_session_factory() as db_session:
                credentials = await vault.retrieve_all(
                    db_session, tenant_id, connector_name, credential_name=credential_name
                )
        except Exception:
            pass
        return await dispatch_action(
            connector_name=connector_name,
            action=action,
            payload=payload,
            tenant_id=tenant_id,
            credentials=credentials,
        )

    workflow_engine.set_action_executor(_execute_connector_action)
    await logger.ainfo("workflow_engine_action_executor_ready")

    import asyncio

    async def _provision_trigger_email_accounts() -> None:
        """Register email accounts on the connector for active workflow/flow triggers."""
        await asyncio.sleep(5)
        try:
            async with async_session_factory() as db_session:
                wf_result = await db_session.execute(
                    select(Workflow).where(
                        Workflow.trigger_connector == "email-client",
                        Workflow.is_enabled.is_(True),
                    )
                )
                workflows = wf_result.scalars().all()

                fl_result = await db_session.execute(
                    select(Flow).where(
                        Flow.source_connector == "email-client",
                        Flow.is_enabled.is_(True),
                    )
                )
                flows = fl_result.scalars().all()

                credential_pairs: set[tuple[Any, str]] = set()
                for wf in workflows:
                    for node in (wf.nodes or []):
                        if node.get("type") == "trigger" and node.get("config", {}).get("connector_name") == "email-client":
                            cred_name = node["config"].get("credential_name", "default")
                            credential_pairs.add((wf.tenant_id, cred_name))
                for fl in flows:
                    credential_pairs.add((fl.tenant_id, "default"))

                base_url = _resolve_service_url("email-client")
                for tenant_id, cred_name in credential_pairs:
                    try:
                        creds = await vault.retrieve_all(db_session, tenant_id, "email-client", credential_name=cred_name)
                        if creds:
                            if "account_name" not in creds:
                                creds["account_name"] = cred_name
                            account_name = await _ensure_email_account(base_url, creds)
                            await logger.ainfo(
                                "trigger_email_account_provisioned",
                                tenant_id=str(tenant_id),
                                credential=cred_name,
                                account=account_name,
                            )
                    except Exception:
                        await logger.aexception(
                            "trigger_email_account_provision_failed",
                            tenant_id=str(tenant_id),
                            credential=cred_name,
                        )
        except Exception:
            await logger.aexception("trigger_email_provision_scan_failed")

    asyncio.create_task(_provision_trigger_email_accounts())

    yield

    await close_redis()
    await logger.ainfo("redis_disconnected")


app = FastAPI(
    title="Open Integration Platform by Pinquark.com",
    version="0.1.0",
    description="Open-source integration hub — connect any system with any other system.",
    lifespan=lifespan,
)

app.add_middleware(RateLimiterMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Health ---


@app.get("/health", response_model=HealthResponse, tags=["health"])
async def health_check() -> HealthResponse:
    redis_ok = await redis_health()
    return HealthResponse(
        status="healthy" if redis_ok else "degraded",
        version="0.1.0",
        uptime_seconds=round(time.time() - _start_time, 1),
        checks={
            "database": "ok",
            "redis": "ok" if redis_ok else "error",
            "registry": "ok",
        },
    )


# --- Connectors (public catalog) ---


@app.get("/api/v1/connectors", response_model=list[ConnectorResponse], tags=["connectors"])
async def list_connectors(
    category: str | None = Query(None),
    interface: str | None = Query(None),
    capability: str | None = Query(None),
) -> list[ConnectorResponse]:
    results = registry.search(category=category, interface=interface, capability=capability)
    return [
        ConnectorResponse(
            name=c.name,
            category=c.category,
            version=c.version,
            display_name=c.display_name,
            description=c.description,
            country=c.country,
            logo_url=c.logo_url,
            website_url=c.website_url,
            interface=c.interface,
            capabilities=c.capabilities,
            events=c.events,
            actions=c.actions,
            config_schema=c.config_schema,
            api_endpoints=c.api_endpoints,
            event_fields=c.event_fields,
            action_fields=c.action_fields,
        )
        for c in results
    ]


@app.get("/api/v1/connectors/{name}/openapi", tags=["connectors"])
async def get_connector_openapi(name: str):
    """Proxy to connector's /openapi.json endpoint for Swagger UI embedding."""
    from core.action_dispatcher import _CONNECTOR_SERVICE_NAMES, DEFAULT_CONNECTOR_PORT

    service = _CONNECTOR_SERVICE_NAMES.get(name, f"connector-{name}")
    url = f"http://{service}:{DEFAULT_CONNECTOR_PORT}/openapi.json"

    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.get(url)
            resp.raise_for_status()
            spec = resp.json()
            spec["servers"] = [{"url": f"/connector-proxy/{name}", "description": "Connector API"}]
            return spec
        except httpx.ConnectError:
            raise HTTPException(status_code=503, detail=f"Connector '{name}' is not reachable")
        except httpx.HTTPStatusError as exc:
            raise HTTPException(status_code=exc.response.status_code, detail="Failed to fetch OpenAPI spec")


@app.get("/api/v1/connectors/{category}/{name}", response_model=ConnectorResponse, tags=["connectors"])
async def get_connector(category: str, name: str) -> ConnectorResponse:
    connector = registry.get_latest(category, name)
    if not connector:
        raise HTTPException(status_code=404, detail=f"Connector {category}/{name} not found")
    return ConnectorResponse(
        name=connector.name,
        category=connector.category,
        version=connector.version,
        display_name=connector.display_name,
        description=connector.description,
        country=connector.country,
        logo_url=connector.logo_url,
        website_url=connector.website_url,
        interface=connector.interface,
        capabilities=connector.capabilities,
        events=connector.events,
        actions=connector.actions,
        config_schema=connector.config_schema,
        api_endpoints=connector.api_endpoints,
        event_fields=connector.event_fields,
        action_fields=connector.action_fields,
    )


# --- Tenant management ---


@app.post("/api/v1/tenants", response_model=TenantResponse, tags=["tenants"])
async def create_tenant(body: TenantCreate, db: AsyncSession = Depends(get_db)) -> TenantResponse:
    tenant = Tenant(name=body.name, slug=body.slug)
    db.add(tenant)
    await db.commit()
    await db.refresh(tenant)
    return TenantResponse.model_validate(tenant)


@app.post("/api/v1/tenants/{tenant_id}/api-keys", response_model=ApiKeyResponse, tags=["tenants"])
async def create_api_key(
    tenant_id: str,
    body: ApiKeyCreate,
    db: AsyncSession = Depends(get_db),
) -> ApiKeyResponse:
    raw_key, key_hash = generate_api_key()
    api_key = ApiKey(
        tenant_id=tenant_id,
        key_hash=key_hash,
        key_prefix=raw_key[:10],
        name=body.name,
    )
    db.add(api_key)
    await db.commit()
    await db.refresh(api_key)
    response = ApiKeyResponse.model_validate(api_key)
    response.raw_key = raw_key
    return response


# --- Connector Instances (per tenant) ---


@app.post(
    "/api/v1/connector-instances",
    response_model=ConnectorInstanceResponse,
    tags=["connector-instances"],
)
async def activate_connector(
    body: ConnectorInstanceCreate,
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
) -> ConnectorInstanceResponse:
    instance = ConnectorInstance(
        tenant_id=tenant.id,
        connector_name=body.connector_name,
        connector_version=body.connector_version,
        connector_category=body.connector_category,
        display_name=body.display_name or body.connector_name,
        config=body.config,
    )
    db.add(instance)
    await db.commit()
    await db.refresh(instance)
    return ConnectorInstanceResponse.model_validate(instance)


@app.get(
    "/api/v1/connector-instances",
    response_model=list[ConnectorInstanceResponse],
    tags=["connector-instances"],
)
async def list_connector_instances(
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
) -> list[ConnectorInstanceResponse]:
    result = await db.execute(
        select(ConnectorInstance).where(ConnectorInstance.tenant_id == tenant.id)
    )
    instances = result.scalars().all()
    return [ConnectorInstanceResponse.model_validate(i) for i in instances]


@app.delete(
    "/api/v1/connector-instances/{instance_id}",
    tags=["connector-instances"],
)
async def deactivate_connector(
    instance_id: str,
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    result = await db.execute(
        select(ConnectorInstance).where(
            ConnectorInstance.id == instance_id,
            ConnectorInstance.tenant_id == tenant.id,
        )
    )
    instance = result.scalar_one_or_none()
    if not instance:
        raise HTTPException(status_code=404, detail="Connector instance not found")
    await db.delete(instance)
    await db.commit()
    return {"status": "deactivated"}


# --- Credentials ---


@app.get("/api/v1/credentials", tags=["credentials"])
async def list_credentials(
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    result = await db.execute(
        select(
            Credential.connector_name,
            Credential.credential_name,
            func.array_agg(Credential.credential_key).label("keys"),
            func.max(Credential.updated_at).label("updated_at"),
        )
        .where(Credential.tenant_id == tenant.id)
        .group_by(Credential.connector_name, Credential.credential_name)
    )
    rows = result.all()
    connector_map = {c.name: c for c in registry.get_all()}
    items = []
    for row in rows:
        connector = connector_map.get(row.connector_name)
        items.append({
            "connector_name": row.connector_name,
            "credential_name": row.credential_name,
            "display_name": connector.display_name if connector else row.connector_name,
            "category": connector.category if connector else "",
            "keys": sorted(row.keys),
            "updated_at": row.updated_at.isoformat() if row.updated_at else None,
        })
    return items


async def _propagate_credential_rename(
    db: AsyncSession,
    tenant_id: Any,
    connector_name: str,
    old_name: str,
    new_name: str,
) -> int:
    """Update all workflow nodes that reference the renamed credential."""
    result = await db.execute(
        select(Workflow).where(Workflow.tenant_id == tenant_id)
    )
    workflows = result.scalars().all()
    updated = 0
    for wf in workflows:
        nodes = wf.nodes or []
        changed = False
        for node in nodes:
            cfg = node.get("config", {})
            if cfg.get("credential_name") != old_name:
                continue
            node_connector = cfg.get("connector_name", "")
            node_type = node.get("type", "")
            matches_connector = node_connector == connector_name
            matches_think = node_type == "think" and connector_name == "ai-agent"
            if matches_connector or matches_think:
                cfg["credential_name"] = new_name
                changed = True
        if changed:
            wf.nodes = list(nodes)
            flag_modified(wf, "nodes")
            updated += 1
    return updated


@app.post("/api/v1/credentials", tags=["credentials"])
async def store_credentials(
    body: CredentialStore,
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    is_rename = (
        body.old_credential_name
        and body.old_credential_name != body.credential_name
    )

    if is_rename:
        old_creds = await vault.retrieve_all(
            db, tenant.id, body.connector_name,
            credential_name=body.old_credential_name,  # type: ignore[arg-type]
        )
        merged = {**old_creds, **{k: v for k, v in body.credentials.items() if v}}
        for key, value in merged.items():
            await vault.store(
                db, tenant.id, body.connector_name, key, value,
                credential_name=body.credential_name,
            )
        await vault.delete(
            db, tenant.id, body.connector_name,
            credential_name=body.old_credential_name,
        )
        workflows_updated = await _propagate_credential_rename(
            db, tenant.id, body.connector_name,
            body.old_credential_name,  # type: ignore[arg-type]
            body.credential_name,
        )
    else:
        workflows_updated = 0
        for key, value in body.credentials.items():
            if value:
                await vault.store(
                    db, tenant.id, body.connector_name, key, value,
                    credential_name=body.credential_name,
                )

    await db.commit()
    return {
        "status": "stored",
        "connector": body.connector_name,
        "credential_name": body.credential_name,
        "keys": list(body.credentials.keys()),
        "workflows_updated": workflows_updated,
    }


_SECRET_KEY_PATTERNS = {"password", "secret", "token", "key"}


def _is_secret_key(key: str) -> bool:
    lower = key.lower()
    return any(p in lower for p in _SECRET_KEY_PATTERNS)


@app.get("/api/v1/credentials/{connector_name}", tags=["credentials"])
async def get_credentials(
    connector_name: str,
    credential_name: str = Query("default"),
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    creds = await vault.retrieve_all(db, tenant.id, connector_name, credential_name=credential_name)
    values: dict[str, str] = {}
    for k, v in creds.items():
        values[k] = "" if _is_secret_key(k) else v
    return {
        "connector": connector_name,
        "credential_name": credential_name,
        "keys": list(creds.keys()),
        "values": values,
        "has_credentials": len(creds) > 0,
    }


@app.get("/api/v1/credentials/{connector_name}/names", tags=["credentials"])
async def list_credential_names(
    connector_name: str,
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
) -> list[str]:
    return await vault.list_credential_names(db, tenant.id, connector_name)


@app.delete("/api/v1/credentials/{connector_name}", tags=["credentials"])
async def delete_credentials(
    connector_name: str,
    credential_name: str = Query(None),
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    affected: list[str] = []
    if credential_name:
        result = await db.execute(
            select(Workflow).where(Workflow.tenant_id == tenant.id)
        )
        for wf in result.scalars().all():
            for node in (wf.nodes or []):
                cfg = node.get("config", {})
                if cfg.get("credential_name") != credential_name:
                    continue
                cn = cfg.get("connector_name", "")
                nt = node.get("type", "")
                if cn == connector_name or (nt == "think" and connector_name == "ai-agent"):
                    affected.append(wf.name)
                    break
    deleted = await vault.delete(db, tenant.id, connector_name, credential_name=credential_name)
    await db.commit()
    return {
        "status": "deleted",
        "connector": connector_name,
        "credential_name": credential_name,
        "keys_deleted": deleted,
        "affected_workflows": affected,
    }


def _normalize_wms_url(raw: str) -> str:
    url = raw.rstrip("/")
    for suffix in ("/auth/sign-in", "/auth/refresh-token", "/auth"):
        if url.endswith(suffix):
            url = url[: -len(suffix)]
            break
    return url


async def _validate_wms_credentials(creds: dict[str, str]) -> dict[str, Any]:
    """Validate WMS credentials by attempting JWT login."""
    api_url = _normalize_wms_url(creds.get("api_url", ""))
    username = creds.get("username", "")
    password = creds.get("password", "")

    if not api_url or not username or not password:
        return {
            "status": "failed",
            "message": "Missing required credentials: api_url, username, password",
        }

    start = time.monotonic()
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(connect=10, read=15, write=10, pool=10)) as client:
            resp = await client.post(
                f"{api_url}/auth/sign-in",
                json={"username": username, "password": password},
            )
        elapsed_ms = int((time.monotonic() - start) * 1000)

        if resp.status_code == 200:
            data = resp.json()
            if data.get("accessToken"):
                return {"status": "success", "message": "Authentication successful", "response_time_ms": elapsed_ms}
        if resp.status_code == 401:
            return {"status": "failed", "message": "Invalid username or password", "response_time_ms": elapsed_ms}
        return {
            "status": "failed",
            "message": f"Unexpected response (HTTP {resp.status_code})",
            "response_time_ms": elapsed_ms,
        }
    except httpx.ConnectError:
        elapsed_ms = int((time.monotonic() - start) * 1000)
        return {"status": "failed", "message": f"Cannot connect to {api_url}", "response_time_ms": elapsed_ms}
    except httpx.TimeoutException:
        elapsed_ms = int((time.monotonic() - start) * 1000)
        return {"status": "failed", "message": "Connection timed out", "response_time_ms": elapsed_ms}
    except Exception as exc:
        elapsed_ms = int((time.monotonic() - start) * 1000)
        return {"status": "failed", "message": str(exc), "response_time_ms": elapsed_ms}


async def _validate_email_credentials(creds: dict[str, str]) -> dict[str, Any]:
    """Validate email credentials by testing IMAP and SMTP connectivity."""
    import imaplib
    import smtplib
    import asyncio
    from functools import partial

    imap_host = creds.get("imap_host", "")
    smtp_host = creds.get("smtp_host", "")
    email_address = creds.get("email_address", "")
    username = creds.get("username", "")
    login = username or email_address
    password = creds.get("password", "")
    imap_port = int(creds.get("imap_port", "993"))
    smtp_port = int(creds.get("smtp_port", "587"))
    use_ssl = creds.get("use_ssl", "true").lower() in ("true", "1", "yes")

    if not imap_host or not smtp_host or not email_address or not password:
        return {
            "status": "failed",
            "message": "Missing required credentials: imap_host, smtp_host, email_address, password",
        }

    loop = asyncio.get_event_loop()
    results: dict[str, Any] = {}
    start = time.monotonic()

    # --- IMAP ---
    try:
        def _test_imap() -> str:
            if use_ssl:
                conn = imaplib.IMAP4_SSL(imap_host, imap_port, timeout=10)
            else:
                conn = imaplib.IMAP4(imap_host, imap_port, timeout=10)
            conn.login(login, password)
            conn.logout()
            return "ok"

        await loop.run_in_executor(None, _test_imap)
        results["imap"] = "ok"
    except imaplib.IMAP4.error as exc:
        results["imap"] = f"auth_failed: {exc}"
    except OSError as exc:
        results["imap"] = f"connection_failed: {exc}"
    except Exception as exc:
        results["imap"] = f"error: {exc}"

    # --- SMTP ---
    try:
        def _test_smtp() -> str:
            if use_ssl and smtp_port == 465:
                server = smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=10)
            else:
                server = smtplib.SMTP(smtp_host, smtp_port, timeout=10)
                server.ehlo()
                if use_ssl:
                    server.starttls()
                    server.ehlo()
            server.login(login, password)
            server.quit()
            return "ok"

        await loop.run_in_executor(None, _test_smtp)
        results["smtp"] = "ok"
    except smtplib.SMTPAuthenticationError as exc:
        results["smtp"] = f"auth_failed: {exc}"
    except OSError as exc:
        results["smtp"] = f"connection_failed: {exc}"
    except Exception as exc:
        results["smtp"] = f"error: {exc}"

    elapsed_ms = int((time.monotonic() - start) * 1000)

    if results["imap"] == "ok" and results["smtp"] == "ok":
        return {
            "status": "success",
            "message": "IMAP and SMTP connection successful",
            "response_time_ms": elapsed_ms,
            "details": results,
        }

    return {
        "status": "failed",
        "message": "Connection test failed",
        "response_time_ms": elapsed_ms,
        "details": results,
    }


async def _validate_ai_agent_credentials(creds: dict[str, str]) -> dict[str, Any]:
    """Validate AI Agent credentials by testing Gemini API key with a minimal request."""
    api_key = creds.get("gemini_api_key", "")
    model_name = creds.get("model_name", "gemini-2.5-flash")

    if not api_key:
        return {
            "status": "failed",
            "message": "Missing required credential: gemini_api_key",
        }

    start = time.monotonic()
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(connect=10, read=15, write=10, pool=10)) as client:
            resp = await client.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent",
                params={"key": api_key},
                json={"contents": [{"parts": [{"text": "Say OK"}]}]},
            )
        elapsed_ms = int((time.monotonic() - start) * 1000)

        if resp.status_code == 200:
            return {
                "status": "success",
                "message": f"Gemini API key valid (model: {model_name})",
                "response_time_ms": elapsed_ms,
            }
        if resp.status_code in (401, 403):
            return {
                "status": "failed",
                "message": "Invalid or unauthorized Gemini API key",
                "response_time_ms": elapsed_ms,
            }
        body = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {}
        error_msg = body.get("error", {}).get("message", f"HTTP {resp.status_code}")
        return {
            "status": "failed",
            "message": f"Gemini API error: {error_msg}",
            "response_time_ms": elapsed_ms,
        }
    except httpx.ConnectError:
        elapsed_ms = int((time.monotonic() - start) * 1000)
        return {"status": "failed", "message": "Cannot connect to Gemini API", "response_time_ms": elapsed_ms}
    except httpx.TimeoutException:
        elapsed_ms = int((time.monotonic() - start) * 1000)
        return {"status": "failed", "message": "Gemini API connection timed out", "response_time_ms": elapsed_ms}
    except Exception as exc:
        elapsed_ms = int((time.monotonic() - start) * 1000)
        return {"status": "failed", "message": str(exc), "response_time_ms": elapsed_ms}


async def _validate_invoice_ocr_credentials(creds: dict[str, str]) -> dict[str, Any]:
    login = creds.get("login", "")
    password = creds.get("password", "")
    api_url = creds.get("api_url", "https://skanujfakture.pl:8443/SFApi").rstrip("/")

    if not login or not password:
        return {
            "status": "failed",
            "message": "Missing required credentials: login and password",
        }

    import base64

    credentials_b64 = base64.b64encode(f"{login}:{password}".encode()).decode()
    start = time.monotonic()
    try:
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(connect=10, read=15, write=10, pool=10),
            verify=True,
        ) as client:
            resp = await client.get(
                f"{api_url}/users/currentUser/companies",
                headers={"Authorization": f"Basic {credentials_b64}"},
            )
        elapsed_ms = int((time.monotonic() - start) * 1000)

        if resp.status_code == 200:
            companies = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else []
            count = len(companies) if isinstance(companies, list) else 0
            return {
                "status": "success",
                "message": f"SkanujFakture login OK — {count} company(ies) accessible",
                "response_time_ms": elapsed_ms,
            }
        if resp.status_code in (401, 403):
            return {
                "status": "failed",
                "message": "Invalid login or password for SkanujFakture",
                "response_time_ms": elapsed_ms,
            }
        return {
            "status": "failed",
            "message": f"SkanujFakture API error: HTTP {resp.status_code}",
            "response_time_ms": elapsed_ms,
        }
    except httpx.ConnectError:
        elapsed_ms = int((time.monotonic() - start) * 1000)
        return {"status": "failed", "message": f"Cannot connect to SkanujFakture API at {api_url}", "response_time_ms": elapsed_ms}
    except httpx.TimeoutException:
        elapsed_ms = int((time.monotonic() - start) * 1000)
        return {"status": "failed", "message": "SkanujFakture API connection timed out", "response_time_ms": elapsed_ms}
    except Exception as exc:
        elapsed_ms = int((time.monotonic() - start) * 1000)
        return {"status": "failed", "message": str(exc), "response_time_ms": elapsed_ms}


_INTERFACE_VALIDATORS: dict[str, Any] = {
    "wms": _validate_wms_credentials,
    "email": _validate_email_credentials,
    "ai-agent": _validate_ai_agent_credentials,
    "invoice-ocr": _validate_invoice_ocr_credentials,
}


@app.post("/api/v1/credentials/{connector_name}/validate", tags=["credentials"])
async def validate_credentials(
    connector_name: str,
    credential_name: str = Query("default"),
    body: CredentialStore | None = None,
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    cred_name = body.credential_name if body and body.credential_name else credential_name
    stored = await vault.retrieve_all(db, tenant.id, connector_name, credential_name=cred_name)

    if body and body.credentials:
        merged = {**stored, **{k: v for k, v in body.credentials.items() if v}}
    else:
        merged = stored

    if not merged:
        raise HTTPException(status_code=404, detail="No credentials found for this connector")

    connectors = registry.get_by_name(connector_name)
    connector = connectors[0] if connectors else None
    interface = connector.interface if connector else "generic"

    validator = _INTERFACE_VALIDATORS.get(interface)
    if not validator:
        return {"status": "unsupported", "message": f"Validation not yet supported for interface '{interface}'"}

    return await validator(merged)


# --- Flows ---


@app.post("/api/v1/flows", response_model=FlowResponse, tags=["flows"])
async def create_flow(
    body: FlowCreate,
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
) -> FlowResponse:
    flow = Flow(
        tenant_id=tenant.id,
        name=body.name,
        source_connector=body.source_connector,
        source_event=body.source_event,
        source_filter=body.source_filter,
        destination_connector=body.destination_connector,
        destination_action=body.destination_action,
        field_mapping=body.field_mapping,
        transform=body.transform,
        on_error=body.on_error,
        max_retries=body.max_retries,
    )
    db.add(flow)
    await db.commit()
    await db.refresh(flow)
    return FlowResponse.model_validate(flow)


@app.get("/api/v1/flows", response_model=list[FlowResponse], tags=["flows"])
async def list_flows(
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
) -> list[FlowResponse]:
    result = await db.execute(select(Flow).where(Flow.tenant_id == tenant.id))
    flows = result.scalars().all()
    return [FlowResponse.model_validate(f) for f in flows]


@app.delete("/api/v1/flows/{flow_id}", tags=["flows"])
async def delete_flow(
    flow_id: str,
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    result = await db.execute(
        select(Flow).where(Flow.id == flow_id, Flow.tenant_id == tenant.id)
    )
    flow = result.scalar_one_or_none()
    if not flow:
        raise HTTPException(status_code=404, detail="Flow not found")
    await db.delete(flow)
    await db.commit()
    return {"status": "deleted"}


@app.patch("/api/v1/flows/{flow_id}", response_model=FlowResponse, tags=["flows"])
async def update_flow(
    flow_id: str,
    body: FlowUpdate,
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
) -> FlowResponse:
    result = await db.execute(
        select(Flow).where(Flow.id == flow_id, Flow.tenant_id == tenant.id)
    )
    flow = result.scalar_one_or_none()
    if not flow:
        raise HTTPException(status_code=404, detail="Flow not found")

    update_data = body.model_dump(exclude_none=True)
    for key, value in update_data.items():
        setattr(flow, key, value)

    await db.commit()
    await db.refresh(flow)
    return FlowResponse.model_validate(flow)


# --- Event Processing ---


@app.post("/api/v1/events", tags=["events"])
async def trigger_event(
    body: EventTrigger,
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    async def execute_action_for_flow(
        connector_name: str,
        action: str,
        payload: dict,
        tenant_id: Any,
        credential_name: str = "default",
    ) -> dict:
        credentials: dict[str, str] | None = None
        try:
            credentials = await vault.retrieve_all(
                db, tenant_id, connector_name, credential_name=credential_name
            )
        except Exception:
            pass
        return await dispatch_action(
            connector_name=connector_name,
            action=action,
            payload=payload,
            tenant_id=tenant_id,
            credentials=credentials,
        )

    flow_executions = await flow_engine.process_event(
        db=db,
        tenant_id=tenant.id,
        connector_name=body.connector_name,
        event=body.event,
        event_data=body.data,
        execute_action_fn=execute_action_for_flow,
    )

    workflow_executions = await workflow_engine.process_event(
        db=db,
        tenant_id=tenant.id,
        connector_name=body.connector_name,
        event=body.event,
        event_data=body.data,
    )

    await db.commit()

    return {
        "event": body.event,
        "connector": body.connector_name,
        "flows_triggered": len(flow_executions),
        "workflows_triggered": len(workflow_executions),
        "executions": [
            {"flow_id": str(e.flow_id), "status": e.status, "duration_ms": e.duration_ms}
            for e in flow_executions
        ],
        "workflow_executions": [
            {"workflow_id": str(e.workflow_id), "status": e.status, "duration_ms": e.duration_ms}
            for e in workflow_executions
        ],
    }


@app.post("/internal/events", tags=["internal"])
async def internal_trigger_event(
    body: EventTrigger,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Internal event endpoint for connector-to-platform communication.

    No API key required — trusted within the Docker network.
    Uses the first active tenant for processing.
    """
    result = await db.execute(
        select(Tenant).where(Tenant.is_active.is_(True)).limit(1)
    )
    tenant = result.scalar_one_or_none()
    if not tenant:
        raise HTTPException(status_code=500, detail="No active tenant")

    async def execute_action_for_flow(
        connector_name: str,
        action: str,
        payload: dict,
        tenant_id: Any,
        credential_name: str = "default",
    ) -> dict:
        credentials: dict[str, str] | None = None
        try:
            credentials = await vault.retrieve_all(
                db, tenant_id, connector_name, credential_name=credential_name
            )
        except Exception:
            pass
        return await dispatch_action(
            connector_name=connector_name,
            action=action,
            payload=payload,
            tenant_id=tenant_id,
            credentials=credentials,
        )

    flow_executions = await flow_engine.process_event(
        db=db,
        tenant_id=tenant.id,
        connector_name=body.connector_name,
        event=body.event,
        event_data=body.data,
        execute_action_fn=execute_action_for_flow,
    )

    workflow_executions = await workflow_engine.process_event(
        db=db,
        tenant_id=tenant.id,
        connector_name=body.connector_name,
        event=body.event,
        event_data=body.data,
    )

    await db.commit()

    logger.info(
        "Internal event processed",
        connector=body.connector_name,
        event_name=body.event,
        flows_triggered=len(flow_executions),
        workflows_triggered=len(workflow_executions),
    )

    return {
        "event": body.event,
        "connector": body.connector_name,
        "flows_triggered": len(flow_executions),
        "workflows_triggered": len(workflow_executions),
    }


# --- Flow Executions (audit log) ---


@app.get(
    "/api/v1/flow-executions",
    response_model=list[FlowExecutionResponse],
    tags=["flow-executions"],
)
async def list_flow_executions(
    flow_id: str | None = Query(None),
    status: str | None = Query(None),
    limit: int = Query(50, le=200),
    offset: int = Query(0, ge=0),
    date_from: datetime | None = Query(None, description="ISO 8601 datetime, e.g. 2026-02-20T00:00:00Z"),
    date_to: datetime | None = Query(None, description="ISO 8601 datetime, e.g. 2026-02-22T23:59:59Z"),
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
) -> list[FlowExecutionResponse]:
    query = select(FlowExecution).where(FlowExecution.tenant_id == tenant.id)
    if flow_id:
        query = query.where(FlowExecution.flow_id == flow_id)
    if status:
        query = query.where(FlowExecution.status == status)
    if date_from:
        query = query.where(FlowExecution.started_at >= date_from)
    if date_to:
        query = query.where(FlowExecution.started_at <= date_to)
    query = query.order_by(FlowExecution.started_at.desc()).offset(offset).limit(limit)

    result = await db.execute(query)
    executions = result.scalars().all()
    return [FlowExecutionResponse.model_validate(e) for e in executions]


@app.get(
    "/api/v1/flow-executions/{execution_id}",
    response_model=FlowExecutionDetailResponse,
    tags=["flow-executions"],
)
async def get_flow_execution_detail(
    execution_id: str,
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
) -> FlowExecutionDetailResponse:
    result = await db.execute(
        select(FlowExecution).where(
            FlowExecution.id == execution_id,
            FlowExecution.tenant_id == tenant.id,
        )
    )
    execution = result.scalar_one_or_none()
    if not execution:
        raise HTTPException(status_code=404, detail="Flow execution not found")

    flow_result = await db.execute(
        select(Flow).where(Flow.id == execution.flow_id)
    )
    flow = flow_result.scalar_one_or_none()

    raw = {
        "id": str(execution.id),
        "flow_id": str(execution.flow_id),
        "status": execution.status,
        "source_event_data": execution.source_event_data or {},
        "destination_action_data": execution.destination_action_data or {},
        "result": execution.result,
        "error": execution.error,
        "retry_count": execution.retry_count,
        "duration_ms": execution.duration_ms,
        "started_at": execution.started_at.isoformat() if execution.started_at else None,
        "completed_at": execution.completed_at.isoformat() if execution.completed_at else None,
        "flow_name": flow.name if flow else None,
        "source_connector": flow.source_connector if flow else None,
        "destination_connector": flow.destination_connector if flow else None,
    }

    redacted = redact_execution_detail(raw)
    return FlowExecutionDetailResponse(
        id=execution.id,
        flow_id=execution.flow_id,
        status=execution.status,
        source_event_data=redacted.get("source_event_data", {}),
        destination_action_data=redacted.get("destination_action_data", {}),
        result=redacted.get("result"),
        error=execution.error,
        retry_count=execution.retry_count,
        duration_ms=execution.duration_ms,
        started_at=execution.started_at,
        completed_at=execution.completed_at,
        flow_name=flow.name if flow else None,
        source_connector=flow.source_connector if flow else None,
        destination_connector=flow.destination_connector if flow else None,
        gdpr_meta=redacted.get("_gdpr", {}),
    )


# --- Workflows ---


def _extract_trigger_info(nodes: list[dict]) -> tuple[str | None, str | None]:
    for node in nodes:
        if node.get("type") == "trigger":
            config = node.get("config", {})
            return config.get("connector_name"), config.get("event")
    return None, None


def _extract_trigger_credential(nodes: list[dict]) -> str:
    for node in nodes:
        if node.get("type") == "trigger":
            return node.get("config", {}).get("credential_name", "default")
    return "default"


async def _provision_email_trigger(
    db: AsyncSession, tenant_id: Any, nodes: list[dict]
) -> None:
    """Provision email account on the connector when a workflow uses an email-client trigger."""
    trigger_connector, _ = _extract_trigger_info(nodes)
    if trigger_connector != "email-client":
        return
    cred_name = _extract_trigger_credential(nodes)
    try:
        creds = await vault.retrieve_all(db, tenant_id, "email-client", credential_name=cred_name)
        if creds:
            if "account_name" not in creds:
                creds["account_name"] = cred_name
            base_url = _resolve_service_url("email-client")
            account_name = await _ensure_email_account(base_url, creds)
            await logger.ainfo(
                "workflow_email_trigger_provisioned",
                tenant_id=str(tenant_id),
                credential=cred_name,
                account=account_name,
            )
    except Exception:
        await logger.aexception(
            "workflow_email_trigger_provision_failed",
            tenant_id=str(tenant_id),
            credential=cred_name,
        )


@app.post("/api/v1/workflows", response_model=WorkflowResponse, tags=["workflows"])
async def create_workflow(
    body: WorkflowCreate,
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
) -> WorkflowResponse:
    nodes_raw = [n.model_dump() for n in body.nodes]
    edges_raw = [e.model_dump() for e in body.edges]
    trigger_connector, trigger_event = _extract_trigger_info(nodes_raw)

    workflow = Workflow(
        tenant_id=tenant.id,
        name=body.name,
        description=body.description,
        nodes=nodes_raw,
        edges=edges_raw,
        variables=body.variables,
        trigger_connector=trigger_connector,
        trigger_event=trigger_event,
        on_error=body.on_error,
        max_retries=body.max_retries,
        timeout_seconds=body.timeout_seconds,
    )
    db.add(workflow)
    await db.commit()
    await db.refresh(workflow)

    await _provision_email_trigger(db, tenant.id, nodes_raw)

    return WorkflowResponse.model_validate(workflow)


@app.get("/api/v1/workflows", response_model=list[WorkflowResponse], tags=["workflows"])
async def list_workflows(
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
) -> list[WorkflowResponse]:
    result = await db.execute(
        select(Workflow)
        .where(Workflow.tenant_id == tenant.id)
        .order_by(Workflow.updated_at.desc())
    )
    return [WorkflowResponse.model_validate(w) for w in result.scalars().all()]


@app.get("/api/v1/workflows/{workflow_id}", response_model=WorkflowResponse, tags=["workflows"])
async def get_workflow(
    workflow_id: str,
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
) -> WorkflowResponse:
    result = await db.execute(
        select(Workflow).where(Workflow.id == workflow_id, Workflow.tenant_id == tenant.id)
    )
    workflow = result.scalar_one_or_none()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return WorkflowResponse.model_validate(workflow)


@app.patch("/api/v1/workflows/{workflow_id}", response_model=WorkflowResponse, tags=["workflows"])
async def update_workflow(
    workflow_id: str,
    body: WorkflowUpdate,
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
) -> WorkflowResponse:
    result = await db.execute(
        select(Workflow).where(Workflow.id == workflow_id, Workflow.tenant_id == tenant.id)
    )
    workflow = result.scalar_one_or_none()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    update_data = body.model_dump(exclude_none=True)

    if "nodes" in update_data:
        update_data["nodes"] = [
            n.model_dump() if hasattr(n, "model_dump") else n for n in update_data["nodes"]
        ]
        trigger_connector, trigger_event = _extract_trigger_info(update_data["nodes"])
        update_data["trigger_connector"] = trigger_connector
        update_data["trigger_event"] = trigger_event

    if "edges" in update_data:
        update_data["edges"] = [
            e.model_dump() if hasattr(e, "model_dump") else e for e in update_data["edges"]
        ]

    for key, value in update_data.items():
        setattr(workflow, key, value)

    workflow.version = (workflow.version or 1) + 1
    await db.commit()
    await db.refresh(workflow)

    needs_provision = (
        "nodes" in update_data
        or (update_data.get("is_enabled") is True)
    )
    if needs_provision and workflow.trigger_connector == "email-client":
        await _provision_email_trigger(db, tenant.id, workflow.nodes or [])

    return WorkflowResponse.model_validate(workflow)


@app.delete("/api/v1/workflows/{workflow_id}", tags=["workflows"])
async def delete_workflow(
    workflow_id: str,
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    result = await db.execute(
        select(Workflow).where(Workflow.id == workflow_id, Workflow.tenant_id == tenant.id)
    )
    workflow = result.scalar_one_or_none()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    await db.delete(workflow)
    await db.commit()
    return {"status": "deleted"}


@app.post(
    "/api/v1/workflows/{workflow_id}/test",
    response_model=WorkflowExecutionResponse,
    tags=["workflows"],
)
async def test_workflow(
    workflow_id: str,
    body: WorkflowTestRequest,
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
) -> WorkflowExecutionResponse:
    result = await db.execute(
        select(Workflow).where(Workflow.id == workflow_id, Workflow.tenant_id == tenant.id)
    )
    workflow = result.scalar_one_or_none()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    execution = await workflow_engine.execute_workflow(db, workflow, body.trigger_data)
    await db.commit()
    return WorkflowExecutionResponse.model_validate(execution)


@app.post("/api/v1/workflows/{workflow_id}/toggle", tags=["workflows"])
async def toggle_workflow(
    workflow_id: str,
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    result = await db.execute(
        select(Workflow).where(Workflow.id == workflow_id, Workflow.tenant_id == tenant.id)
    )
    workflow = result.scalar_one_or_none()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    workflow.is_enabled = not workflow.is_enabled
    await db.commit()

    if workflow.is_enabled and workflow.trigger_connector == "email-client":
        await _provision_email_trigger(db, tenant.id, workflow.nodes or [])

    return {"status": "enabled" if workflow.is_enabled else "disabled", "is_enabled": workflow.is_enabled}


@app.get(
    "/api/v1/workflow-executions",
    response_model=list[WorkflowExecutionResponse],
    tags=["workflow-executions"],
)
async def list_workflow_executions(
    workflow_id: str | None = Query(None),
    status: str | None = Query(None),
    limit: int = Query(50, le=200),
    offset: int = Query(0, ge=0),
    date_from: datetime | None = Query(None, description="ISO 8601 datetime, e.g. 2026-02-20T00:00:00Z"),
    date_to: datetime | None = Query(None, description="ISO 8601 datetime, e.g. 2026-02-22T23:59:59Z"),
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
) -> list[WorkflowExecutionResponse]:
    query = select(WorkflowExecution).where(WorkflowExecution.tenant_id == tenant.id)
    if workflow_id:
        query = query.where(WorkflowExecution.workflow_id == workflow_id)
    if status:
        query = query.where(WorkflowExecution.status == status)
    if date_from:
        query = query.where(WorkflowExecution.started_at >= date_from)
    if date_to:
        query = query.where(WorkflowExecution.started_at <= date_to)
    query = query.order_by(WorkflowExecution.started_at.desc()).offset(offset).limit(limit)
    result = await db.execute(query)
    return [WorkflowExecutionResponse.model_validate(e) for e in result.scalars().all()]


@app.get(
    "/api/v1/workflow-executions/{execution_id}",
    response_model=WorkflowExecutionDetailResponse,
    tags=["workflow-executions"],
)
async def get_workflow_execution_detail(
    execution_id: str,
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
) -> WorkflowExecutionDetailResponse:
    result = await db.execute(
        select(WorkflowExecution).where(
            WorkflowExecution.id == execution_id,
            WorkflowExecution.tenant_id == tenant.id,
        )
    )
    execution = result.scalar_one_or_none()
    if not execution:
        raise HTTPException(status_code=404, detail="Workflow execution not found")

    wf_result = await db.execute(
        select(Workflow).where(Workflow.id == execution.workflow_id)
    )
    workflow = wf_result.scalar_one_or_none()

    raw = {
        "id": str(execution.id),
        "workflow_id": str(execution.workflow_id),
        "status": execution.status,
        "trigger_data": execution.trigger_data or {},
        "node_results": execution.node_results or [],
        "context_snapshot": execution.context_snapshot or {},
        "error": execution.error,
        "error_node_id": execution.error_node_id,
        "duration_ms": execution.duration_ms,
        "started_at": execution.started_at.isoformat() if execution.started_at else None,
        "completed_at": execution.completed_at.isoformat() if execution.completed_at else None,
    }

    redacted = redact_execution_detail(raw)
    nodes_snapshot = execution.workflow_nodes_snapshot
    edges_snapshot = execution.workflow_edges_snapshot
    if not nodes_snapshot and workflow:
        nodes_snapshot = workflow.nodes
    if not edges_snapshot and workflow:
        edges_snapshot = workflow.edges

    return WorkflowExecutionDetailResponse(
        id=execution.id,
        workflow_id=execution.workflow_id,
        status=execution.status,
        trigger_data=redacted.get("trigger_data", {}),
        node_results=redacted.get("node_results", []),
        context_snapshot=redacted.get("context_snapshot", {}),
        workflow_nodes_snapshot=nodes_snapshot,
        workflow_edges_snapshot=edges_snapshot,
        error=execution.error,
        error_node_id=execution.error_node_id,
        duration_ms=execution.duration_ms,
        started_at=execution.started_at,
        completed_at=execution.completed_at,
        workflow_name=workflow.name if workflow else None,
        workflow_description=workflow.description if workflow else None,
        trigger_connector=workflow.trigger_connector if workflow else None,
        trigger_event=workflow.trigger_event if workflow else None,
        gdpr_meta=redacted.get("_gdpr", {}),
    )
