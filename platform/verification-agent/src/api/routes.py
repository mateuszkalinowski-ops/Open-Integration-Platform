"""Verification Agent API routes."""

import asyncio
import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import desc, func, select

from src.db import VerificationReport, async_session_factory
from src.reporter import ensure_settings
from src.runner import is_running, run_verification

router = APIRouter()


class SchedulerUpdate(BaseModel):
    enabled: bool | None = None
    interval_days: int | None = None


class RunResponse(BaseModel):
    run_id: str
    status: str


class SchedulerStatusResponse(BaseModel):
    enabled: bool
    interval_days: int
    last_run: str | None
    next_run: str | None
    currently_running: bool


@router.post("/run", response_model=RunResponse)
async def trigger_run() -> RunResponse:
    """Trigger an on-demand full verification run."""
    if is_running():
        raise HTTPException(status_code=409, detail="A verification run is already in progress")
    rid = uuid.uuid4()
    asyncio.create_task(run_verification(run_id=rid))
    return RunResponse(run_id=str(rid), status="started")


@router.post("/run/{connector_name}", response_model=RunResponse)
async def trigger_single_run(
    connector_name: str,
    version: str | None = Query(None, description="Specific version to test"),
) -> RunResponse:
    """Trigger verification for a single connector (optionally a specific version)."""
    if is_running():
        raise HTTPException(status_code=409, detail="A verification run is already in progress")
    rid = uuid.uuid4()
    asyncio.create_task(
        run_verification(connector_filter=connector_name, version_filter=version, run_id=rid)
    )
    return RunResponse(run_id=str(rid), status="started")


@router.get("/scheduler/status", response_model=SchedulerStatusResponse)
async def get_scheduler_status() -> SchedulerStatusResponse:
    async with async_session_factory() as db:
        settings_row = await ensure_settings(db)
        await db.commit()
        return SchedulerStatusResponse(
            enabled=settings_row.enabled,
            interval_days=settings_row.interval_days,
            last_run=settings_row.last_run_at.isoformat() if settings_row.last_run_at else None,
            next_run=settings_row.next_run_at.isoformat() if settings_row.next_run_at else None,
            currently_running=is_running(),
        )


@router.put("/scheduler")
async def update_scheduler(body: SchedulerUpdate) -> dict[str, Any]:
    """Update scheduler configuration."""
    async with async_session_factory() as db:
        row = await ensure_settings(db)
        if body.enabled is not None:
            row.enabled = body.enabled
        if body.interval_days is not None:
            if body.interval_days < 1:
                raise HTTPException(status_code=400, detail="interval_days must be >= 1")
            row.interval_days = body.interval_days
        await db.commit()

        if body.interval_days is not None:
            from src.main import reschedule
            reschedule(row.interval_days)

        return {
            "enabled": row.enabled,
            "interval_days": row.interval_days,
            "last_run": row.last_run_at.isoformat() if row.last_run_at else None,
            "next_run": row.next_run_at.isoformat() if row.next_run_at else None,
        }


@router.get("/runs")
async def list_runs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> dict[str, Any]:
    """List past verification runs with summaries."""
    async with async_session_factory() as db:
        count_q = select(func.count(func.distinct(VerificationReport.run_id)))
        total_result = await db.execute(count_q)
        total = total_result.scalar() or 0

        subq = (
            select(VerificationReport.run_id)
            .group_by(VerificationReport.run_id)
            .order_by(desc(func.min(VerificationReport.created_at)))
            .offset((page - 1) * page_size)
            .limit(page_size)
        ).subquery()

        q = (
            select(VerificationReport)
            .where(VerificationReport.run_id.in_(select(subq.c.run_id)))
            .order_by(desc(VerificationReport.created_at))
        )
        result = await db.execute(q)
        reports = result.scalars().all()

        runs: dict[str, dict[str, Any]] = {}
        for r in reports:
            rid = str(r.run_id)
            if rid not in runs:
                runs[rid] = {
                    "run_id": rid,
                    "created_at": r.created_at.isoformat(),
                    "total": 0, "passed": 0, "failed": 0, "skipped": 0,
                    "duration_ms": 0, "connectors": [],
                }
            run = runs[rid]
            run["total"] += 1
            s = r.summary or {}
            run["passed"] += s.get("passed", 0)
            run["failed"] += s.get("failed", 0)
            run["skipped"] += s.get("skipped", 0)
            run["duration_ms"] += s.get("duration_ms", 0)
            run["connectors"].append({
                "connector_name": r.connector_name,
                "connector_version": r.connector_version,
                "connector_category": r.connector_category,
                "status": r.status,
                "summary": r.summary,
                "created_at": r.created_at.isoformat(),
            })

        return {"total": total, "page": page, "page_size": page_size, "runs": list(runs.values())}


