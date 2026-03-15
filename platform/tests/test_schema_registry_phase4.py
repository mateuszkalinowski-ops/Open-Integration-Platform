from __future__ import annotations

import json

import pytest
from core.connector_registry import ConnectorManifest, ConnectorRegistry
from core.schema_registry import SchemaRegistry


class _FakeRedis:
    def __init__(self) -> None:
        self.values: dict[str, str] = {}

    async def get(self, key: str) -> str | None:
        return self.values.get(key)

    async def set(self, key: str, value: str, ex: int | None = None) -> None:
        self.values[key] = value


async def _get_redis(redis: _FakeRedis) -> _FakeRedis:
    return redis


async def _record_invalidation(target: list[str | None], connector_name: str | None) -> None:
    target.append(connector_name)


async def _record_change(target: list[dict[str, object]], event: dict[str, object]) -> None:
    target.append(event)


def _manifest() -> ConnectorManifest:
    return ConnectorManifest(
        name="inpost",
        category="courier",
        version="3.0.0",
        display_name="InPost",
        description="Schema registry test",
        interface="courier",
        action_fields={"rates.get": [{"field": "weight", "label": "Weight", "type": "number", "required": True}]},
        output_fields={"rates.get": [{"field": "products", "label": "Products", "type": "object[]"}]},
    )


@pytest.mark.asyncio
async def test_schema_registry_merges_dynamic_and_static_fields(monkeypatch: pytest.MonkeyPatch) -> None:
    registry = ConnectorRegistry()
    registry._connectors = {"courier/inpost/3.0.0": _manifest()}
    redis = _FakeRedis()
    schema_registry = SchemaRegistry(registry, lambda: _get_redis(redis))

    async def _fake_fetch(*_args, **_kwargs):
        return {
            "input_fields": [{"field": "service", "label": "Service", "type": "string"}],
            "output_fields": [{"field": "currency", "label": "Currency", "type": "string"}],
        }

    monkeypatch.setattr(schema_registry, "_fetch_dynamic_schema", _fake_fetch)

    result = await schema_registry.get_action_schema(
        "inpost", "rates.get", connector_version="3.0.0", tenant_id="tenant-1"
    )

    assert result["source"] == "merged"
    assert {field["field"] for field in result["input_fields"]} == {"weight", "service"}
    assert {field["field"] for field in result["output_fields"]} == {"products", "currency"}

    cached = json.loads(redis.values["schema:inpost:rates.get:tenant-1"])
    assert cached["source"] == "merged"


@pytest.mark.asyncio
async def test_schema_registry_uses_cached_value_before_fetch(monkeypatch: pytest.MonkeyPatch) -> None:
    registry = ConnectorRegistry()
    registry._connectors = {"courier/inpost/3.0.0": _manifest()}
    redis = _FakeRedis()
    redis.values["schema:inpost:rates.get:tenant-1"] = json.dumps(
        {
            "connector_name": "inpost",
            "connector_version": "3.0.0",
            "tenant_id": "tenant-1",
            "action": "rates.get",
            "source": "dynamic",
            "cached": False,
            "input_fields": [{"field": "weight", "label": "Weight", "type": "number", "required": True}],
            "output_fields": [],
        }
    )
    schema_registry = SchemaRegistry(registry, lambda: _get_redis(redis))

    async def _unexpected_fetch(*_args, **_kwargs):
        raise AssertionError("dynamic fetch should not run when cache is present")

    monkeypatch.setattr(schema_registry, "_fetch_dynamic_schema", _unexpected_fetch)

    result = await schema_registry.get_action_schema(
        "inpost", "rates.get", connector_version="3.0.0", tenant_id="tenant-1"
    )

    assert result["cached"] is True
    assert result["source"] == "dynamic"


def test_schema_registry_diff_detects_added_removed_and_changed_fields() -> None:
    registry = ConnectorRegistry()
    schema_registry = SchemaRegistry(registry, lambda: _get_redis(_FakeRedis()))

    diff = schema_registry.diff_schemas(
        {
            "input_fields": [{"field": "weight", "label": "Weight", "type": "number"}],
            "output_fields": [{"field": "products", "label": "Products", "type": "object[]"}],
        },
        {
            "input_fields": [
                {"field": "weight", "label": "Shipment weight", "type": "number"},
                {"field": "service", "label": "Service", "type": "string"},
            ],
            "output_fields": [],
        },
    )

    assert diff["changed"] is True
    assert diff["input_fields"]["added"] == ["service"]
    assert diff["input_fields"]["changed_fields"] == ["weight"]
    assert diff["output_fields"]["removed"] == ["products"]


@pytest.mark.asyncio
async def test_schema_registry_refresh_invalidates_mapping_cache_on_change(monkeypatch: pytest.MonkeyPatch) -> None:
    registry = ConnectorRegistry()
    registry._connectors = {"courier/inpost/3.0.0": _manifest()}
    redis = _FakeRedis()
    invalidated: list[str | None] = []
    changes: list[dict[str, object]] = []
    schema_registry = SchemaRegistry(
        registry,
        lambda: _get_redis(redis),
        mapping_invalidator=lambda connector_name: _record_invalidation(invalidated, connector_name),
        change_handler=lambda event: _record_change(changes, event),
    )
    redis.values["schema:inpost:rates.get:tenant-1"] = json.dumps(
        {
            "connector_name": "inpost",
            "connector_version": "3.0.0",
            "tenant_id": "tenant-1",
            "action": "rates.get",
            "source": "dynamic",
            "cached": False,
            "input_fields": [{"field": "weight", "label": "Weight", "type": "number"}],
            "output_fields": [],
        }
    )

    async def _fake_fetch(*_args, **_kwargs):
        return {
            "input_fields": [
                {"field": "weight", "label": "Weight", "type": "number"},
                {"field": "service", "label": "Service", "type": "string"},
            ],
            "output_fields": [],
        }

    monkeypatch.setattr(schema_registry, "_fetch_dynamic_schema", _fake_fetch)
    await schema_registry.get_action_schema("inpost", "rates.get", connector_version="3.0.0", tenant_id="tenant-1")
    await schema_registry.refresh_observed_schemas()

    assert invalidated == ["inpost"]
    assert changes
    assert changes[0]["tenant_id"] == "tenant-1"
    assert changes[0]["diff"]["input_fields"]["added"] == ["service"]
