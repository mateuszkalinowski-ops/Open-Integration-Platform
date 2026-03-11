"""Auto-generated health and readiness routes for connector FastAPI apps.

/health  — liveness probe: checks whether the connector can reach its
           upstream API by calling ``test_connection()``.  Returns
           "healthy" or "degraded" (never crashes the probe).
/readiness — readiness probe: runs all registered readiness checks,
             including ``test_connection()`` if the subclass overrides it.
"""

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
    checks: dict[str, str] = Field(default_factory=dict)


class ReadinessResponse(BaseModel):
    status: str
    version: str
    checks: dict[str, str] = Field(default_factory=dict)


class _HealthState:
    def __init__(self, connector_app: ConnectorApp) -> None:
        self._connector_app = connector_app
        self._start_time = time.monotonic()
        self._readiness_checks: dict[str, Any] = {}
        self._has_test_connection = self._detect_test_connection()

    def _detect_test_connection(self) -> bool:
        """Check whether the subclass provides a real ``test_connection``."""
        method = getattr(type(self._connector_app), "test_connection", None)
        if method is None:
            return False
        from pinquark_connector_sdk.app import ConnectorApp as _Base
        return method is not getattr(_Base, "test_connection", None)

    def register_check(self, name: str, check_fn: Any) -> None:
        self._readiness_checks[name] = check_fn

    def uptime(self) -> float:
        return round(time.monotonic() - self._start_time, 1)

    async def liveness(self) -> HealthResponse:
        status = "healthy"
        checks: dict[str, str] = {}

        if self._has_test_connection:
            try:
                ok = await self._connector_app.test_connection()
                if ok:
                    checks["upstream_api"] = "ok"
                else:
                    checks["upstream_api"] = "unreachable"
                    status = "degraded"
            except Exception as exc:
                checks["upstream_api"] = f"error: {exc}"
                status = "degraded"

        return HealthResponse(
            status=status,
            version=self._connector_app.version,
            uptime_seconds=self.uptime(),
            connector=self._connector_app.name,
            checks=checks,
        )

    async def readiness(self) -> ReadinessResponse:
        results: dict[str, str] = {}
        all_ok = True

        if self._has_test_connection and "upstream_api" not in self._readiness_checks:
            try:
                ok = await self._connector_app.test_connection()
                results["upstream_api"] = "ok" if ok else "unreachable"
                if not ok:
                    all_ok = False
            except Exception as exc:
                results["upstream_api"] = f"error: {exc}"
                all_ok = False

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

    If the connector subclass overrides ``test_connection()``, it is
    automatically used as both a liveness and readiness check.
    """
    state = _HealthState(connector_app)

    @app.get("/health", response_model=HealthResponse, tags=["health"])
    async def health() -> HealthResponse:
        return await state.liveness()

    @app.get("/readiness", response_model=ReadinessResponse, tags=["health"])
    async def readiness() -> ReadinessResponse:
        return await state.readiness()

    return state
