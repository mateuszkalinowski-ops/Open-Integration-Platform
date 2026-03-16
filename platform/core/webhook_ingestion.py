"""Webhook ingestion service — signature verification, dedup, and routing.

Receives external webhook payloads, verifies signatures using connector-specific
algorithms, deduplicates by external_id via Redis, persists to webhook_events,
and triggers matching flows/workflows.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import time
import uuid
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from typing import Any

import structlog
from db.models import WebhookEvent
from prometheus_client import Counter, Histogram
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.connector_registry import ConnectorManifest, ConnectorRegistry
from core.credential_vault import CredentialVault

logger = structlog.get_logger(__name__)

WEBHOOK_RECEIVED = Counter(
    "webhook_events_received_total",
    "Total webhook events received",
    ["connector", "event"],
)
WEBHOOK_PROCESSED = Counter(
    "webhook_events_processed_total",
    "Webhook events successfully processed",
    ["connector", "event"],
)
WEBHOOK_FAILED = Counter(
    "webhook_events_failed_total",
    "Webhook events that failed processing",
    ["connector", "event", "reason"],
)
WEBHOOK_LATENCY = Histogram(
    "webhook_processing_duration_seconds",
    "Webhook processing latency",
    ["connector"],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0],
)

_DEDUP_TTL = 86400  # 24 hours
_DEDUP_PREFIX = "webhook:dedup:"

_ALGORITHMS: dict[str, Callable[[bytes, bytes], str]] = {
    "hmac-sha256": lambda key, body: hmac.new(key, body, hashlib.sha256).hexdigest(),
    "hmac-sha1": lambda key, body: hmac.new(key, body, hashlib.sha1).hexdigest(),
    "hmac-sha512": lambda key, body: hmac.new(key, body, hashlib.sha512).hexdigest(),
}


def verify_signature(
    body: bytes,
    signature: str,
    secret: str,
    algorithm: str = "hmac-sha256",
) -> bool:
    """Verify a webhook signature using the specified algorithm."""
    algo_fn = _ALGORITHMS.get(algorithm.lower())
    if algo_fn is None:
        logger.warning("webhook.unknown_algorithm", algorithm=algorithm)
        return False

    expected = algo_fn(secret.encode(), body)

    clean_sig = signature
    for prefix in ("sha256=", "sha1=", "sha512="):
        if clean_sig.startswith(prefix):
            clean_sig = clean_sig[len(prefix) :]
            break

    return hmac.compare_digest(expected, clean_sig)


_MAX_RETRIES_BEFORE_DLQ = 3


class WebhookIngestionService:
    """Handles incoming webhooks: verify, dedup, persist, route asynchronously."""

    def __init__(
        self,
        registry: ConnectorRegistry,
        vault: CredentialVault,
        redis_getter: Callable[[], Awaitable[Any]],
        session_factory: Any = None,
    ) -> None:
        self._registry = registry
        self._vault = vault
        self._redis_getter = redis_getter
        self._session_factory = session_factory

    async def ingest_webhook(
        self,
        db: AsyncSession,
        connector_name: str,
        event_type: str,
        body: bytes,
        headers: dict[str, str],
        tenant_id: uuid.UUID,
        *,
        require_signature: bool = False,
    ) -> dict[str, Any]:
        """Verify, dedup, persist, and return 200 immediately. Processing is async.

        When ``require_signature`` is True (tenant inferred, not verified via
        API key), the webhook is rejected unless signature verification passes.
        """
        WEBHOOK_RECEIVED.labels(connector=connector_name, event=event_type).inc()

        try:
            payload = json.loads(body)
        except (json.JSONDecodeError, UnicodeDecodeError):
            WEBHOOK_FAILED.labels(connector=connector_name, event=event_type, reason="invalid_json").inc()
            return {"status": "rejected", "reason": "Invalid JSON payload"}

        manifest = self._get_manifest(connector_name)
        webhook_config = self._get_webhook_config(manifest, event_type) if manifest else None

        sig_valid: bool | None = None
        if webhook_config:
            sig_valid = await self._verify(
                db,
                webhook_config,
                body,
                headers,
                tenant_id,
                connector_name,
            )
            if sig_valid is False:
                WEBHOOK_FAILED.labels(connector=connector_name, event=event_type, reason="bad_signature").inc()
                return {"status": "rejected", "reason": "Invalid signature"}
        elif require_signature:
            WEBHOOK_FAILED.labels(connector=connector_name, event=event_type, reason="no_signature_config").inc()
            logger.warning(
                "webhook.rejected_no_signature_config",
                connector=connector_name,
                event_type=event_type,
            )
            return {
                "status": "rejected",
                "reason": "Webhook signature verification required but not configured for this event",
            }

        external_id = self._extract_external_id(headers, payload)
        if external_id:
            is_dup = await self._check_dedup(connector_name, event_type, external_id)
            if is_dup:
                return {"status": "duplicate", "external_id": external_id}

        webhook_event = WebhookEvent(
            tenant_id=tenant_id,
            connector_name=connector_name,
            event_type=event_type,
            external_id=external_id,
            payload=payload,
            headers=dict(headers),
            signature_valid=sig_valid,
            processing_status="received",
        )
        db.add(webhook_event)
        await db.flush()

        if external_id:
            await self._mark_dedup(connector_name, event_type, external_id)

        webhook_id = str(webhook_event.id)
        return {"status": "accepted", "webhook_id": webhook_id, "external_id": external_id}

    async def process_webhook_async(
        self,
        webhook_id: uuid.UUID,
        process_event_fn: Callable[..., Awaitable[Any]],
    ) -> None:
        """Process a persisted webhook event in the background."""
        if self._session_factory is None:
            logger.error("webhook.no_session_factory")
            return

        start = time.monotonic()
        async with self._session_factory() as db:
            from db.base import set_rls_bypass

            await set_rls_bypass(db)

            result = await db.execute(select(WebhookEvent).where(WebhookEvent.id == webhook_id))
            event = result.scalar_one_or_none()
            if event is None:
                return

            try:
                event.processing_status = "processing"
                await db.flush()
                exec_result = await process_event_fn(
                    connector_name=event.connector_name,
                    event=event.event_type,
                    event_data=event.payload,
                    tenant_id=event.tenant_id,
                )
                event.processing_status = "processed"
                event.processed_at = datetime.now(UTC)
                event.error = None

                duration = time.monotonic() - start
                WEBHOOK_PROCESSED.labels(connector=event.connector_name, event=event.event_type).inc()
                WEBHOOK_LATENCY.labels(connector=event.connector_name).observe(duration)

                logger.info(
                    "webhook.processed_async",
                    webhook_id=str(webhook_id),
                    connector=event.connector_name,
                    event=event.event_type,
                    flows_triggered=exec_result.get("flows_triggered", 0),
                    workflows_triggered=exec_result.get("workflows_triggered", 0),
                    duration_ms=round(duration * 1000, 1),
                )
            except Exception as exc:
                event.retry_count += 1
                event.error = str(exc)[:2000]

                if event.retry_count >= _MAX_RETRIES_BEFORE_DLQ:
                    event.processing_status = "dead_letter"
                    WEBHOOK_FAILED.labels(
                        connector=event.connector_name,
                        event=event.event_type,
                        reason="dead_letter",
                    ).inc()
                    logger.error(
                        "webhook.dead_letter",
                        webhook_id=str(webhook_id),
                        connector=event.connector_name,
                        retries=event.retry_count,
                        error=str(exc),
                    )
                else:
                    event.processing_status = "failed"
                    WEBHOOK_FAILED.labels(
                        connector=event.connector_name,
                        event=event.event_type,
                        reason="processing",
                    ).inc()
                    logger.warning(
                        "webhook.processing_failed",
                        webhook_id=str(webhook_id),
                        connector=event.connector_name,
                        retry_count=event.retry_count,
                        error=str(exc),
                    )

            await db.commit()

    async def replay_webhook(
        self,
        db: AsyncSession,
        webhook_id: uuid.UUID,
        process_event_fn: Callable[..., Awaitable[Any]],
    ) -> dict[str, Any]:
        """Replay a previously received webhook."""
        result = await db.execute(select(WebhookEvent).where(WebhookEvent.id == webhook_id))
        event = result.scalar_one_or_none()
        if event is None:
            return {"status": "not_found"}

        try:
            event.processing_status = "processing"
            await db.flush()
            exec_result = await process_event_fn(
                connector_name=event.connector_name,
                event=event.event_type,
                event_data=event.payload,
                tenant_id=event.tenant_id,
            )
            event.processing_status = "processed"
            event.processed_at = datetime.now(UTC)
            event.error = None
            event.retry_count += 1
            await db.flush()
            return {"status": "replayed", "result": exec_result}
        except Exception as exc:
            event.processing_status = "failed"
            event.error = str(exc)[:2000]
            event.retry_count += 1
            await db.flush()
            return {"status": "replay_failed", "error": str(exc)}

    def _get_manifest(self, connector_name: str) -> ConnectorManifest | None:
        manifests = self._registry.get_by_name(connector_name)
        return manifests[0] if manifests else None

    def _get_webhook_config(
        self,
        manifest: ConnectorManifest,
        event_type: str,
    ) -> dict[str, Any] | None:
        webhooks: dict[str, Any] = getattr(manifest, "webhooks", {}) or {}
        return webhooks.get(event_type)

    async def _verify(
        self,
        db: AsyncSession,
        webhook_config: dict[str, Any],
        body: bytes,
        headers: dict[str, str],
        tenant_id: uuid.UUID,
        connector_name: str,
    ) -> bool | None:
        sig_header = webhook_config.get("signature_header")
        if not sig_header:
            return None

        signature = headers.get(sig_header) or headers.get(sig_header.lower())
        if not signature:
            return False

        secret_field = webhook_config.get("signature_key_field", "webhook_secret")
        algorithm = webhook_config.get("signature_algorithm", "hmac-sha256")

        secret = await self._vault.retrieve(db, tenant_id, connector_name, secret_field)
        if not secret:
            logger.warning(
                "webhook.signature_required_but_no_secret",
                connector=connector_name,
                field=secret_field,
            )
            return False

        return verify_signature(body, signature, secret, algorithm)

    @staticmethod
    def _extract_external_id(headers: dict[str, str], payload: dict[str, Any]) -> str | None:
        for key in ("X-Webhook-Id", "X-Request-Id", "X-Event-Id", "x-webhook-id", "x-request-id"):
            if key in headers:
                return headers[key]
        for field in ("id", "event_id", "message_id", "webhook_id"):
            if field in payload and isinstance(payload[field], (str, int)):
                return str(payload[field])
        return None

    async def _check_dedup(self, connector: str, event: str, external_id: str) -> bool:
        redis = await self._redis_getter()
        key = f"{_DEDUP_PREFIX}{connector}:{event}:{external_id}"
        return bool(await redis.exists(key))

    async def _mark_dedup(self, connector: str, event: str, external_id: str) -> None:
        redis = await self._redis_getter()
        key = f"{_DEDUP_PREFIX}{connector}:{event}:{external_id}"
        await redis.set(key, "1", ex=_DEDUP_TTL)
