"""ConnectorApp — the main framework class for building connectors."""

from __future__ import annotations

import asyncio
import hashlib
import hmac
import inspect
import time
import uuid
from datetime import datetime, timezone
from typing import Any

import structlog
import uvicorn
from fastapi import FastAPI, Request, Response
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from pinquark_connector_sdk.accounts import AccountStore, register_account_routes
from pinquark_connector_sdk.auth import OAuth2Manager
from pinquark_connector_sdk.decorators import ActionMeta, ConnectorMeta, TriggerMeta, WebhookMeta
from pinquark_connector_sdk.health import _HealthState, register_health_routes
from pinquark_connector_sdk.http import ConnectorHttpClient
from pinquark_connector_sdk.metrics import register_metrics

logger = structlog.get_logger(__name__)


class _TokenBucket:
    """Simple in-process token bucket rate limiter."""

    def __init__(self, rate: float, burst: int) -> None:
        self._rate = rate
        self._burst = burst
        self._tokens = float(burst)
        self._last_refill = time.monotonic()

    def allow(self) -> bool:
        now = time.monotonic()
        elapsed = now - self._last_refill
        self._tokens = min(self._burst, self._tokens + elapsed * self._rate)
        self._last_refill = now
        if self._tokens >= 1.0:
            self._tokens -= 1.0
            return True
        return False


def _parse_rate_spec(spec: str) -> tuple[float, int]:
    """Parse rate specs like '100/minute', '10/second', '40/s', '500/h'."""
    parts = spec.strip().split("/")
    if len(parts) != 2:
        return 10.0, 10
    count = int(parts[0].strip())
    unit = parts[1].strip().lower()
    divisors = {
        "s": 1, "sec": 1, "second": 1, "seconds": 1,
        "m": 60, "min": 60, "minute": 60, "minutes": 60,
        "h": 3600, "hr": 3600, "hour": 3600, "hours": 3600,
    }
    divisor = divisors.get(unit, 60)
    return count / divisor, count


class _ConnectorConfig:
    required_credentials: list[str] = []
    rate_limits: dict[str, str] = {}
    oauth2: dict[str, Any] | None = None
    port: int = 8000


