"""API Gateway -- main FastAPI application for Open Integration Platform by Pinquark.com."""

import io
import os
import re
import secrets
import time
import uuid
import zipfile
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Any

import httpx
import structlog
from fastapi import Depends, FastAPI, HTTPException, Query, Request, Security
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import flag_modified

from api.auth import api_key_header, generate_api_key, get_current_tenant, hash_api_key
from api.schemas import (
    ApiKeyCreate,
    ApiKeyResponse,
    ConnectorInstanceCreate,
    ConnectorInstanceResponse,
    ConnectorResponse,
    CredentialStore,
    DemoRegisterRequest,
    DemoRegisterResponse,
    DemoValidateKeyRequest,
    DemoValidateKeyResponse,
    EventTrigger,
    FlowCreate,
    FlowExecutionDetailResponse,
    FlowExecutionResponse,
    FlowResponse,
    FlowUpdate,
    HealthResponse,
    TenantCreate,
    TenantResponse,
    WorkflowAiGenerateRequest,
    WorkflowAiGenerateResponse,
    WorkflowCreate,
    WorkflowExecutionDetailResponse,
    WorkflowExecutionResponse,
    WorkflowResponse,
    WorkflowTestRequest,
    WorkflowUpdate,
)
from config import settings
from api.credential_validator import validate_credentials as generic_validate_credentials
from core.action_dispatcher import dispatch_action, _ensure_account_generic, _resolve_service_url
from core.pii_redactor import redact_execution_detail
from core.connector_registry import ConnectorRegistry
from core.credential_vault import CredentialVault
from core.flow_engine import FlowEngine
from core.mapping_resolver import MappingResolver
from core.redis_client import close_redis, get_redis, redis_health
from core.workflow_engine import WorkflowEngine
from db.base import async_session_factory, get_db, set_rls_bypass
from db.models import ApiKey, ConnectorInstance, Credential, Flow, FlowExecution, Tenant, Workflow, WorkflowExecution
from middleware.rate_limiter import RateLimiterMiddleware
from middleware.metrics import PrometheusMiddleware, metrics_endpoint

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

    async with async_session_factory() as db_session:
        tenant_result = await db_session.execute(select(Tenant).limit(1))
        if not tenant_result.scalar_one_or_none():
            default_tenant = Tenant(name="Default", slug="default", is_active=True, plan="free")
            db_session.add(default_tenant)
            await db_session.flush()

            preset_key = os.environ.get("DEFAULT_API_KEY", "")
            if preset_key:
                raw_key = preset_key
                key_hash = hash_api_key(raw_key)
            else:
                raw_key, key_hash = generate_api_key()

            api_key = ApiKey(
                tenant_id=default_tenant.id,
                key_hash=key_hash,
                key_prefix=raw_key[:10],
                name="dashboard",
                is_active=True,
            )
            db_session.add(api_key)
            await db_session.commit()
            await logger.ainfo(
                "default_tenant_created",
                tenant_id=str(default_tenant.id),
                api_key_prefix=raw_key[:10],
                api_key="***auto-generated***" if not preset_key else "***set-from-env***",
            )

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
                await set_rls_bypass(db_session)
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
            registry=registry,
        )

    workflow_engine.set_action_executor(_execute_connector_action)

    async def _resolve_credentials(
        connector_name: str,
        credential_name: str,
        tenant_id: Any,
    ) -> tuple[dict[str, str] | None, str]:
        credentials: dict[str, str] | None = None
        try:
            async with async_session_factory() as db_session:
                await set_rls_bypass(db_session)
                credentials = await vault.retrieve_all(
                    db_session, tenant_id, connector_name, credential_name=credential_name
                )
        except Exception:
            pass

        manifests = registry.get_by_name(connector_name)
        manifest = manifests[0] if manifests else None
        base_url = manifest.base_url if manifest else f"http://connector-{connector_name}:8000"

        if credentials and manifest:
            from core.action_dispatcher import _provision_credentials
            dummy: dict[str, Any] = {}
            await _provision_credentials(base_url, connector_name, dummy, credentials, manifest)

        account_name = credentials.get("account_name", credential_name) if credentials else credential_name
        creds_with_account = dict(credentials) if credentials else {}
        creds_with_account.setdefault("account_name", account_name)

        return creds_with_account, base_url

    workflow_engine.set_credential_resolver(_resolve_credentials)
    await logger.ainfo("workflow_engine_action_executor_ready")

    import asyncio

    async def _provision_trigger_accounts() -> None:
        """Provision accounts on connectors that use account-based credential
        provisioning and have active workflow/flow triggers."""
        await asyncio.sleep(5)

        account_connectors: set[str] = set()
        for manifest in registry.get_all():
            prov = manifest.credential_provisioning
            if prov and prov.get("mode") == "account":
                account_connectors.add(manifest.name)

        if not account_connectors:
            return

        try:
            async with async_session_factory() as db_session:
                await set_rls_bypass(db_session)
                for connector_name in account_connectors:
                    wf_result = await db_session.execute(
                        select(Workflow).where(
                            Workflow.trigger_connector == connector_name,
                            Workflow.is_enabled.is_(True),
                        )
                    )
                    workflows = wf_result.scalars().all()

                    fl_result = await db_session.execute(
                        select(Flow).where(
                            Flow.source_connector == connector_name,
                            Flow.is_enabled.is_(True),
                        )
                    )
                    flows = fl_result.scalars().all()

                    credential_pairs: set[tuple[Any, str]] = set()
                    for wf in workflows:
                        for node in (wf.nodes or []):
                            if (
                                node.get("type") == "trigger"
                                and node.get("config", {}).get("connector_name") == connector_name
                            ):
                                cred_name = node["config"].get("credential_name", "default")
                                credential_pairs.add((wf.tenant_id, cred_name))
                    for fl in flows:
                        credential_pairs.add((fl.tenant_id, "default"))

                    if not credential_pairs:
                        continue

                    manifests = registry.get_by_name(connector_name)
                    manifest = manifests[0] if manifests else None
                    base_url = manifest.base_url if manifest else _resolve_service_url(connector_name, registry)
                    provisioning = manifest.credential_provisioning if manifest else {}

                    for tid, cred_name in credential_pairs:
                        try:
                            creds = await vault.retrieve_all(
                                db_session, tid, connector_name, credential_name=cred_name
                            )
                            if creds:
                                if "account_name" not in creds:
                                    creds["account_name"] = cred_name
                                account_name = await _ensure_account_generic(
                                    base_url, creds, provisioning
                                )
                                await logger.ainfo(
                                    "trigger_account_provisioned",
                                    connector=connector_name,
                                    tenant_id=str(tid),
                                    credential=cred_name,
                                    account=account_name,
                                )
                        except Exception:
                            await logger.aexception(
                                "trigger_account_provision_failed",
                                connector=connector_name,
                                tenant_id=str(tid),
                                credential=cred_name,
                            )
        except Exception:
            await logger.aexception("trigger_provision_scan_failed")

    asyncio.create_task(_provision_trigger_accounts())

    # Kafka Event Bridge — consume events from Kafka and trigger workflows/flows
    kafka_bridge = None
    if settings.kafka_enabled:
        from core.kafka_event_consumer import KafkaEventBridge

        kafka_bridge = KafkaEventBridge(
            bootstrap_servers=settings.kafka_bootstrap_servers,
            group_id=settings.kafka_consumer_group,
            topics=settings.kafka_event_topics,
            security_protocol=settings.kafka_security_protocol,
            session_factory=async_session_factory,
            workflow_engine=workflow_engine,
            flow_engine=flow_engine,
            registry=registry,
            sasl_mechanism=settings.kafka_sasl_mechanism,
            sasl_username=settings.kafka_sasl_username,
            sasl_password=settings.kafka_sasl_password,
            ssl_cafile=settings.kafka_ssl_cafile,
        )
        try:
            await kafka_bridge.start()
            await logger.ainfo(
                "kafka_event_bridge_started",
                topics=settings.kafka_event_topics,
                bootstrap_servers=settings.kafka_bootstrap_servers,
            )
        except Exception:
            await logger.aexception("kafka_event_bridge_start_failed")
            kafka_bridge = None

    yield

    if kafka_bridge:
        await kafka_bridge.stop()
    await close_redis()
    await logger.ainfo("redis_disconnected")


