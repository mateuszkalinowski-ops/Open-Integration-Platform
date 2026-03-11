from __future__ import annotations

import asyncio
import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from pinquark_connector_sdk import ConnectorApp, action, trigger, webhook
from pinquark_connector_sdk.testing import ConnectorTestClient


class DemoConnector(ConnectorApp):
    name = "demo"
    category = "other"
    version = "1.0.0"
    display_name = "Demo"
    description = "SDK contract test connector"

    class Config:
        rate_limits = {"default": "2/s"}

    def __init__(self) -> None:
        self.upstream_ok = False
        super().__init__()

    @action("ping")
    async def ping(self, payload: dict) -> dict:
        return {"pong": True, "payload": payload}

    @action("validate")
    async def validate(self, payload: dict) -> dict:
        if payload.get("fail"):
            return {"error": "invalid payload", "status_code": 422}
        return {"ok": True}

    @action(
        "rates.get",
        output_schema={
            "properties": {
                "products": {"type": "array", "title": "Products"},
                "currency": {"type": "string", "title": "Currency"},
            },
            "required": ["products"],
        },
        dynamic_schema=True,
    )
    async def get_rates(self, payload: dict) -> dict:
        return {"products": [], "currency": payload.get("currency", "PLN")}

    @webhook("order.created", signature_header="X-Test-Signature")
    async def order_created(self, payload: dict) -> dict:
        return payload

    async def test_connection(self) -> bool:
        return self.upstream_ok


class TriggerConnector(ConnectorApp):
    name = "trigger-demo"
    category = "other"
    version = "1.0.0"
    display_name = "Trigger Demo"
    description = "SDK trigger contract test connector"

    def __init__(self) -> None:
        self.seen_since = []
        super().__init__()

    @trigger("orders.poll", interval_seconds=1)
    async def poll_orders(self, since=None):  # noqa: ANN001
        self.seen_since.append(since)
        return []

    async def test_connection(self) -> bool:
        return True


@pytest.mark.asyncio
async def test_health_and_readiness_reflect_test_connection() -> None:
    async with ConnectorTestClient(DemoConnector()) as client:
        health = await client.get("/health")
        readiness = await client.get("/readiness")

    assert health.status_code == 200
    assert health.json()["status"] == "degraded"
    assert health.json()["checks"]["upstream_api"] == "unreachable"

    assert readiness.status_code == 200
    assert readiness.json()["status"] == "not_ready"
    assert readiness.json()["checks"]["upstream_api"] == "unreachable"


@pytest.mark.asyncio
async def test_actions_return_raw_payload_not_sdk_envelope() -> None:
    async with ConnectorTestClient(DemoConnector()) as client:
        response = await client.post("/actions/ping", json={"hello": "world"})

    assert response.status_code == 200
    assert response.json() == {"pong": True, "payload": {"hello": "world"}}


@pytest.mark.asyncio
async def test_action_status_code_dict_is_mapped_to_http_status() -> None:
    async with ConnectorTestClient(DemoConnector()) as client:
        response = await client.post("/actions/validate", json={"fail": True})

    assert response.status_code == 422
    assert response.json() == {"error": "invalid payload", "status_code": 422}


@pytest.mark.asyncio
async def test_trace_id_is_echoed_back_in_response_headers() -> None:
    async with ConnectorTestClient(DemoConnector()) as client:
        response = await client.get("/health", headers={"X-Trace-Id": "trace-123"})

    assert response.status_code == 200
    assert response.headers["X-Trace-Id"] == "trace-123"


@pytest.mark.asyncio
async def test_rate_limit_applies_only_to_actions() -> None:
    async with ConnectorTestClient(DemoConnector()) as client:
        assert (await client.get("/health")).status_code == 200
        assert (await client.get("/readiness")).status_code == 200

        first = await client.post("/actions/ping", json={"i": 1})
        second = await client.post("/actions/ping", json={"i": 2})
        third = await client.post("/actions/ping", json={"i": 3})

    assert first.status_code == 200
    assert second.status_code == 200
    assert third.status_code == 429


@pytest.mark.asyncio
async def test_account_delete_returns_empty_204_response() -> None:
    async with ConnectorTestClient(DemoConnector()) as client:
        create = await client.setup_account("demo-account", {"api_key": "abc"})
        delete = await client.delete("/accounts/demo-account")

    assert create.status_code == 201
    assert delete.status_code == 204
    assert delete.text == ""


@pytest.mark.asyncio
async def test_webhook_requires_signature_secret() -> None:
    async with ConnectorTestClient(DemoConnector()) as client:
        response = await client.post(
            "/webhooks/order.created",
            json={"id": "evt-1"},
            headers={"X-Test-Signature": "sha256=bad"},
        )

    assert response.status_code == 401
    assert response.json()["acknowledged"] is False


@pytest.mark.asyncio
async def test_dynamic_schema_endpoint_is_exposed_for_sdk_actions() -> None:
    async with ConnectorTestClient(DemoConnector()) as client:
        response = await client.get("/schema/rates/get")

    assert response.status_code == 200
    payload = response.json()
    assert payload["action"] == "rates.get"
    assert {field["field"] for field in payload["output_fields"]} == {"products", "currency"}


@pytest.mark.asyncio
async def test_trigger_loop_passes_since_when_handler_accepts_it(monkeypatch: pytest.MonkeyPatch) -> None:
    connector = TriggerConnector()

    async def _cancel_sleep(_seconds: int) -> None:
        raise asyncio.CancelledError

    monkeypatch.setattr("pinquark_connector_sdk.app.asyncio.sleep", _cancel_sleep)

    await connector._run_trigger_loop("orders.poll", 1, connector.poll_orders)

    assert connector.seen_since == [None]