class ConnectorApp:
    """Base class for building connectors.

    Subclass this, set class attributes, and decorate methods with
    ``@action``, ``@trigger``, or ``@webhook``.

    Example::

        from pinquark_connector_sdk import ConnectorApp, action, webhook

        class MyConnector(ConnectorApp):
            name = "my-connector"
            category = "courier"
            version = "1.0.0"
            display_name = "My Connector"
            description = "A sample connector"

            @action("shipment.create")
            async def create_shipment(self, payload: dict) -> dict:
                resp = await self.http.post("https://api.example.com/shipments", json=payload)
                return resp.json()

        if __name__ == "__main__":
            MyConnector().run()
    """

    name: str = ""
    category: str = ""
    version: str = "1.0.0"
    display_name: str = ""
    description: str = ""

    Config = _ConnectorConfig

    def __init__(self) -> None:
        self._config = self._resolve_config()
        self._actions: dict[str, tuple[ActionMeta, Any]] = {}
        self._triggers: dict[str, tuple[TriggerMeta, Any]] = {}
        self._webhooks: dict[str, tuple[WebhookMeta, Any]] = {}
        self._http_client: ConnectorHttpClient | None = None
        self._trigger_tasks: list[asyncio.Task[None]] = []
        self.oauth2: OAuth2Manager | None = None

        self._discover_decorated_methods()

        self._fastapi = FastAPI(
            title=self.display_name or self.name,
            version=self.version,
            description=self.description,
        )
        self._health_state: _HealthState | None = None
        self._account_store: AccountStore | None = None
        self._setup_app()

    def _resolve_config(self) -> _ConnectorConfig:
        for attr_name in dir(self):
            attr = getattr(self, attr_name, None)
            if isinstance(attr, type) and attr_name == "Config" and attr is not _ConnectorConfig:
                cfg = _ConnectorConfig()
                for field in ("required_credentials", "rate_limits", "oauth2", "port"):
                    if hasattr(attr, field):
                        setattr(cfg, field, getattr(attr, field))
                return cfg
        return _ConnectorConfig()

    def _discover_decorated_methods(self) -> None:
        for attr_name in dir(self):
            if attr_name.startswith("_"):
                continue
            method = getattr(self, attr_name, None)
            if not callable(method):
                continue

            meta: ConnectorMeta | None = getattr(method, "_connector_meta", None)
            if meta is None:
                continue

            if isinstance(meta, ActionMeta):
                self._actions[meta.name] = (meta, method)
            elif isinstance(meta, TriggerMeta):
                self._triggers[meta.name] = (meta, method)
            elif isinstance(meta, WebhookMeta):
                self._webhooks[meta.name] = (meta, method)

    def _setup_app(self) -> None:
        self._health_state = register_health_routes(self._fastapi, self)
        register_metrics(self._fastapi, self.name)
        self._account_store = register_account_routes(self._fastapi, self)
        self._register_oauth2_support()
        self._register_trace_context()
        self._register_action_routes()
        self._register_schema_routes()
        self._register_webhook_routes()
        self._register_lifecycle_events()
        self._register_rate_limiting()

    def _register_trace_context(self) -> None:
        @self._fastapi.middleware("http")
        async def trace_middleware(request: Request, call_next: Any) -> Response:
            trace_id = request.headers.get("x-trace-id") or str(uuid.uuid4())
            request.state.trace_id = trace_id
            start = time.monotonic()
            try:
                response = await call_next(request)
            except Exception:
                logger.exception(
                    "request_failed",
                    trace_id=trace_id,
                    method=request.method,
                    path=request.url.path,
                )
                raise

            response.headers["X-Trace-Id"] = trace_id
            logger.info(
                "request_completed",
                trace_id=trace_id,
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                duration_ms=round((time.monotonic() - start) * 1000, 1),
            )
            return response

    def _register_oauth2_support(self) -> None:
        oauth2_cfg = self._config.oauth2 or {}
        authorize_url = oauth2_cfg.get("authorization_url")
        token_url = oauth2_cfg.get("token_url")
        client_id = oauth2_cfg.get("client_id")
        client_secret = oauth2_cfg.get("client_secret", "")
        if not authorize_url or not token_url or not client_id:
            self.oauth2: OAuth2Manager | None = None
            return

        self.oauth2 = OAuth2Manager(
            client_id=client_id,
            client_secret=client_secret,
            authorize_url=authorize_url,
            token_url=token_url,
            redirect_uri=oauth2_cfg.get("redirect_uri", "urn:ietf:wg:oauth:2.0:oob"),
            scopes=oauth2_cfg.get("scopes", []),
        )

        @self._fastapi.get("/oauth2/authorize", tags=["oauth2"])
        async def oauth2_authorize(state: str | None = None) -> dict[str, str]:
            assert self.oauth2 is not None
            return {"authorization_url": self.oauth2.get_authorization_url(state=state)}

        @self._fastapi.post("/oauth2/callback", tags=["oauth2"])
        async def oauth2_callback(payload: dict[str, Any]) -> dict[str, Any]:
            assert self.oauth2 is not None
            code = str(payload.get("code", "")).strip()
            account = str(payload.get("account", "default")).strip() or "default"
            if not code:
                return {"error": "Missing authorization code"}
            token = await self.oauth2.exchange_code(code, account=account)
            return token.model_dump()

        @self._fastapi.post("/oauth2/refresh", tags=["oauth2"])
        async def oauth2_refresh(payload: dict[str, Any]) -> dict[str, Any]:
            assert self.oauth2 is not None
            account = str(payload.get("account", "default")).strip() or "default"
            token = await self.oauth2.refresh_token(account=account)
            return token.model_dump()

    def _register_action_routes(self) -> None:
        for action_name, (meta, method) in self._actions.items():
            path_segment = action_name.replace(".", "/")
            path = f"/actions/{path_segment}"
            self._add_action_endpoint(path, action_name, meta, method)

    def _register_schema_routes(self) -> None:
        for action_name, (meta, _method) in self._actions.items():
            if not meta.dynamic_schema:
                continue
            path_segment = action_name.replace(".", "/")
            path = f"/schema/{path_segment}"
            self._add_schema_endpoint(path, action_name, meta)

    def _add_action_endpoint(self, path: str, action_name: str, meta: ActionMeta, method: Any) -> None:
        bound_method = method
        bound_name = action_name

        @self._fastapi.post(path, tags=["actions"], name=f"action_{action_name}")
        async def action_handler(request: Request) -> Response:
            payload = await request.json()
            trace_id = getattr(request.state, "trace_id", "")
            try:
                result = await bound_method(payload)
                return _build_action_response(result)
            except Exception as exc:
                logger.error("action_failed", action=bound_name, error=str(exc), trace_id=trace_id)
                return JSONResponse(
                    status_code=500,
                    content={"error": str(exc)},
                )

    def _add_schema_endpoint(self, path: str, action_name: str, meta: ActionMeta) -> None:
        bound_name = action_name
        bound_meta = meta

        @self._fastapi.get(path, tags=["schema"], name=f"schema_{action_name}")
        async def schema_handler() -> JSONResponse:
            return JSONResponse(
                content={
                    "connector_name": self.name,
                    "action": bound_name,
                    "input_fields": _schema_to_fields(bound_meta.input_schema),
                    "output_fields": _schema_to_fields(bound_meta.output_schema),
                }
            )

    def _register_webhook_routes(self) -> None:
        for webhook_name, (meta, method) in self._webhooks.items():
            path = f"/webhooks/{webhook_name}"
            self._add_webhook_endpoint(path, webhook_name, meta, method)

    def _add_webhook_endpoint(self, path: str, webhook_name: str, meta: WebhookMeta, method: Any) -> None:
        bound_method = method
        bound_name = webhook_name
        bound_meta = meta

        @self._fastapi.post(path, tags=["webhooks"], name=f"webhook_{webhook_name}")
        async def webhook_handler(request: Request) -> JSONResponse:
            body = await request.body()
            trace_id = getattr(request.state, "trace_id", "")

            if bound_meta.signature_header:
                sig_ok = self._verify_webhook_signature(
                    body, dict(request.headers), bound_meta, bound_name,
                )
                if not sig_ok:
                    return JSONResponse(
                        status_code=401,
                        content={"acknowledged": False, "error": "Invalid webhook signature"},
                    )

            import json as _json
            try:
                payload = _json.loads(body)
            except (ValueError, UnicodeDecodeError):
                return JSONResponse(
                    status_code=400,
                    content={"acknowledged": False, "error": "Invalid JSON payload"},
                )

            try:
                result = await bound_method(payload)
                return JSONResponse(content={"acknowledged": True, "data": result})
            except Exception as exc:
                logger.error("webhook_failed", webhook=bound_name, error=str(exc), trace_id=trace_id)
                return JSONResponse(
                    status_code=500,
                    content={"acknowledged": False, "error": str(exc)},
                )

    def _verify_webhook_signature(
        self,
        body: bytes,
        headers: dict[str, str],
        meta: WebhookMeta,
        webhook_name: str,
    ) -> bool:
        """Verify HMAC signature of an incoming webhook payload."""
        if not meta.signature_header:
            return True

        header_lower = {k.lower(): v for k, v in headers.items()}
        provided_sig = header_lower.get(meta.signature_header.lower(), "")
        if not provided_sig:
            logger.warning("webhook_signature_missing", webhook=webhook_name, header=meta.signature_header)
            return False

        secret = self._get_webhook_secret(webhook_name)
        if not secret:
            logger.error(
                "webhook_secret_not_configured",
                webhook=webhook_name,
                hint="Set WEBHOOK_SECRET_{NAME} env var or store 'webhook_secret' in account credentials",
            )
            return False

        algo_map = {
            "hmac-sha256": hashlib.sha256,
            "hmac-sha1": hashlib.sha1,
            "hmac-sha512": hashlib.sha512,
        }
        hash_fn = algo_map.get(meta.signature_algorithm, hashlib.sha256)
        computed = hmac.new(secret.encode(), body, hash_fn).hexdigest()

        clean_sig = provided_sig
        for prefix in ("sha256=", "sha1=", "sha512="):
            if clean_sig.startswith(prefix):
                clean_sig = clean_sig[len(prefix):]
                break

        if hmac.compare_digest(computed, clean_sig):
            return True

        logger.warning("webhook_signature_mismatch", webhook=webhook_name)
        return False

    def _get_webhook_secret(self, webhook_name: str) -> str | None:
        """Retrieve webhook signing secret from the account store or env."""
        import os
        env_key = f"WEBHOOK_SECRET_{webhook_name.upper().replace('.', '_').replace('-', '_')}"
        env_val = os.environ.get(env_key)
        if env_val:
            return env_val
        if self._account_store:
            for acc in self._account_store._accounts.values():
                secret = acc.get("webhook_secret") or acc.get("signing_secret")
                if secret:
                    return secret
        return None

    def _register_lifecycle_events(self) -> None:
        @self._fastapi.on_event("startup")
        async def on_startup() -> None:
            logger.info("connector_starting", name=self.name, version=self.version)
            self._start_triggers()

        @self._fastapi.on_event("shutdown")
        async def on_shutdown() -> None:
            logger.info("connector_stopping", name=self.name)
            for task in self._trigger_tasks:
                task.cancel()
            if self._http_client is not None:
                await self._http_client.close()

    def _register_rate_limiting(self) -> None:
        """Register per-action rate limiting middleware from Config.rate_limits."""
        rate_limits = self._config.rate_limits
        if not rate_limits:
            return

        buckets: dict[str, _TokenBucket] = {}

        if "default" in rate_limits:
            rate, burst = _parse_rate_spec(rate_limits["default"])
            buckets["__default__"] = _TokenBucket(rate, burst)

        for key, spec in rate_limits.items():
            if key == "default":
                continue
            rate, burst = _parse_rate_spec(spec)
            buckets[key] = _TokenBucket(rate, burst)

        from starlette.middleware.base import BaseHTTPMiddleware
        from starlette.responses import Response as StarletteResponse

        class _RateLimitMiddleware(BaseHTTPMiddleware):
            async def dispatch(self, request: Request, call_next: Any) -> StarletteResponse:
                path = request.url.path
                if "/actions/" not in path:
                    return await call_next(request)

                action_key = path.split("/actions/", 1)[1].replace("/", ".")
                bucket = buckets.get(action_key, buckets.get("__default__"))
                if bucket and not bucket.allow():
                    return JSONResponse(
                        status_code=429,
                        content={"error": "Rate limit exceeded"},
                        headers={"Retry-After": "1"},
                    )
                return await call_next(request)

        self._fastapi.add_middleware(_RateLimitMiddleware)

    def _start_triggers(self) -> None:
        for trigger_name, (meta, method) in self._triggers.items():
            task = asyncio.create_task(
                self._run_trigger_loop(trigger_name, meta.interval_seconds, method),
                name=f"trigger_{trigger_name}",
            )
            self._trigger_tasks.append(task)

    async def _run_trigger_loop(self, name: str, interval: int, method: Any) -> None:
        logger.info("trigger_started", trigger=name, interval_seconds=interval)
        last_run_at: datetime | None = None
        while True:
            started_at = datetime.now(timezone.utc)
            trace_id = str(uuid.uuid4())
            try:
                if _method_accepts_since(method):
                    events = await method(since=last_run_at)
                else:
                    events = await method()
                if events:
                    logger.info("trigger_emitted", trigger=name, event_count=len(events), trace_id=trace_id)
            except asyncio.CancelledError:
                break
            except Exception as exc:
                logger.error("trigger_error", trigger=name, error=str(exc), trace_id=trace_id)
            last_run_at = started_at
            try:
                await asyncio.sleep(interval)
            except asyncio.CancelledError:
                break

    @property
    def http(self) -> ConnectorHttpClient:
        if self._http_client is None:
            self._http_client = ConnectorHttpClient()
        return self._http_client

    @property
    def accounts(self) -> AccountStore:
        assert self._account_store is not None
        return self._account_store

    async def test_connection(self) -> bool:
        """Override in subclass to test external API connectivity."""
        raise NotImplementedError

    def generate_manifest(self) -> dict[str, Any]:
        """Generate a connector.yaml-compatible dict from class metadata and decorators."""
        action_routes: dict[str, dict[str, str]] = {}
        for action_name in self._actions:
            path_segment = action_name.replace(".", "/")
            action_routes[action_name] = {
                "method": "POST",
                "path": f"/actions/{path_segment}",
            }

        events: list[str] = []
        for trigger_name in self._triggers:
            events.append(trigger_name)
        for _, (meta, _) in self._webhooks.items():
            if meta.topic:
                events.append(meta.topic)

        manifest: dict[str, Any] = {
            "name": self.name,
            "category": self.category,
            "version": self.version,
            "display_name": self.display_name,
            "description": self.description,
            "interface": self.category,
            "service_name": f"connector-{self.name}",
            "capabilities": list(self._actions.keys()),
            "events": events,
            "actions": list(self._actions.keys()),
            "action_routes": action_routes,
            "config_schema": {
                "required": self._config.required_credentials,
            },
            "health_endpoint": "/health",
            "docs_url": "/docs",
        }
        if self._config.rate_limits:
            manifest["rate_limits"] = dict(self._config.rate_limits)
        if self._config.oauth2:
            manifest["oauth2"] = dict(self._config.oauth2)
        if self._webhooks:
            manifest["webhooks"] = {
                name: {
                    "topic": meta.topic,
                    "signature_header": meta.signature_header,
                    "signature_algorithm": meta.signature_algorithm,
                }
                for name, (meta, _) in self._webhooks.items()
            }
        return manifest

    def run(self, host: str = "0.0.0.0", port: int | None = None) -> None:
        """Start the connector with uvicorn."""
        effective_port = port or self._config.port
        logger.info(
            "connector_run",
            name=self.name,
            host=host,
            port=effective_port,
        )
        uvicorn.run(
            self._fastapi,
            host=host,
            port=effective_port,
            log_level="info",
        )


