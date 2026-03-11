"""ConnectorApp — the main framework class for building connectors."""

from __future__ import annotations

import asyncio
from typing import Any

import structlog
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from pinquark_connector_sdk.accounts import AccountStore, register_account_routes
from pinquark_connector_sdk.decorators import ActionMeta, ConnectorMeta, TriggerMeta, WebhookMeta
from pinquark_connector_sdk.health import _HealthState, register_health_routes
from pinquark_connector_sdk.http import ConnectorHttpClient
from pinquark_connector_sdk.metrics import register_metrics

logger = structlog.get_logger(__name__)


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
        self._register_action_routes()
        self._register_webhook_routes()
        self._register_lifecycle_events()

    def _register_action_routes(self) -> None:
        for action_name, (meta, method) in self._actions.items():
            path_segment = action_name.replace(".", "/")
            path = f"/actions/{path_segment}"
            self._add_action_endpoint(path, action_name, meta, method)

    def _add_action_endpoint(self, path: str, action_name: str, meta: ActionMeta, method: Any) -> None:
        @self._fastapi.post(path, tags=["actions"], name=f"action_{action_name}")
        async def action_handler(request: Request, _method: Any = method, _name: str = action_name) -> JSONResponse:
            payload = await request.json()
            try:
                result = await _method(payload)
                return JSONResponse(content={"success": True, "data": result})
            except Exception as exc:
                logger.error("action_failed", action=_name, error=str(exc))
                return JSONResponse(
                    status_code=500,
                    content={"success": False, "error": str(exc)},
                )

    def _register_webhook_routes(self) -> None:
        for webhook_name, (meta, method) in self._webhooks.items():
            path = f"/webhooks/{webhook_name}"
            self._add_webhook_endpoint(path, webhook_name, meta, method)

    def _add_webhook_endpoint(self, path: str, webhook_name: str, meta: WebhookMeta, method: Any) -> None:
        @self._fastapi.post(path, tags=["webhooks"], name=f"webhook_{webhook_name}")
        async def webhook_handler(
            request: Request, _method: Any = method, _name: str = webhook_name
        ) -> JSONResponse:
            payload = await request.json()
            try:
                result = await _method(payload)
                return JSONResponse(content={"acknowledged": True, "data": result})
            except Exception as exc:
                logger.error("webhook_failed", webhook=_name, error=str(exc))
                return JSONResponse(
                    status_code=500,
                    content={"acknowledged": False, "error": str(exc)},
                )

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

    def _start_triggers(self) -> None:
        for trigger_name, (meta, method) in self._triggers.items():
            task = asyncio.create_task(
                self._run_trigger_loop(trigger_name, meta.interval_seconds, method),
                name=f"trigger_{trigger_name}",
            )
            self._trigger_tasks.append(task)

    async def _run_trigger_loop(self, name: str, interval: int, method: Any) -> None:
        logger.info("trigger_started", trigger=name, interval_seconds=interval)
        while True:
            try:
                events = await method()
                if events:
                    logger.info("trigger_emitted", trigger=name, event_count=len(events))
            except asyncio.CancelledError:
                break
            except Exception as exc:
                logger.error("trigger_error", trigger=name, error=str(exc))
            await asyncio.sleep(interval)

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
        for webhook_name, (meta, _) in self._webhooks.items():
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