@router.get("/runs/{run_id}")
async def get_run(run_id: str) -> dict[str, Any]:
    """Get detailed results for a specific verification run."""
    try:
        rid = uuid.UUID(run_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid run_id format") from exc

    async with async_session_factory() as db:
        q = (
            select(VerificationReport)
            .where(VerificationReport.run_id == rid)
            .order_by(VerificationReport.connector_name)
        )
        result = await db.execute(q)
        reports = result.scalars().all()

        if not reports:
            raise HTTPException(status_code=404, detail="Run not found")

        connectors = []
        total_passed = total_failed = total_skipped = total_duration = 0
        for r in reports:
            s = r.summary or {}
            total_passed += s.get("passed", 0)
            total_failed += s.get("failed", 0)
            total_skipped += s.get("skipped", 0)
            total_duration += s.get("duration_ms", 0)
            connectors.append({
                "id": str(r.id),
                "connector_name": r.connector_name,
                "connector_version": r.connector_version,
                "connector_category": r.connector_category,
                "status": r.status,
                "checks": r.checks,
                "summary": r.summary,
                "created_at": r.created_at.isoformat(),
            })

        return {
            "run_id": run_id,
            "created_at": reports[0].created_at.isoformat(),
            "connectors_tested": len(connectors),
            "total_passed": total_passed,
            "total_failed": total_failed,
            "total_skipped": total_skipped,
            "total_duration_ms": total_duration,
            "connectors": connectors,
        }


@router.get("/errors")
async def list_errors(
    connector_name: str | None = Query(None),
    date_from: str | None = Query(None),
    date_to: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
) -> dict[str, Any]:
    """List all FAIL checks across all runs, filterable.

    Pagination is applied at the report level in SQL, then FAIL checks
    are extracted in Python.  This avoids loading all historical reports
    into memory.
    """
    async with async_session_factory() as db:
        q = select(VerificationReport).where(VerificationReport.status.in_(["FAIL", "PARTIAL"]))

        if connector_name:
            q = q.where(VerificationReport.connector_name == connector_name)
        if date_from:
            q = q.where(VerificationReport.created_at >= datetime.fromisoformat(date_from))
        if date_to:
            q = q.where(VerificationReport.created_at <= datetime.fromisoformat(date_to))

        count_q = select(func.count()).select_from(q.subquery())
        total_reports = (await db.execute(count_q)).scalar() or 0

        q = q.order_by(desc(VerificationReport.created_at))
        q = q.offset((page - 1) * page_size).limit(page_size)

        result = await db.execute(q)
        reports = result.scalars().all()

        errors: list[dict[str, Any]] = []
        for report in reports:
            for check in (report.checks or []):
                if check.get("status") == "FAIL":
                    errors.append({
                        "connector_name": report.connector_name,
                        "connector_version": report.connector_version,
                        "connector_category": report.connector_category,
                        "check_name": check["name"],
                        "error": check.get("error", ""),
                        "suggestion": check.get("suggestion"),
                        "response_time_ms": check.get("response_time_ms", 0),
                        "run_id": str(report.run_id),
                        "created_at": report.created_at.isoformat(),
                    })

        return {"total_reports": total_reports, "page": page, "page_size": page_size, "errors": errors}


@router.get("/reports/latest")
async def latest_reports() -> dict[str, Any]:
    """Get the latest verification status for every active connector version.

    Connectors discovered from current manifests are always included, even if
    they have never been verified yet. In that case, a synthetic ``NOT_RUN``
    row is returned so the dashboard can display the connector before its
    first verification report exists.
    """
    from src.discovery import discover_manifests

    manifests = discover_manifests()
    active_versions: dict[tuple[str, str], Any] = {}
    for m in manifests:
        active_versions[(m.name, m.version)] = m

    async with async_session_factory() as db:
        latest_per_connector = (
            select(
                VerificationReport.connector_name,
                VerificationReport.connector_version,
                func.max(VerificationReport.created_at).label("max_created"),
            )
            .group_by(VerificationReport.connector_name, VerificationReport.connector_version)
            .subquery()
        )

        q = (
            select(VerificationReport)
            .join(
                latest_per_connector,
                (VerificationReport.connector_name == latest_per_connector.c.connector_name)
                & (VerificationReport.connector_version == latest_per_connector.c.connector_version)
                & (VerificationReport.created_at == latest_per_connector.c.max_created),
            )
            .order_by(VerificationReport.connector_name, VerificationReport.connector_version)
        )
        result = await db.execute(q)
        reports = result.scalars().all()

        report_map: dict[tuple[str, str], VerificationReport] = {}
        for report in reports:
            key = (report.connector_name, report.connector_version)
            if key in active_versions and key not in report_map:
                report_map[key] = report

        most_recent = max(report_map.values(), key=lambda r: r.created_at) if report_map else None

        connectors = []
        for key in sorted(active_versions):
            manifest = active_versions[key]
            report = report_map.get(key)
            if report:
                connectors.append({
                    "connector_name": report.connector_name,
                    "connector_version": report.connector_version,
                    "connector_category": report.connector_category,
                    "status": report.status,
                    "checks": report.checks,
                    "summary": report.summary,
                    "created_at": report.created_at.isoformat(),
                })
                continue

            connectors.append({
                "connector_name": manifest.name,
                "connector_version": manifest.version,
                "connector_category": manifest.category,
                "status": "NOT_RUN",
                "checks": [],
                "summary": {
                    "total": 0,
                    "passed": 0,
                    "failed": 0,
                    "skipped": 0,
                    "warned": 0,
                    "duration_ms": 0,
                },
                "created_at": None,
            })

        return {
            "run_id": str(most_recent.run_id) if most_recent else None,
            "created_at": most_recent.created_at.isoformat() if most_recent else None,
            "connectors": connectors,
        }
