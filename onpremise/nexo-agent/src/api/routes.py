"""Main router — health, readiness, and sub-router mounting."""

import time
from typing import Any

from fastapi import APIRouter, HTTPException

from src.api.dependencies import app_state
from src.api.contractors import router as contractors_router
from src.api.products import router as products_router
from src.api.documents import router as documents_router
from src.api.orders import router as orders_router
from src.api.stock import router as stock_router
from src.config import settings

router = APIRouter()

_start_time = time.monotonic()

router.include_router(contractors_router, prefix="/contractors", tags=["Contractors"])
router.include_router(products_router, prefix="/products", tags=["Products"])
router.include_router(documents_router, prefix="/documents", tags=["Documents"])
router.include_router(orders_router, prefix="/orders", tags=["Orders"])
router.include_router(stock_router, prefix="/stock", tags=["Stock"])


@router.get("/health", tags=["System"])
async def health() -> dict[str, Any]:
    conn_status = "disconnected"
    if app_state.connection_pool:
        try:
            conn = app_state.connection_pool.connection
            conn_status = conn.status.value
        except Exception:
            conn_status = "error"

    return {
        "status": "healthy" if conn_status == "connected" else "degraded",
        "version": settings.app_version,
        "uptime_seconds": round(time.monotonic() - _start_time, 1),
        "checks": {
            "nexo_connection": conn_status,
        },
    }


@router.get("/readiness", tags=["System"])
async def readiness() -> dict[str, Any]:
    if not app_state.connection_pool:
        raise HTTPException(status_code=503, detail={"status": "not_ready", "error": "Connection pool not initialized"})

    try:
        conn = app_state.connection_pool.ensure_connected()
        ping_result = conn.ping()
    except Exception as exc:
        raise HTTPException(status_code=503, detail={"status": "not_ready", "error": str(exc)})

    if ping_result.get("status") != "ok":
        raise HTTPException(status_code=503, detail={"status": "not_ready", "nexo_ping": ping_result})

    return {
        "status": "ready",
        "version": settings.app_version,
        "nexo_ping": ping_result,
    }


@router.get("/connection/status", tags=["System"])
async def connection_status() -> dict[str, Any]:
    if not app_state.connection_pool:
        return {"connected": False, "status": "not_initialized"}

    conn = app_state.connection_pool._connection
    result: dict[str, Any] = {
        "connected": conn.is_connected,
        "status": conn.status.value,
        "consecutive_failures": conn.consecutive_failures,
    }

    if conn.is_connected:
        result["ping"] = conn.ping()

    return result


@router.post("/connection/reconnect", tags=["System"])
async def reconnect() -> dict[str, Any]:
    if not app_state.connection_pool:
        raise HTTPException(status_code=503, detail="Connection pool not initialized")

    try:
        app_state.connection_pool.connection.reconnect()
        return {"status": "reconnected"}
    except Exception as exc:
        raise HTTPException(status_code=503, detail={"status": "failed", "error": str(exc)})
