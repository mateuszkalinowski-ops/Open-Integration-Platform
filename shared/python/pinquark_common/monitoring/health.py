"""Health check utilities for integrators."""

import time
from typing import Any

from pinquark_common.schemas.common import HealthResponse


class HealthChecker:
    def __init__(self, version: str):
        self._version = version
        self._start_time = time.monotonic()
        self._checks: dict[str, Any] = {}

    def register_check(self, name: str, check_fn: Any) -> None:
        self._checks[name] = check_fn

    async def run(self) -> HealthResponse:
        results: dict[str, str] = {}
        overall_healthy = True

        for name, check_fn in self._checks.items():
            try:
                await check_fn()
                results[name] = "ok"
            except Exception as exc:
                results[name] = f"error: {exc}"
                overall_healthy = False

        return HealthResponse(
            status="healthy" if overall_healthy else "unhealthy",
            version=self._version,
            uptime_seconds=round(time.monotonic() - self._start_time, 1),
            checks=results,
        )
