"""Reporter — writes verification results to the database."""

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.db import VerificationReport, VerificationSettings, async_session_factory


async def save_report(
    db: AsyncSession,
    run_id: uuid.UUID,
    connector_name: str,
    connector_version: str,
    connector_category: str,
    checks: list[dict[str, Any]],
    tenant_id: str | None = None,
) -> VerificationReport:
    passed = sum(1 for c in checks if c["status"] == "PASS")
    failed = sum(1 for c in checks if c["status"] == "FAIL")
    skipped = sum(1 for c in checks if c["status"] == "SKIP")
    warned = sum(1 for c in checks if c["status"] == "WARN")
    total_ms = sum(c.get("response_time_ms", 0) for c in checks)

    status = "PASS"
    if failed > 0 and passed > 0:
        status = "PARTIAL"
    elif failed > 0:
        status = "FAIL"
    elif skipped == len(checks):
        status = "SKIP"
    elif warned > 0:
        status = "WARN"

    report = VerificationReport(
        run_id=run_id,
        connector_name=connector_name,
        connector_version=connector_version,
        connector_category=connector_category,
        tenant_id=uuid.UUID(tenant_id) if tenant_id else None,
        status=status,
        checks=checks,
        summary={
            "total": len(checks),
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
            "warned": warned,
            "duration_ms": total_ms,
        },
    )
    db.add(report)
    await db.flush()
    return report


async def update_last_run(db: AsyncSession, next_run_at: datetime | None = None) -> None:
    """Update the verification_settings singleton with last run timestamp."""
    result = await db.execute(select(VerificationSettings))
    row = result.scalar_one_or_none()

    now = datetime.now(timezone.utc)
    if row:
        row.last_run_at = now
        if next_run_at:
            row.next_run_at = next_run_at
        row.updated_at = now
    else:
        db.add(VerificationSettings(
            enabled=True,
            interval_days=7,
            last_run_at=now,
            next_run_at=next_run_at,
        ))
    await db.flush()


async def get_settings() -> VerificationSettings | None:
    async with async_session_factory() as db:
        result = await db.execute(select(VerificationSettings))
        return result.scalar_one_or_none()


async def ensure_settings(db: AsyncSession) -> VerificationSettings:
    result = await db.execute(select(VerificationSettings))
    row = result.scalar_one_or_none()
    if not row:
        row = VerificationSettings(enabled=True, interval_days=7)
        db.add(row)
        await db.flush()
    return row
