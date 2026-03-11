"""Auto-generated health and readiness routes for connector FastAPI apps."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any

from fastapi import FastAPI
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from pinquark_connector_sdk.app import ConnectorApp


class HealthResponse(BaseModel):
    status: str
    version: str
    uptime_seconds: float
    connector: str


class ReadinessResponse(BaseModel):
    status: str
    version: str
    checks: dict[str, str] = Field(default_factory=dict)


class _HealthState:
    def __init__(self, connector_app: ConnectorApp) -> None:
        self._connector_app = connector_app
        self._start_time = time.monotonic()
        self._readiness_checks: dict[str, Any] = {}

    def register_check(self, name: str, check_fn: Any) -> None:
        self._readiness_checks[name] = check_fn

    def uptime(self) -> float:
        return round(time.monotonic() - self._start_time, 1)

    async def liveness(self) -> HealthResponse:
        return HealthResponse(
            status="healthy",
            version=self._connector_app.version,
            uptime_seconds=self.uptime(),
            connector=self._connector_app.name,
        )

    async def readiness(self) -> ReadinessResponse:
        results: dict[str, str] = {}
        all_ok = True

        for name, check_fn in self._readiness_checks.items():
            try:
                await check_fn()
                results[name] = "ok"
            except Exception as exc:
                results[name] = f"error: {exc}"
                all_ok = False

        return ReadinessResponse(
            status="ready" if all_ok else "not_ready",
            version=self._connector_app.version,
            checks=results,
        )


def register_health_routes(app: FastAPI, connector_app: ConnectorApp) -> _HealthState:
    """Add /health and /readiness endpoints to the FastAPI app.

    Returns the HealthState instance so callers can register additional
    readiness checks via ``state.register_check(name, async_fn)``.
    """
    state = _HealthState(connector_app)

    @app.get("/health", response_model=HealthResponse, tags=["health"])
    async def health() -> HealthResponse:
        return await state.liveness()

    @app.get("/readiness", response_model=ReadinessResponse, tags=["health"])
    async def readiness() -> ReadinessResponse:
        return await state.readiness()

    return state
