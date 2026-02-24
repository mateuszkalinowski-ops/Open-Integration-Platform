"""Verification Agent — FastAPI application with APScheduler."""

import logging
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI

from src.api.routes import router
from src.config import settings
from src.reporter import ensure_settings, get_settings
from src.runner import run_verification
from src.db import async_session_factory

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
    logger.info("Scheduled verification run starting")
    await run_verification()


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
        next_run_time=datetime.now(timezone.utc) + timedelta(minutes=1),
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


@app.get("/readiness")
async def readiness() -> dict[str, str]:
    return {"status": "ready"}
