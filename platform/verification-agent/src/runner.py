"""Verification Runner — orchestrates a full verification run across all connectors."""

import asyncio
import logging
import time
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import httpx

from src.checks.api_version import check_api_version
from src.checks.auth import run_tier2
from src.checks.base import TIMEOUT, run_tier1
from src.checks.functional import run_tier3
from src.config import settings
from src.credential_vault import CredentialVault
from src.db import async_session_factory, set_rls_bypass
from src.discovery import VerificationTarget, discover_targets
from src.reporter import save_report, update_last_run

logger = logging.getLogger(__name__)

_lock = asyncio.Lock()


def is_running() -> bool:
    return _lock.locked()


async def run_verification(
    connector_filter: str | None = None,
    version_filter: str | None = None,
    *,
    run_id: uuid.UUID | None = None,
) -> dict[str, Any]:
    """Execute a full verification run. Returns summary.

    Uses an asyncio.Lock to prevent concurrent runs (race-free).
    If *run_id* is not provided one is generated internally (backward compat
    for scheduled runs).
    """
    if _lock.locked():
        return {"status": "already_running"}

    async with _lock:
        if run_id is None:
            run_id = uuid.uuid4()
        start = time.monotonic()
        total_reports: list[dict[str, Any]] = []

        try:
            vault: CredentialVault | None = None
            if settings.encryption_key:
                try:
                    vault = CredentialVault()
                except Exception as exc:
                    logger.warning("CredentialVault init failed: %s", exc)

            async with async_session_factory() as db:
                await set_rls_bypass(db)
                targets = await discover_targets(db)

                if connector_filter:
                    targets = [t for t in targets if t.manifest.name == connector_filter]
                if version_filter:
                    targets = [t for t in targets if t.manifest.version == version_filter]

                if not targets:
                    logger.warning("No verification targets found")
                    return {"status": "no_targets", "run_id": str(run_id)}

                for target in targets:
                    if vault and target.tenant_id:
                        try:
                            cred_names = await vault.list_credential_names(
                                db,
                                uuid.UUID(target.tenant_id),
                                target.manifest.name,
                            )
                            cred_name = cred_names[0] if cred_names else "default"
                            creds = await vault.retrieve_all(
                                db,
                                uuid.UUID(target.tenant_id),
                                target.manifest.name,
                                cred_name,
                            )
                            if creds:
                                creds["account_name"] = cred_name.replace(" ", "-")
                                target.credentials = creds
                        except Exception as exc:
                            logger.warning("Credential retrieval failed for %s: %s", target.manifest.name, exc)

                async with httpx.AsyncClient(timeout=TIMEOUT) as client:
                    for target in targets:
                        try:
                            report_data = await _verify_single(client, target)
                        except Exception as exc:
                            logger.exception(
                                "Verification aborted for connector %s v%s: %s",
                                target.manifest.name,
                                target.manifest.version,
                                exc,
                            )
                            report_data = [{"name": "runner", "status": "FAIL", "error": str(exc)}]

                        report = await save_report(
                            db,
                            run_id=run_id,
                            connector_name=target.manifest.name,
                            connector_version=target.manifest.version,
                            connector_category=target.manifest.category,
                            checks=report_data,
                            tenant_id=target.tenant_id,
                        )
                        total_reports.append(
                            {
                                "connector": f"{target.manifest.category}/{target.manifest.name}/{target.manifest.version}",
                                "status": report.status,
                                "summary": report.summary,
                            }
                        )

                next_run = datetime.now(UTC) + timedelta(days=settings.verification_interval_days)
                await update_last_run(db, next_run_at=next_run)
                await db.commit()

        except Exception as exc:
            logger.exception("Verification run failed: %s", exc)
            return {"status": "error", "run_id": str(run_id), "error": str(exc)}

    elapsed = int((time.monotonic() - start) * 1000)
    passed = sum(1 for r in total_reports if r["status"] == "PASS")
    failed = sum(1 for r in total_reports if r["status"] in ("FAIL", "PARTIAL"))
    skipped = sum(1 for r in total_reports if r["status"] == "SKIP")

    logger.info(
        "Verification run %s completed: %d connectors, %d pass, %d fail, %d skip, %dms",
        run_id,
        len(total_reports),
        passed,
        failed,
        skipped,
        elapsed,
    )

    return {
        "status": "completed",
        "run_id": str(run_id),
        "connectors_tested": len(total_reports),
        "passed": passed,
        "failed": failed,
        "skipped": skipped,
        "duration_ms": elapsed,
        "reports": total_reports,
    }


async def _verify_single(
    client: httpx.AsyncClient,
    target: VerificationTarget,
) -> list[dict[str, Any]]:
    """Run all verification tiers for a single connector."""
    logger.info("Verifying connector: %s v%s", target.manifest.name, target.manifest.version)
    checks: list[dict[str, Any]] = []

    tier1 = await run_tier1(client, target)
    checks.extend(tier1)

    version_check = await check_api_version(client, target)
    if version_check:
        checks.append(version_check)

    health_ok = any(c["name"] == "health" and c["status"] == "PASS" for c in tier1)
    if not health_ok:
        return checks

    tier2 = await run_tier2(client, target)
    checks.extend(tier2)

    auth_ok = any(c.get("status") == "PASS" for c in tier2)
    if auth_ok:
        tier3 = await run_tier3(client, target)
        checks.extend(tier3)

    return checks