_APP_VERSION = os.environ.get("APP_VERSION", "0.1.0")

app = FastAPI(
    title="Open Integration Platform by Pinquark.com",
    version=_APP_VERSION,
    description="Open-source integration hub — connect any system with any other system.",
    lifespan=lifespan,
)

app.add_middleware(RateLimiterMiddleware)
app.add_middleware(PrometheusMiddleware)

app.get("/metrics", tags=["health"])(metrics_endpoint)

_cors_origins = [o.strip() for o in settings.cors_allowed_origins.split(",") if o.strip()] if settings.cors_allowed_origins else []
if _cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-API-Key", "X-Admin-Secret", "X-Internal-Secret"],
    )


from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from fastapi import Response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response


app.add_middleware(SecurityHeadersMiddleware)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    await logger.aerror("unhandled_exception", path=request.url.path, error=type(exc).__name__)
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An internal error occurred",
            }
        },
    )


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
    return JSONResponse(
        status_code=400,
        content={
            "error": {
                "code": "INVALID_INPUT",
                "message": str(exc),
            }
        },
    )


def _require_admin_secret(request: Request) -> None:
    """Verify admin secret for tenant-management endpoints.

    When no ADMIN_SECRET is configured the endpoints are fully locked
    to prevent unauthenticated tenant/key creation.  The only exception
    is demo_mode, which uses its own registration flow.
    """
    if not settings.admin_secret:
        raise HTTPException(
            status_code=403,
            detail="Tenant management is disabled — set ADMIN_SECRET to enable",
        )
    provided = request.headers.get("X-Admin-Secret", "")
    if not secrets.compare_digest(provided, settings.admin_secret):
        raise HTTPException(status_code=403, detail="Invalid admin secret")


