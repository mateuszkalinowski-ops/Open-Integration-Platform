"""Sync State Manager — tracks incremental sync state between systems.

Provides deduplication, change detection (content hash), and retry logic
for workflow-based data synchronization. State is persisted in the
``sync_ledger`` PostgreSQL table.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import SyncLedger


class SyncDecision(str, Enum):
    SYNC = "sync"
    UPDATE = "update"
    SKIP = "skip"
    RETRY = "retry"


@dataclass
class SyncCheckResult:
    decision: SyncDecision
    existing_hash: str | None = None
    attempt_count: int = 0
    ledger_id: uuid.UUID | None = None


def compute_content_hash(
    data: dict[str, Any],
    hash_fields: list[str] | None = None,
) -> str:
    """Deterministic SHA-256 hash of event data for change detection.

    If ``hash_fields`` is ``["*"]`` or ``None``, hash the entire payload
    (excluding internal metadata). Otherwise hash only the listed fields.
    """
    if hash_fields and hash_fields != ["*"]:
        subset = {k: data.get(k) for k in hash_fields}
    else:
        subset = {
            k: v for k, v in data.items()
            if not k.startswith("_") and k not in ("account_name", "polled_at")
        }
    raw = json.dumps(subset, sort_keys=True, default=str)
    return hashlib.sha256(raw.encode()).hexdigest()


def resolve_entity_key(
    data: dict[str, Any],
    key_field: str | list[str],
) -> str:
    """Extract a unique entity key from event data.

    Supports simple field (``"erp_id"``), nested dot-notation
    (``"document.erp_id"``), and composite keys (``["source", "erp_id"]``).
    """
    if isinstance(key_field, list):
        parts = [str(_get_nested(data, f) or "") for f in key_field]
        return ":".join(parts)
    return str(_get_nested(data, key_field) or "")


def _get_nested(data: dict[str, Any], path: str) -> Any:
    current: Any = data
    for part in path.split("."):
        if isinstance(current, dict):
            current = current.get(part)
        else:
            return None
    return current


class SyncStateManager:
    """Manages sync state for workflows with ``sync_config`` enabled."""

    async def should_sync(
        self,
        db: AsyncSession,
        workflow_id: uuid.UUID,
        entity_key: str,
        content_hash: str,
        max_retries: int = 3,
    ) -> SyncCheckResult:
        """Check the ledger and decide whether this entity should be synced."""
        result = await db.execute(
            select(SyncLedger).where(
                SyncLedger.workflow_id == workflow_id,
                SyncLedger.entity_key == entity_key,
            )
        )
        entry = result.scalar_one_or_none()

        if entry is None:
            return SyncCheckResult(decision=SyncDecision.SYNC)

        if entry.sync_status == "failed" and entry.attempt_count < max_retries:
            return SyncCheckResult(
                decision=SyncDecision.RETRY,
                existing_hash=entry.content_hash,
                attempt_count=entry.attempt_count,
                ledger_id=entry.id,
            )

        if entry.content_hash == content_hash and entry.sync_status == "synced":
            return SyncCheckResult(
                decision=SyncDecision.SKIP,
                existing_hash=entry.content_hash,
                ledger_id=entry.id,
            )

        if entry.content_hash != content_hash:
            return SyncCheckResult(
                decision=SyncDecision.UPDATE,
                existing_hash=entry.content_hash,
                attempt_count=entry.attempt_count,
                ledger_id=entry.id,
            )

        return SyncCheckResult(
            decision=SyncDecision.SYNC,
            existing_hash=entry.content_hash,
            ledger_id=entry.id,
        )

    async def record_success(
        self,
        db: AsyncSession,
        *,
        tenant_id: uuid.UUID,
        workflow_id: uuid.UUID,
        source_connector: str,
        source_event: str,
        entity_key: str,
        content_hash: str,
        ledger_id: uuid.UUID | None = None,
    ) -> None:
        now = datetime.now(timezone.utc)

        if ledger_id:
            await db.execute(
                update(SyncLedger)
                .where(SyncLedger.id == ledger_id)
                .values(
                    content_hash=content_hash,
                    sync_status="synced",
                    synced_at=now,
                    updated_at=now,
                    last_error=None,
                )
            )
        else:
            entry = SyncLedger(
                tenant_id=tenant_id,
                workflow_id=workflow_id,
                source_connector=source_connector,
                source_event=source_event,
                entity_key=entity_key,
                content_hash=content_hash,
                sync_status="synced",
                synced_at=now,
            )
            db.add(entry)

    async def record_failure(
        self,
        db: AsyncSession,
        *,
        tenant_id: uuid.UUID,
        workflow_id: uuid.UUID,
        source_connector: str,
        source_event: str,
        entity_key: str,
        content_hash: str,
        error: str,
        ledger_id: uuid.UUID | None = None,
    ) -> None:
        now = datetime.now(timezone.utc)

        if ledger_id:
            await db.execute(
                update(SyncLedger)
                .where(SyncLedger.id == ledger_id)
                .values(
                    content_hash=content_hash,
                    sync_status="failed",
                    attempt_count=SyncLedger.attempt_count + 1,
                    last_error=error[:2000],
                    updated_at=now,
                )
            )
        else:
            entry = SyncLedger(
                tenant_id=tenant_id,
                workflow_id=workflow_id,
                source_connector=source_connector,
                source_event=source_event,
                entity_key=entity_key,
                content_hash=content_hash,
                sync_status="failed",
                attempt_count=1,
                last_error=error[:2000],
            )
            db.add(entry)

    async def mark_stale(
        self,
        db: AsyncSession,
        workflow_id: uuid.UUID,
    ) -> int:
        """Mark all synced entries as stale (used before full_sync mode)."""
        result = await db.execute(
            update(SyncLedger)
            .where(
                SyncLedger.workflow_id == workflow_id,
                SyncLedger.sync_status == "synced",
            )
            .values(sync_status="stale", updated_at=datetime.now(timezone.utc))
        )
        return result.rowcount  # type: ignore[return-value]

    async def get_stats(
        self,
        db: AsyncSession,
        workflow_id: uuid.UUID,
    ) -> dict[str, int]:
        result = await db.execute(
            select(
                SyncLedger.sync_status,
                func.count(SyncLedger.id),
            )
            .where(SyncLedger.workflow_id == workflow_id)
            .group_by(SyncLedger.sync_status)
        )
        stats: dict[str, int] = {"synced": 0, "failed": 0, "pending": 0, "stale": 0}
        for status, count in result.all():
            stats[status] = count
        stats["total"] = sum(stats.values())
        return stats

    async def get_failed_entries(
        self,
        db: AsyncSession,
        workflow_id: uuid.UUID,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        result = await db.execute(
            select(SyncLedger)
            .where(
                SyncLedger.workflow_id == workflow_id,
                SyncLedger.sync_status == "failed",
            )
            .order_by(SyncLedger.updated_at.desc())
            .limit(limit)
        )
        return [
            {
                "id": str(e.id),
                "entity_key": e.entity_key,
                "attempt_count": e.attempt_count,
                "last_error": e.last_error,
                "updated_at": e.updated_at.isoformat() if e.updated_at else None,
            }
            for e in result.scalars().all()
        ]

    async def reset_failed(
        self,
        db: AsyncSession,
        workflow_id: uuid.UUID,
    ) -> int:
        """Reset all failed entries to pending so they are retried."""
        result = await db.execute(
            update(SyncLedger)
            .where(
                SyncLedger.workflow_id == workflow_id,
                SyncLedger.sync_status == "failed",
            )
            .values(
                sync_status="pending",
                attempt_count=0,
                last_error=None,
                updated_at=datetime.now(timezone.utc),
            )
        )
        return result.rowcount  # type: ignore[return-value]

    async def clear_ledger(
        self,
        db: AsyncSession,
        workflow_id: uuid.UUID,
    ) -> int:
        """Delete all ledger entries for a workflow (force full re-sync)."""
        from sqlalchemy import delete
        result = await db.execute(
            delete(SyncLedger).where(SyncLedger.workflow_id == workflow_id)
        )
        return result.rowcount  # type: ignore[return-value]
