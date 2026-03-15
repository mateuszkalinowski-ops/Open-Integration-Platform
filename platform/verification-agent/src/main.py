"""Verification Agent — FastAPI application with APScheduler."""

import logging
from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta
from typing import Any

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI
from prometheus_client import CONTENT_TYPE_LATEST, Counter, generate_latest
from sqlalchemy import text
from starlette.responses import Response as StarletteResponse

from src.api.routes import router
from src.config import settings
from src.db import async_session_factory
from src.reporter import ensure_settings, get_settings
from src.runner import is_running, run_verification

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


async def _scheduled_run() -> None:
    """Called by APScheduler on each tick."""
    srow = await get_settings()
    if srow and not srow.enabled:
        logger.info("Scheduler is disabled — skipping run")
        return
    if is_running():
        logger.warning("Scheduled run skipped — a verification run is already in progress")
        return
    logger.info("Scheduled verification run starting")
    await run_verification()


def reschedule(interval_days: int) -> None:
    """Reschedule the live APScheduler job with a new interval."""
    scheduler.reschedule_job(
        "verification_run",
        trigger="interval",
        days=interval_days,
    )
    logger.info("Scheduler rescheduled — new interval=%d days", interval_days)


async def _init_scheduler() -> None:
    """Initialise APScheduler from DB settings or defaults."""
    async with async_session_factory() as db:
        srow = await ensure_settings(db)
        await db.commit()
        interval_days = srow.interval_days

    scheduler.add_job(
        _scheduled_run,
        "interval",
        days=interval_days,
        id="verification_run",
        replace_existing=True,
        next_run_time=datetime.now(UTC) + timedelta(minutes=1),
    )
    scheduler.start()
    logger.info("Scheduler started — interval=%d days", interval_days)


@asynccontextmanager
async def lifespan(app: FastAPI):  # type: ignore[no-untyped-def]
    await _init_scheduler()
    yield
    scheduler.shutdown(wait=False)


app = FastAPI(
    title="Verification Agent",
    version=settings.app_version,
    lifespan=lifespan,
)

app.include_router(router, prefix="")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "healthy", "service": settings.app_name, "version": settings.app_version}


VERIFICATION_RUNS_TOTAL = Counter(
    "verification_runs_total",
    "Total verification runs",
    ["status"],
)


@app.get("/metrics")
async def metrics() -> StarletteResponse:
    return StarletteResponse(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/readiness")
async def readiness() -> dict[str, Any]:
    db_ok = True
    try:
        async with async_session_factory() as db:
            await db.execute(text("SELECT 1"))
    except Exception:
        db_ok = False
    status = "ready" if db_ok else "degraded"
    return {"status": status, "checks": {"database": "ok" if db_ok else "error"}}