def _build_action_response(result: Any) -> Response:
    """Normalize action return values into HTTP responses.

    Successful actions should return the raw domain payload so the platform
    can consume top-level fields directly. A connector may also return a dict
    containing ``status_code`` to signal an HTTP error or alternate success
    code without raising an exception.
    """
    if isinstance(result, Response):
        return result

    status_code = 200
    payload = result

    if isinstance(result, tuple) and len(result) == 2 and isinstance(result[1], int):
        payload, status_code = result
    elif isinstance(result, dict):
        embedded_status = result.get("status_code")
        if isinstance(embedded_status, int):
            status_code = embedded_status

    return JSONResponse(
        status_code=status_code,
        content=jsonable_encoder(payload),
    )


def _schema_to_fields(schema: Any) -> list[dict[str, Any]]:
    if schema is None:
        return []

    if hasattr(schema, "model_json_schema"):
        schema = schema.model_json_schema()

    if not isinstance(schema, dict):
        return []

    properties = schema.get("properties")
    required = set(schema.get("required", []))
    if isinstance(properties, dict):
        fields: list[dict[str, Any]] = []
        for field_name, field_schema in properties.items():
            if not isinstance(field_schema, dict):
                continue
            field_type = field_schema.get("type")
            if not field_type and field_schema.get("anyOf"):
                any_of = field_schema["anyOf"]
                if isinstance(any_of, list) and any_of:
                    field_type = any_of[0].get("type", "string")
            fields.append(
                {
                    "field": field_name,
                    "label": field_schema.get("title", field_name),
                    "type": field_type or "string",
                    "required": field_name in required,
                    "description": field_schema.get("description"),
                }
            )
        return fields

    if isinstance(schema.get("fields"), list):
        return [
            {
                "field": item.get("field"),
                "label": item.get("label", item.get("field")),
                "type": item.get("type", "string"),
                "required": bool(item.get("required", False)),
                "description": item.get("description"),
            }
            for item in schema["fields"]
            if isinstance(item, dict) and item.get("field")
        ]

    if all(isinstance(value, str) for value in schema.values()):
        return [
            {
                "field": key,
                "label": key,
                "type": value,
                "required": key in required,
                "description": None,
            }
            for key, value in schema.items()
        ]

    return []


def _method_accepts_since(method: Any) -> bool:
    """Return True when a trigger method can accept a ``since`` kwarg."""
    signature = inspect.signature(method)
    for param in signature.parameters.values():
        if param.kind == inspect.Parameter.VAR_KEYWORD:
            return True
        if param.name == "since" and param.kind in (
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
            inspect.Parameter.KEYWORD_ONLY,
        ):
            return True
    return False