async def _require_admin_or_api_key(
    request: Request,
    api_key: str | None = Security(api_key_header),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Allow access via X-Admin-Secret OR a valid X-API-Key.

    Verification proxy endpoints need to be accessible from both:
    - Admin tooling (using X-Admin-Secret)
    - Dashboard (using X-API-Key from an authenticated tenant)
    """
    admin_ok = False
    if settings.admin_secret:
        provided = request.headers.get("X-Admin-Secret", "")
        if provided and secrets.compare_digest(provided, settings.admin_secret):
            admin_ok = True

    if admin_ok:
        return

    if api_key:
        key_hash = hash_api_key(api_key)
        result = await db.execute(
            select(ApiKey).where(ApiKey.key_hash == key_hash, ApiKey.is_active.is_(True))
        )
        if result.scalar_one_or_none():
            return

    raise HTTPException(status_code=403, detail="Admin secret or valid API key required")


def _require_internal_secret(request: Request) -> None:
    """Verify internal secret for /internal/* endpoints.

    These endpoints are meant to be called only from within the Docker
    network by other connectors/services.  When no INTERNAL_SECRET is
    configured, access is allowed (Docker network trust model) with a
    warning logged on first call.
    """
    if not settings.internal_secret:
        return
    provided = request.headers.get("X-Internal-Secret", "")
    if not secrets.compare_digest(provided, settings.internal_secret):
        raise HTTPException(status_code=403, detail="Invalid internal secret")


# --- Health ---


@app.get("/health", response_model=HealthResponse, tags=["health"])
async def health_check() -> HealthResponse:
    redis_ok = await redis_health()
    db_ok = True
    try:
        async with async_session_factory() as db_session:
            await db_session.execute(select(func.now()))
    except Exception:
        db_ok = False
    all_ok = redis_ok and db_ok
    return HealthResponse(
        status="healthy" if all_ok else "degraded",
        version=_APP_VERSION,
        uptime_seconds=round(time.time() - _start_time, 1),
        checks={
            "database": "ok" if db_ok else "error",
            "redis": "ok" if redis_ok else "error",
            "registry": "ok",
        },
    )


@app.get("/readiness", tags=["health"])
async def readiness_check() -> dict[str, Any]:
    redis_ok = await redis_health()
    db_ok = True
    try:
        async with async_session_factory() as db_session:
            await db_session.execute(select(func.now()))
    except Exception:
        db_ok = False

    all_ok = redis_ok and db_ok
    return {
        "status": "ready" if all_ok else "not_ready",
        "checks": {
            "database": "ok" if db_ok else "error",
            "redis": "ok" if redis_ok else "error",
            "connectors": f"{len(registry.get_all())} discovered",
        },
    }


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
            output_fields=c.output_fields,
            deployment=c.deployment,
            requires_onpremise_agent=c.requires_onpremise_agent,
            onpremise_agent=c.onpremise_agent,
        )
        for c in results
    ]


@app.get("/api/v1/connectors/{name}/openapi", tags=["connectors"])
async def get_connector_openapi(name: str):
    """Proxy to connector's /openapi.json endpoint for Swagger UI embedding."""
    manifests = registry.get_by_name(name)
    if not manifests:
        raise HTTPException(status_code=404, detail=f"Connector '{name}' not found")

    sorted_manifests = sorted(manifests, key=lambda m: m.version, reverse=True)

    async with httpx.AsyncClient(timeout=10.0) as client:
        for manifest in sorted_manifests:
            url = f"{manifest.base_url}/openapi.json"
            try:
                resp = await client.get(url)
                resp.raise_for_status()
                spec = resp.json()
                spec["servers"] = [{"url": f"/connector-proxy/{name}", "description": "Connector API"}]
                return spec
            except (httpx.ConnectError, httpx.HTTPStatusError):
                continue

        raise HTTPException(status_code=503, detail=f"Connector '{name}' is not reachable")


@app.get("/api/v1/connectors/{name}/onpremise-agent", tags=["connectors"])
async def download_onpremise_agent(
    name: str,
    tenant: Tenant = Depends(get_current_tenant),
) -> StreamingResponse:
    """Download the on-premise agent package as a ZIP file."""
    connectors = registry.get_by_name(name)
    if not connectors:
        raise HTTPException(status_code=404, detail=f"Connector '{name}' not found")

    manifest = connectors[0]
    if not manifest.requires_onpremise_agent:
        raise HTTPException(status_code=404, detail=f"Connector '{name}' does not have an on-premise agent")

    agent_info = manifest.onpremise_agent
    source_dir = agent_info.get("source_directory", "")
    if not source_dir:
        raise HTTPException(status_code=404, detail="On-premise agent source directory not configured")

    agent_path = Path(source_dir)
    if not agent_path.is_absolute():
        agent_path = Path(settings.connector_discovery_path).parent / source_dir

    agent_path = agent_path.resolve()
    safe_base = Path(settings.connector_discovery_path).parent.resolve()
    try:
        agent_path.relative_to(safe_base)
    except ValueError:
        raise HTTPException(status_code=403, detail="Access denied")

    if not agent_path.exists() or not agent_path.is_dir():
        raise HTTPException(status_code=404, detail="On-premise agent files not found on server")

    _skip_exact = {".pyc", "__pycache__", ".git", ".env"}

    def _should_skip(path: Path) -> bool:
        parts = path.parts
        for part in parts:
            if part in _skip_exact:
                return True
            if part.endswith(".egg-info"):
                return True
        return False

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for file_path in sorted(agent_path.rglob("*")):
            if not file_path.is_file():
                continue
            if _should_skip(file_path.relative_to(agent_path)):
                continue
            arcname = file_path.relative_to(agent_path)
            zf.write(file_path, arcname)
    buf.seek(0)

    filename = f"{name}-onpremise-agent-v{manifest.version}.zip"
    return StreamingResponse(
        buf,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


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
        output_fields=connector.output_fields,
        deployment=connector.deployment,
        requires_onpremise_agent=connector.requires_onpremise_agent,
        onpremise_agent=connector.onpremise_agent,
    )


# --- Tenant management ---


@app.get("/api/v1/tenants", tags=["tenants"])
async def list_tenants(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    _require_admin_secret(request)
    result = await db.execute(select(Tenant).order_by(Tenant.created_at))
    tenants = result.scalars().all()
    out: list[dict[str, Any]] = []
    for t in tenants:
        keys_result = await db.execute(
            select(ApiKey).where(ApiKey.tenant_id == t.id)
        )
        keys = keys_result.scalars().all()
        out.append({
            "id": str(t.id),
            "name": t.name,
            "slug": t.slug,
            "plan": t.plan,
            "is_active": t.is_active,
            "created_at": t.created_at.isoformat() if t.created_at else None,
            "api_keys": [
                {
                    "id": str(k.id),
                    "key_prefix": k.key_prefix,
                    "name": k.name,
                    "is_active": k.is_active,
                }
                for k in keys
            ],
        })
    return out


@app.post("/api/v1/tenants", response_model=TenantResponse, tags=["tenants"])
async def create_tenant(
    request: Request,
    body: TenantCreate,
    db: AsyncSession = Depends(get_db),
) -> TenantResponse:
    _require_admin_secret(request)
    existing = await db.execute(select(Tenant).where(Tenant.slug == body.slug))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail=f"Tenant with slug '{body.slug}' already exists")
    tenant = Tenant(name=body.name, slug=body.slug)
    db.add(tenant)
    await db.commit()
    await db.refresh(tenant)
    return TenantResponse.model_validate(tenant)


@app.post("/api/v1/tenants/{tenant_id}/api-keys", response_model=ApiKeyResponse, tags=["tenants"])
async def create_api_key(
    request: Request,
    tenant_id: str,
    body: ApiKeyCreate,
    db: AsyncSession = Depends(get_db),
) -> ApiKeyResponse:
    _require_admin_secret(request)
    try:
        tid = uuid.UUID(tenant_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid tenant_id format")
    tenant = await db.execute(select(Tenant).where(Tenant.id == tid))
    if not tenant.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Tenant not found")
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

    account_provisioned = False
    manifests = registry.get_by_name(body.connector_name)
    if manifests:
        manifest = manifests[0]
        provisioning = manifest.credential_provisioning
        if provisioning and provisioning.get("mode") == "account":
            try:
                creds = await vault.retrieve_all(
                    db, tenant.id, body.connector_name,
                    credential_name=body.credential_name,
                )
                if creds:
                    if "account_name" not in creds:
                        creds["account_name"] = body.credential_name
                    base_url = manifest.base_url
                    await _ensure_account_generic(base_url, creds, provisioning, force_update=True)
                    account_provisioned = True
                    await logger.ainfo(
                        "credential_account_reprovisioned",
                        connector=body.connector_name,
                        credential=body.credential_name,
                    )
            except Exception:
                await logger.aexception(
                    "credential_account_reprovision_failed",
                    connector=body.connector_name,
                    credential=body.credential_name,
                )

    return {
        "status": "stored",
        "connector": body.connector_name,
        "credential_name": body.credential_name,
        "keys": list(body.credentials.keys()),
        "workflows_updated": workflows_updated,
        "account_provisioned": account_provisioned,
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

    return await generic_validate_credentials(connector_name, merged, registry)


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

    update_data = body.model_dump(exclude_unset=True)
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
            registry=registry,
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
            {
                "workflow_id": str(e.workflow_id),
                "execution_id": str(e.id),
                "status": e.status,
                "duration_ms": e.duration_ms,
                "node_results": e.node_results or [],
                "context_snapshot": e.context_snapshot or {},
                "error": e.error,
            }
            for e in workflow_executions
        ],
    }


@app.post("/internal/events", tags=["internal"], dependencies=[Depends(_require_internal_secret)])
async def internal_trigger_event(
    body: EventTrigger,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Internal event endpoint for connector-to-platform communication.

    No API key required — trusted within the Docker network.
    Processes the event for ALL active tenants so every tenant's
    matching flows/workflows are triggered regardless of DB row order.
    """
    await set_rls_bypass(db)
    result = await db.execute(
        select(Tenant).where(Tenant.is_active.is_(True))
    )
    tenants = list(result.scalars().all())
    if not tenants:
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
            registry=registry,
        )

    all_flow_executions: list[FlowExecution] = []
    all_workflow_executions: list[WorkflowExecution] = []

    for tenant in tenants:
        flow_executions = await flow_engine.process_event(
            db=db,
            tenant_id=tenant.id,
            connector_name=body.connector_name,
            event=body.event,
            event_data=body.data,
            execute_action_fn=execute_action_for_flow,
        )
        all_flow_executions.extend(flow_executions)

        workflow_executions = await workflow_engine.process_event(
            db=db,
            tenant_id=tenant.id,
            connector_name=body.connector_name,
            event=body.event,
            event_data=body.data,
        )
        all_workflow_executions.extend(workflow_executions)

    await db.commit()

    logger.info(
        "Internal event processed",
        connector=body.connector_name,
        event_name=body.event,
        tenants_checked=len(tenants),
        flows_triggered=len(all_flow_executions),
        workflows_triggered=len(all_workflow_executions),
    )

    return {
        "event": body.event,
        "connector": body.connector_name,
        "flows_triggered": len(all_flow_executions),
        "workflows_triggered": len(all_workflow_executions),
    }


# --- Internal: connector credential distribution ---


@app.get("/internal/connector-credentials/{connector_name}", tags=["internal"], dependencies=[Depends(_require_internal_secret)])
async def internal_get_connector_credentials(
    connector_name: str,
    db: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    """Return all stored credentials for a connector across all tenants.

    Used internally by connectors (within Docker network) to auto-register
    credentials for event polling.
    """
    await set_rls_bypass(db)
    result = await db.execute(
        select(Tenant).where(Tenant.is_active.is_(True))
    )
    tenants = list(result.scalars().all())

    accounts: list[dict[str, Any]] = []
    for tenant in tenants:
        try:
            cred_names = await vault.list_credential_names(
                db, tenant.id, connector_name
            )
            for cred_name in cred_names:
                try:
                    creds = await vault.retrieve_all(
                        db, tenant.id, connector_name,
                        credential_name=cred_name,
                    )
                    if creds:
                        accounts.append({
                            "tenant_id": str(tenant.id),
                            "credential_name": cred_name,
                            "credentials": creds,
                        })
                except Exception:
                    pass
        except Exception:
            pass

    return accounts


# --- Internal: connector poller diagnostics ---


@app.get("/internal/connector/{connector_name}/poller/status", tags=["internal"], dependencies=[Depends(_require_internal_secret)])
async def internal_connector_poller_status(connector_name: str) -> Any:
    """Proxy GET to connector debug/poller endpoint."""
    base = _resolve_service_url(connector_name, registry)
    async with httpx.AsyncClient(timeout=10.0) as client:
        for path in ("/debug/poller", "/poller/status"):
            try:
                resp = await client.get(f"{base}{path}")
                if resp.status_code < 400:
                    return resp.json()
            except Exception:
                continue
        raise HTTPException(status_code=502, detail="Cannot reach connector poller status")


@app.post("/internal/connector/{connector_name}/poller/reset", tags=["internal"], dependencies=[Depends(_require_internal_secret)])
async def internal_connector_poller_reset(connector_name: str) -> Any:
    """Proxy POST /poller/reset to a connector."""
    base = _resolve_service_url(connector_name, registry)
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.post(f"{base}/poller/reset")
            return resp.json()
        except Exception as exc:
            raise HTTPException(status_code=502, detail=f"Cannot reach connector poller: {exc}")


@app.post("/internal/connector/{connector_name}/poller/poll-now", tags=["internal"], dependencies=[Depends(_require_internal_secret)])
async def internal_connector_poller_poll_now(connector_name: str) -> Any:
    """Proxy POST to connector debug/poll-now endpoint."""
    base = _resolve_service_url(connector_name, registry)
    async with httpx.AsyncClient(timeout=30.0) as client:
        for path in ("/debug/poll-now", "/poller/poll-now"):
            try:
                resp = await client.post(f"{base}{path}")
                if resp.status_code < 400:
                    return resp.json()
            except Exception:
                continue
        raise HTTPException(status_code=502, detail="Cannot reach connector poll-now")


@app.get("/internal/connector/{connector_name}/poller/diagnose", tags=["internal"], dependencies=[Depends(_require_internal_secret)])
async def internal_connector_poller_diagnose(connector_name: str) -> Any:
    """Proxy GET /poller/diagnose to a connector for WMS API testing."""
    base = _resolve_service_url(connector_name, registry)
    async with httpx.AsyncClient(timeout=30.0) as client:
        for path in ("/poller/diagnose", "/debug/diagnose"):
            try:
                resp = await client.get(f"{base}{path}")
                if resp.status_code < 400:
                    return resp.json()
            except Exception:
                continue
        raise HTTPException(status_code=502, detail="Cannot reach connector diagnose")


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


# --- AI Workflow Generation ---

_WORKFLOW_AI_SYSTEM_PROMPT = """\
You are an integration workflow designer for the Open Integration Platform by Pinquark.com.
Your task is to create workflow definitions based on user descriptions.

A workflow consists of NODES (processing steps) and EDGES (connections between them).

## Available Node Types

- **trigger**: Starting point — listens for a connector event.
  Config: { connector_name, event, credential_name?, filter? }
- **action**: Execute an action on a connector.
  Config: { connector_name, action, credential_name?, field_mapping: [{from, to}], on_error: "stop"|"continue" }
- **condition**: If/else branching. Outputs: "true" / "false".
  Config: { conditions: [{field, operator, value}], logic: "and"|"or" }
  Operators: eq, neq, gt, lt, gte, lte, contains, not_contains, starts_with, ends_with, exists, not_exists, in, not_in, regex, is_empty, is_not_empty
- **switch**: Multi-branch routing based on field value. Outputs: one handle per case + default.
  Config: { field, cases: [{value, handle}], default_handle: "default" }
- **transform**: Map and transform data fields.
  Config: { mappings: [{from, to, transform?}], expressions: {} }
- **filter**: Pass data only if conditions met.
  Config: { conditions: [{field, operator, value}], logic: "and"|"or" }
- **think**: AI Agent — analyze data with a prompt.
  Config: { connector_name: "ai-agent", action: "agent.analyze", prompt, output_schema_json?, temperature?, redact_pii? }
- **delay**: Wait for specified duration.
  Config: { seconds: number }
- **loop**: Iterate over an array.
  Config: { array_field, item_variable: "item", index_variable: "index", max_iterations: 100 }
- **merge**: Merge multiple branches.
  Config: { strategy: "wait_all" }
- **parallel**: Execute branches in parallel. Outputs: "branch" / "done".
  Config: {}
- **aggregate**: Aggregate parallel results.
  Config: { strategy: "cheapest"|"most_expensive"|"concat", field? }
- **http_request**: Make an arbitrary HTTP call.
  Config: { url, method: "GET"|"POST"|"PUT"|"DELETE", headers: {}, body: {}, timeout_seconds: 30 }
- **set_variable**: Set a variable in context.
  Config: { variable_name, value }
- **response**: End workflow and return response.
  Config: { body: {} }

## Edge Structure
{ id: "edge_<unique>", source: "<node_id>", target: "<node_id>", sourceHandle: "default", label: "" }
For condition nodes, sourceHandle is "true" or "false".
For switch nodes, sourceHandle matches the case handle.

## Node Position Layout
Place nodes top-to-bottom. Start trigger at (0, 0), next nodes at (0, 150), then (0, 300), etc.
For branches (condition/switch), offset horizontally: left branch at (-200, y), right at (200, y).

## Response Format
ALWAYS respond with valid JSON wrapped in ```json fences:
```json
{
  "message": "Human-readable explanation of what the workflow does",
  "name": "Workflow name",
  "description": "Brief workflow description",
  "nodes": [ ... ],
  "edges": [ ... ]
}
```

If the user asks a question or clarification (not a workflow request), respond with just a message:
```json
{
  "message": "Your helpful response here"
}
```

## Rules
- Every workflow MUST start with exactly one trigger node.
- Node IDs: use "node_1", "node_2", etc.
- Edge IDs: use "edge_1", "edge_2", etc.
- Use the connectors provided in the context — match connector_name and event/action from their capabilities.
- If the user's request is vague, ask clarifying questions.
- Field references use dot notation: "order.buyer.name", "data.status", etc.
- For field_mapping in action nodes, map from trigger/previous node output fields to the action's expected fields.
"""


async def _call_gemini(api_key: str, messages: list[dict], system_prompt: str) -> str:
    contents = []
    for msg in messages:
        role = "user" if msg["role"] == "user" else "model"
        contents.append({"role": role, "parts": [{"text": msg["content"]}]})

    body = {
        "system_instruction": {"parts": [{"text": system_prompt}]},
        "contents": contents,
        "generationConfig": {"temperature": 0.3, "maxOutputTokens": 8192},
    }

    async with httpx.AsyncClient(timeout=httpx.Timeout(connect=10, read=120, write=10, pool=10)) as client:
        resp = await client.post(
            "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent",
            params={"key": api_key},
            json=body,
        )
        resp.raise_for_status()
        data = resp.json()
        candidates = data.get("candidates", [])
        if candidates:
            parts = candidates[0].get("content", {}).get("parts", [])
            if parts:
                return parts[0].get("text", "")
    return '{"message": "No response from Gemini"}'


async def _call_opus(api_key: str, messages: list[dict], system_prompt: str) -> str:
    api_messages = []
    for msg in messages:
        api_messages.append({"role": msg["role"], "content": msg["content"]})

    body = {
        "model": "claude-opus-4-20250514",
        "max_tokens": 8192,
        "system": system_prompt,
        "messages": api_messages,
    }

    async with httpx.AsyncClient(timeout=httpx.Timeout(connect=10, read=120, write=10, pool=10)) as client:
        resp = await client.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json=body,
        )
        resp.raise_for_status()
        data = resp.json()
        content_blocks = data.get("content", [])
        for block in content_blocks:
            if block.get("type") == "text":
                return block.get("text", "")
    return '{"message": "No response from Claude"}'


def _parse_ai_response(raw_text: str) -> dict:
    import json
    import re

    json_match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", raw_text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(1).strip())
        except json.JSONDecodeError:
            pass

    try:
        return json.loads(raw_text.strip())
    except json.JSONDecodeError:
        return {"message": raw_text.strip()}


@app.post(
    "/api/v1/workflows/ai-generate",
    response_model=WorkflowAiGenerateResponse,
    tags=["workflows"],
)
async def ai_generate_workflow(
    body: WorkflowAiGenerateRequest,
    tenant: Tenant = Depends(get_current_tenant),
) -> WorkflowAiGenerateResponse:
    connector_context = ""
    if body.connectors:
        lines = []
        for c in body.connectors:
            lines.append(
                f"- **{c.get('display_name', c.get('name', ''))}** ({c.get('name', '')}): "
                f"category={c.get('category', '')}, "
                f"events={c.get('events', [])}, "
                f"actions={c.get('actions', [])}"
            )
        connector_context = "\n\n## Available Connectors\n" + "\n".join(lines)

    current_state = ""
    if body.current_nodes:
        import json
        current_state = (
            "\n\n## Current Workflow State\n"
            f"Nodes: {json.dumps(body.current_nodes, indent=2)}\n"
            f"Edges: {json.dumps(body.current_edges, indent=2)}"
        )

    system_prompt = _WORKFLOW_AI_SYSTEM_PROMPT + connector_context + current_state

    messages = [{"role": m.role, "content": m.content} for m in body.conversation]
    messages.append({"role": "user", "content": body.prompt})

    try:
        if body.model == "opus":
            raw_response = await _call_opus(body.api_key, messages, system_prompt)
        else:
            raw_response = await _call_gemini(body.api_key, messages, system_prompt)
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"AI API error: HTTP {exc.response.status_code} — {exc.response.text[:200]}",
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"AI API error: {exc}")

    parsed = _parse_ai_response(raw_response)
    return WorkflowAiGenerateResponse(
        message=parsed.get("message", ""),
        nodes=parsed.get("nodes"),
        edges=parsed.get("edges"),
        name=parsed.get("name"),
        description=parsed.get("description"),
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


async def _provision_trigger_account(
    db: AsyncSession, tenant_id: Any, nodes: list[dict]
) -> None:
    """Provision account on the connector when a workflow uses a trigger that
    requires account-based credential provisioning."""
    trigger_connector, _ = _extract_trigger_info(nodes)
    if not trigger_connector:
        return

    manifests = registry.get_by_name(trigger_connector)
    if not manifests:
        return
    manifest = manifests[0]
    provisioning = manifest.credential_provisioning
    if not provisioning or provisioning.get("mode") != "account":
        return

    cred_name = _extract_trigger_credential(nodes)
    try:
        creds = await vault.retrieve_all(db, tenant_id, trigger_connector, credential_name=cred_name)
        if creds:
            if "account_name" not in creds:
                creds["account_name"] = cred_name
            base_url = manifest.base_url
            account_name = await _ensure_account_generic(base_url, creds, provisioning)
            await logger.ainfo(
                "workflow_trigger_account_provisioned",
                connector=trigger_connector,
                tenant_id=str(tenant_id),
                credential=cred_name,
                account=account_name,
            )
    except Exception:
        await logger.aexception(
            "workflow_trigger_account_provision_failed",
            connector=trigger_connector,
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
        sync_config=body.sync_config,
        trigger_connector=trigger_connector,
        trigger_event=trigger_event,
        on_error=body.on_error,
        max_retries=body.max_retries,
        timeout_seconds=body.timeout_seconds,
    )
    db.add(workflow)
    await db.commit()
    await db.refresh(workflow)

    await _provision_trigger_account(db, tenant.id, nodes_raw)

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

    update_data = body.model_dump(exclude_unset=True)

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
    if needs_provision:
        await _provision_trigger_account(db, tenant.id, workflow.nodes or [])

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


@app.post(
    "/api/v1/workflows/{workflow_id}/execute",
    response_model=WorkflowExecutionResponse,
    tags=["workflows"],
)
async def execute_workflow(
    workflow_id: str,
    body: WorkflowTestRequest,
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
) -> WorkflowExecutionResponse:
    """Execute a workflow synchronously and return full results.

    Use this endpoint when you need the workflow output in the same
    HTTP response (e.g. fetching a shipping label from a courier).
    The response includes ``node_results`` with each node's output
    and ``context_snapshot`` with the final merged data.
    """
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

    if workflow.is_enabled:
        await _provision_trigger_account(db, tenant.id, workflow.nodes or [])

    return {"status": "enabled" if workflow.is_enabled else "disabled", "is_enabled": workflow.is_enabled}


# --- Sync Ledger ---


@app.get("/api/v1/workflows/{workflow_id}/sync-stats", tags=["sync"])
async def get_sync_stats(
    workflow_id: str,
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Get sync ledger statistics for a workflow."""
    result = await db.execute(
        select(Workflow).where(Workflow.id == workflow_id, Workflow.tenant_id == tenant.id)
    )
    workflow = result.scalar_one_or_none()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    from core.sync_state import SyncStateManager
    mgr = SyncStateManager()
    stats = await mgr.get_stats(db, workflow.id)
    return {
        "workflow_id": str(workflow.id),
        "workflow_name": workflow.name,
        "sync_config": workflow.sync_config,
        "stats": stats,
    }


@app.get("/api/v1/workflows/{workflow_id}/sync-failed", tags=["sync"])
async def get_sync_failed(
    workflow_id: str,
    limit: int = Query(50, le=200),
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    """List failed sync entries for a workflow."""
    result = await db.execute(
        select(Workflow).where(Workflow.id == workflow_id, Workflow.tenant_id == tenant.id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Workflow not found")

    from core.sync_state import SyncStateManager
    mgr = SyncStateManager()
    return await mgr.get_failed_entries(db, uuid.UUID(workflow_id), limit=limit)


@app.post("/api/v1/workflows/{workflow_id}/sync-retry", tags=["sync"])
async def retry_failed_syncs(
    workflow_id: str,
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Reset all failed sync entries to pending for retry."""
    result = await db.execute(
        select(Workflow).where(Workflow.id == workflow_id, Workflow.tenant_id == tenant.id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Workflow not found")

    from core.sync_state import SyncStateManager
    mgr = SyncStateManager()
    reset_count = await mgr.reset_failed(db, uuid.UUID(workflow_id))
    await db.commit()
    return {"reset_count": reset_count}


@app.post("/api/v1/workflows/{workflow_id}/sync-clear", tags=["sync"])
async def clear_sync_ledger(
    workflow_id: str,
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Delete all sync ledger entries for a workflow (force full re-sync)."""
    result = await db.execute(
        select(Workflow).where(Workflow.id == workflow_id, Workflow.tenant_id == tenant.id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Workflow not found")

    from core.sync_state import SyncStateManager
    mgr = SyncStateManager()
    deleted = await mgr.clear_ledger(db, uuid.UUID(workflow_id))
    await db.commit()
    return {"deleted_count": deleted}


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
        workflow_name=workflow.name if workflow else (execution.workflow_name or "(usunięty)"),
        workflow_description=workflow.description if workflow else None,
        trigger_connector=workflow.trigger_connector if workflow else None,
        trigger_event=workflow.trigger_event if workflow else None,
        gdpr_meta=redacted.get("_gdpr", {}),
    )


# --- Verification Agent Proxy ---


_VERIFICATION_AGENT_URL = settings.verification_agent_url


async def _proxy_verification(method: str, path: str, body: Any = None, params: dict | None = None) -> Any:
    """Forward requests to the verification-agent microservice."""
    url = f"{_VERIFICATION_AGENT_URL}{path}"
    async with httpx.AsyncClient(timeout=httpx.Timeout(connect=10, read=120, write=10, pool=10)) as client:
        try:
            resp = await client.request(method, url, json=body, params=params)
            resp.raise_for_status()
            return resp.json()
        except httpx.ConnectError:
            raise HTTPException(status_code=503, detail="Verification agent is not reachable")
        except httpx.HTTPStatusError as exc:
            raise HTTPException(status_code=exc.response.status_code, detail=exc.response.text[:500])


@app.post("/api/verification/run", tags=["verification"], dependencies=[Depends(_require_admin_or_api_key)])
async def verification_run_all() -> Any:
    return await _proxy_verification("POST", "/run")


@app.post("/api/verification/run/{connector_name}", tags=["verification"], dependencies=[Depends(_require_admin_or_api_key)])
async def verification_run_single(connector_name: str, version: str | None = Query(None)) -> Any:
    params = {"version": version} if version else None
    return await _proxy_verification("POST", f"/run/{connector_name}", params=params)


@app.get("/api/verification/scheduler", tags=["verification"], dependencies=[Depends(_require_admin_or_api_key)])
async def verification_scheduler_status() -> Any:
    return await _proxy_verification("GET", "/scheduler/status")


@app.put("/api/verification/scheduler", tags=["verification"], dependencies=[Depends(_require_admin_or_api_key)])
async def verification_scheduler_update(body: dict[str, Any]) -> Any:
    return await _proxy_verification("PUT", "/scheduler", body=body)


@app.get("/api/verification/runs", tags=["verification"], dependencies=[Depends(_require_admin_or_api_key)])
async def verification_list_runs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> Any:
    return await _proxy_verification("GET", "/runs", params={"page": str(page), "page_size": str(page_size)})


@app.get("/api/verification/runs/{run_id}", tags=["verification"], dependencies=[Depends(_require_admin_or_api_key)])
async def verification_get_run(run_id: str) -> Any:
    return await _proxy_verification("GET", f"/runs/{run_id}")


@app.get("/api/verification/errors", tags=["verification"], dependencies=[Depends(_require_admin_or_api_key)])
async def verification_list_errors(
    connector_name: str | None = Query(None),
    date_from: str | None = Query(None),
    date_to: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
) -> Any:
    params: dict[str, str] = {"page": str(page), "page_size": str(page_size)}
    if connector_name:
        params["connector_name"] = connector_name
    if date_from:
        params["date_from"] = date_from
    if date_to:
        params["date_to"] = date_to
    return await _proxy_verification("GET", "/errors", params=params)


@app.get("/api/verification/reports/latest", tags=["verification"], dependencies=[Depends(_require_admin_or_api_key)])
async def verification_latest_reports() -> Any:
    return await _proxy_verification("GET", "/reports/latest")


# ── Demo Gate ──────────────────────────────────────────────────────────

_DEMO_RATE_LIMIT = 10
_DEMO_RATE_WINDOW = 3600  # 1 hour


def _slugify(text: str) -> str:
    slug = re.sub(r"[^\w\s-]", "", text.lower().strip())
    slug = re.sub(r"[\s_]+", "-", slug)
    slug = re.sub(r"-+", "-", slug).strip("-")
    return slug or "workspace"


async def _demo_rate_check(client_ip: str) -> None:
    """Rate limit demo registrations using the Redis-based sliding window."""
    try:
        redis = await get_redis()
        now = time.time()
        key = f"demo_register:{client_ip}"
        pipe = redis.pipeline()
        pipe.zremrangebyscore(key, 0, now - _DEMO_RATE_WINDOW)
        pipe.zadd(key, {str(now): now})
        pipe.zcard(key)
        pipe.expire(key, _DEMO_RATE_WINDOW)
        results = await pipe.execute()
        if results[2] > _DEMO_RATE_LIMIT:
            raise HTTPException(status_code=429, detail="Too many demo registrations. Try again later.")
    except HTTPException:
        raise
    except Exception:
        pass


@app.post("/api/v1/demo/register", tags=["demo"], response_model=DemoRegisterResponse)
async def demo_register(
    body: DemoRegisterRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> DemoRegisterResponse:
    if not settings.demo_mode:
        raise HTTPException(status_code=404, detail="Not found")

    client_ip = request.client.host if request.client else "unknown"
    await _demo_rate_check(client_ip)

    suffix = secrets.token_hex(3)
    slug = f"{_slugify(body.workspace_name)}-{suffix}"

    tenant = Tenant(name=body.workspace_name, slug=slug, is_active=True, plan="demo")
    db.add(tenant)
    await db.flush()

    raw_key, key_hash = generate_api_key(prefix="pk_demo")
    api_key = ApiKey(
        tenant_id=tenant.id,
        key_hash=key_hash,
        key_prefix=raw_key[:10],
        name="demo-dashboard",
        is_active=True,
    )
    db.add(api_key)
    await db.commit()

    await logger.ainfo(
        "demo_tenant_created",
        tenant_id=str(tenant.id),
        tenant_slug=slug,
        api_key_prefix=raw_key[:10],
    )

    return DemoRegisterResponse(api_key=raw_key, tenant_name=body.workspace_name, tenant_slug=slug)


@app.post("/api/v1/demo/validate-key", tags=["demo"], response_model=DemoValidateKeyResponse)
async def demo_validate_key(
    body: DemoValidateKeyRequest,
    db: AsyncSession = Depends(get_db),
) -> DemoValidateKeyResponse:
    if not settings.demo_mode:
        raise HTTPException(status_code=404, detail="Not found")

    key_hash = hash_api_key(body.api_key)
    result = await db.execute(
        select(ApiKey).where(ApiKey.key_hash == key_hash, ApiKey.is_active.is_(True))
    )
    api_key_record = result.scalar_one_or_none()
    if not api_key_record:
        return DemoValidateKeyResponse(valid=False)

    tenant_result = await db.execute(
        select(Tenant).where(Tenant.id == api_key_record.tenant_id, Tenant.is_active.is_(True))
    )
    tenant = tenant_result.scalar_one_or_none()
    if not tenant:
        return DemoValidateKeyResponse(valid=False)

    return DemoValidateKeyResponse(valid=True, tenant_name=tenant.name)
