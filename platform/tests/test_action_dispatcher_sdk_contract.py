from __future__ import annotations

import pathlib
import sys
import uuid

import httpx
import pytest
from fastapi import HTTPException

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "sdk/python"))

from core.action_dispatcher import dispatch_action, set_rate_limiter
from core.connector_registry import ConnectorManifest

from pinquark_connector_sdk import ConnectorApp, action


class DemoSdkConnector(ConnectorApp):
    name = "demo-sdk"
    category = "other"
    version = "1.0.0"
    display_name = "Demo SDK"
    description = "Dispatch contract test connector"

    @action("ping")
    async def ping(self, payload: dict) -> dict:
        return {"pong": True, "payload": payload}

    @action("fail")
    async def fail(self, payload: dict) -> dict:
        return {"error": "bad request", "status_code": 422, "payload": payload}


class _AsgiBackedClient(httpx.AsyncClient):
    def __init__(self, *args, **kwargs) -> None:
        kwargs["transport"] = httpx.ASGITransport(app=DemoSdkConnector()._fastapi)
        kwargs["base_url"] = "http://connector-demo-sdk:8000"
        super().__init__(*args, **kwargs)


def _manifest() -> ConnectorManifest:
    return ConnectorManifest(
        name="demo-sdk",
        category="other",
        version="1.0.0",
        display_name="Demo SDK",
        description="Dispatch contract test connector",
        interface="other",
        actions=["ping", "fail"],
        action_routes={},
        service_name="connector-demo-sdk",
    )


@pytest.mark.asyncio
async def test_dispatch_action_returns_raw_sdk_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("core.action_dispatcher.httpx.AsyncClient", _AsgiBackedClient)

    result = await dispatch_action(
        connector_name="demo-sdk",
        action="ping",
        payload={"hello": "world"},
        tenant_id=uuid.uuid4(),
        registry=None,
        credentials=None,
    )

    assert result == {"pong": True, "payload": {"hello": "world"}}


@pytest.mark.asyncio
async def test_dispatch_action_raises_for_sdk_http_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("core.action_dispatcher.httpx.AsyncClient", _AsgiBackedClient)

    with pytest.raises(httpx.HTTPStatusError):
        await dispatch_action(
            connector_name="demo-sdk",
            action="fail",
            payload={"hello": "world"},
            tenant_id=uuid.uuid4(),
            registry=None,
            credentials=None,
        )


@pytest.mark.asyncio
async def test_dispatch_action_respects_manifest_action_route(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("core.action_dispatcher.httpx.AsyncClient", _AsgiBackedClient)
    manifest = _manifest()
    manifest.action_routes = {"ping": {"method": "POST", "path": "/actions/ping"}}

    result = await dispatch_action(
        connector_name="demo-sdk",
        action="ping",
        payload={"route": "manifest"},
        tenant_id=uuid.uuid4(),
        registry=type("Registry", (), {"get_by_name_version": staticmethod(lambda *_args, **_kwargs: manifest)})(),
        credentials=None,
    )

    assert result == {"pong": True, "payload": {"route": "manifest"}}


@pytest.mark.asyncio
async def test_dispatch_action_enforces_registered_rate_limiter() -> None:
    class _AlwaysLimitedRateLimiter:
        async def check(self, connector_name, action, tenant_id, connector_version=None):
            return type(
                "RateLimitResult",
                (),
                {
                    "allowed": False,
                    "retry_after": 1.5,
                    "limit": 1,
                    "window_seconds": 60,
                },
            )()

    set_rate_limiter(_AlwaysLimitedRateLimiter())
    try:
        with pytest.raises(HTTPException) as exc_info:
            await dispatch_action(
                connector_name="demo-sdk",
                action="ping",
                payload={"hello": "world"},
                tenant_id=uuid.uuid4(),
                registry=None,
                credentials=None,
            )
    finally:
        set_rate_limiter(None)

    assert exc_info.value.status_code == 429
    assert exc_info.value.detail["code"] == "CONNECTOR_RATE_LIMITED"
