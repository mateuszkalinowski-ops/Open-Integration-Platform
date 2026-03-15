from __future__ import annotations

import json
import uuid

import pytest
from core.webhook_ingestion import WebhookIngestionService


class _DummyDb:
    def __init__(self) -> None:
        self.added = []

    def add(self, value) -> None:
        self.added.append(value)

    async def flush(self) -> None:
        if self.added:
            self.added[-1].id = uuid.uuid4()


class _DummyRegistry:
    def get_by_name(self, _name: str):
        return []


class _DummyVault:
    async def retrieve(self, db, tenant_id, connector_name, secret_field):
        return None


@pytest.mark.asyncio
async def test_ingest_webhook_persists_received_status() -> None:
    async def _redis_getter():
        class _Redis:
            async def exists(self, _key):
                return 0

            async def set(self, _key, _value, ex=None):
                return True

        return _Redis()

    service = WebhookIngestionService(
        registry=_DummyRegistry(),
        vault=_DummyVault(),
        redis_getter=_redis_getter,
    )
    db = _DummyDb()
    tenant_id = uuid.uuid4()

    result = await service.ingest_webhook(
        db,
        "shopify",
        "order.created",
        json.dumps({"id": "evt-1"}).encode(),
        {"X-Webhook-Id": "evt-1"},
        tenant_id,
    )

    assert result["status"] == "accepted"
    assert db.added[0].processing_status == "received"
