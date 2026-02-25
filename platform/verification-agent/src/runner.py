"""Verification Runner — orchestrates a full verification run across all connectors."""

import logging
import time
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx

from src.checks.api_version import check_api_version
from src.checks.base import run_tier1, TIMEOUT
from src.checks.auth import run_tier2
from src.checks.functional import run_tier3
from src.config import settings
from src.credential_vault import CredentialVault
from src.db import async_session_factory
from src.discovery import VerificationTarget, discover_targets
from src.reporter import save_report, update_last_run

logger = logging.getLogger(__name__)

_running = False


def is_running() -> bool:
    return _running


async def run_verification(
    connector_filter: str | None = None,
    version_filter: str | None = None,
) -> dict[str, Any]:
    """Execute a full verification run. Returns summary."""
    global _running
    if _running:
        return {"status": "already_running"}

    _running = True
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
                            db, uuid.UUID(target.tenant_id), target.manifest.name,
                        )
                        cred_name = cred_names[0] if cred_names else "default"
                        creds = await vault.retrieve_all(
                            db, uuid.UUID(target.tenant_id), target.manifest.name, cred_name,
                        )
                        if creds:
                            creds["account_name"] = cred_name.replace(" ", "-")
                            target.credentials = creds
                    except Exception as exc:
                        logger.warning("Credential retrieval failed for %s: %s", target.manifest.name, exc)

            async with httpx.AsyncClient(timeout=TIMEOUT) as client:
                for target in targets:
                    logger.info("Verifying connector: %s v%s", target.manifest.name, target.manifest.version)
                    checks: list[dict[str, Any]] = []

                    tier1 = await run_tier1(client, target)
                    checks.extend(tier1)

                    version_check = await check_api_version(client, target)
                    if version_check:
                        checks.append(version_check)

                    health_ok = any(c["name"] == "health" and c["status"] == "PASS" for c in tier1)

                    if health_ok:
                        tier2 = await run_tier2(client, target)
                        checks.extend(tier2)

                        auth_skipped = all(
                            c.get("status") == "SKIP" for c in tier2
                        )
                        if not auth_skipped:
                            tier3 = await run_tier3(client, target)
                            checks.extend(tier3)

                    report = await save_report(
                        db,
                        run_id=run_id,
                        connector_name=target.manifest.name,
                        connector_version=target.manifest.version,
                        connector_category=target.manifest.category,
                        checks=checks,
                        tenant_id=target.tenant_id,
                    )
                    total_reports.append({
                        "connector": f"{target.manifest.category}/{target.manifest.name}/{target.manifest.version}",
                        "status": report.status,
                        "summary": report.summary,
                    })

            next_run = datetime.now(timezone.utc) + timedelta(days=settings.verification_interval_days)
            await update_last_run(db, next_run_at=next_run)
            await db.commit()

    except Exception as exc:
        logger.exception("Verification run failed: %s", exc)
        return {"status": "error", "run_id": str(run_id), "error": str(exc)}
    finally:
        _running = False

    elapsed = int((time.monotonic() - start) * 1000)
    passed = sum(1 for r in total_reports if r["status"] == "PASS")
    failed = sum(1 for r in total_reports if r["status"] in ("FAIL", "PARTIAL"))
    skipped = sum(1 for r in total_reports if r["status"] == "SKIP")

    logger.info(
        "Verification run %s completed: %d connectors, %d pass, %d fail, %d skip, %dms",
        run_id, len(total_reports), passed, failed, skipped, elapsed,
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
