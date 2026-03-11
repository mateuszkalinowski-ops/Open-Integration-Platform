"""Real-time connector health monitoring with Redis-backed status store."""

from __future__ import annotations

import asyncio
import json
import time
from dataclasses import dataclass
from typing import Any, Callable, Awaitable

import httpx
import structlog
from prometheus_client import Gauge, Histogram

from core.connector_registry import ConnectorManifest, ConnectorRegistry

logger = structlog.get_logger()

HEALTH_STATUS = Gauge(
    "connector_health_status",
    "Connector health status (2=healthy, 1=degraded, 0=unhealthy)",
    ["name", "category"],
)
HEALTH_LATENCY = Histogram(
    "connector_health_latency_ms",
    "Health check latency in milliseconds",
    ["name"],
    buckets=[5, 10, 25, 50, 100, 250, 500, 1000],
)
HEALTH_FAILURES = Gauge(
    "connector_health_consecutive_failures",
    "Consecutive health check failures",
    ["name"],
)

_STATUS_GAUGE_VALUES = {"healthy": 2, "degraded": 1, "unhealthy": 0}
_REDIS_KEY_PREFIX = "connector:health:"


@dataclass
class ConnectorHealthStatus:
    connector_name: str
    status: str
    latency_ms: float
    last_check: float
    consecutive_failures: int
    last_error: str | None = None
    error_rate_5m: float = 0.0
    category: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "latency_ms": self.latency_ms,
            "last_check": self.last_check,
            "consecutive_failures": self.consecutive_failures,
            "last_error": self.last_error,
            "error_rate_5m": self.error_rate_5m,
            "category": self.category,
        }

    @classmethod
    def from_redis(cls, connector_name: str, data: dict[str, Any]) -> ConnectorHealthStatus:
        return cls(
            connector_name=connector_name,
            status=data.get("status", "unhealthy"),
            latency_ms=float(data.get("latency_ms", 0)),
            last_check=float(data.get("last_check", 0)),
            consecutive_failures=int(data.get("consecutive_failures", 0)),
            last_error=data.get("last_error"),
            error_rate_5m=float(data.get("error_rate_5m", 0)),
            category=data.get("category", ""),
        )


class ConnectorHealthMonitor:
    def __init__(
        self,
        registry: ConnectorRegistry,
        redis_getter: Callable[[], Awaitable[Any]],
        check_interval: int = 30,
    ) -> None:
        self._registry = registry
        self._redis_getter = redis_getter
        self._check_interval = check_interval
        self._task: asyncio.Task[None] | None = None
        self._failure_counts: dict[str, int] = {}
        self._error_timestamps: dict[str, list[float]] = {}

    async def start(self) -> None:
        if self._task is not None:
            return
        self._task = asyncio.create_task(self._poll_loop())
        logger.info("connector_health_monitor.started", interval=self._check_interval)

    async def stop(self) -> None:
        if self._task is None:
            return
        self._task.cancel()
        try:
            await self._task
        except asyncio.CancelledError:
            pass
        self._task = None
        logger.info("connector_health_monitor.stopped")

    async def _poll_loop(self) -> None:
        while True:
            try:
                await self._check_all_connectors()
            except Exception:
                logger.exception("connector_health_monitor.poll_error")
            await asyncio.sleep(self._check_interval)

    async def _check_all_connectors(self) -> None:
        connectors = self._registry.get_all()
        if not connectors:
            return
        async with httpx.AsyncClient(timeout=httpx.Timeout(5.0)) as client:
            tasks = [self._check_one(client, m) for m in connectors]
            await asyncio.gather(*tasks, return_exceptions=True)

    async def _check_one(self, client: httpx.AsyncClient, manifest: ConnectorManifest) -> None:
        name = manifest.name
        url = f"{manifest.base_url}{manifest.health_endpoint}"
        start = time.monotonic()
        now = time.time()
        status = "unhealthy"
        latency_ms = 0.0
        error_msg: str | None = None

        try:
            resp = await client.get(url)
            latency_ms = (time.monotonic() - start) * 1000
            if resp.status_code == 200:
                status = "healthy"
                self._failure_counts[name] = 0
            else:
                status = "degraded"
                self._failure_counts[name] = self._failure_counts.get(name, 0) + 1
                error_msg = f"HTTP {resp.status_code}"
        except httpx.TimeoutException:
            latency_ms = (time.monotonic() - start) * 1000
            status = "degraded"
            self._failure_counts[name] = self._failure_counts.get(name, 0) + 1
            error_msg = "Health check timed out"
        except Exception as exc:
            latency_ms = (time.monotonic() - start) * 1000
            status = "unhealthy"
            self._failure_counts[name] = self._failure_counts.get(name, 0) + 1
            error_msg = str(exc)

        if status != "healthy":
            ts_list = self._error_timestamps.setdefault(name, [])
            ts_list.append(now)

        error_rate = self._compute_error_rate_5m(name, now)
        consecutive = self._failure_counts.get(name, 0)

        health = ConnectorHealthStatus(
            connector_name=name,
            status=status,
            latency_ms=round(latency_ms, 2),
            last_check=now,
            consecutive_failures=consecutive,
            last_error=error_msg,
            error_rate_5m=round(error_rate, 4),
            category=manifest.category,
        )

        await self._store_status(name, health)

        HEALTH_STATUS.labels(name=name, category=manifest.category).set(
            _STATUS_GAUGE_VALUES.get(status, 0)
        )
        HEALTH_LATENCY.labels(name=name).observe(latency_ms)
        HEALTH_FAILURES.labels(name=name).set(consecutive)

        logger.debug(
            "connector_health_check",
            connector=name,
            status=status,
            latency_ms=round(latency_ms, 2),
            consecutive_failures=consecutive,
        )

    def _compute_error_rate_5m(self, name: str, now: float) -> float:
        ts_list = self._error_timestamps.get(name, [])
        cutoff = now - 300
        ts_list[:] = [t for t in ts_list if t > cutoff]
        expected_checks = max(1, 300 / self._check_interval)
        return len(ts_list) / expected_checks

    async def _store_status(self, name: str, health: ConnectorHealthStatus) -> None:
        redis = await self._redis_getter()
        key = f"{_REDIS_KEY_PREFIX}{name}"
        ttl = self._check_interval * 4
        await redis.set(key, json.dumps(health.to_dict()), ex=ttl)

    async def get_status(self, connector_name: str) -> ConnectorHealthStatus | None:
        redis = await self._redis_getter()
        key = f"{_REDIS_KEY_PREFIX}{connector_name}"
        raw = await redis.get(key)
        if raw is None:
            return None
        try:
            data = json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            return None
        return ConnectorHealthStatus.from_redis(connector_name, data)

    async def get_all_statuses(self) -> list[ConnectorHealthStatus]:
        redis = await self._redis_getter()
        statuses: list[ConnectorHealthStatus] = []
        cursor: int | bytes = 0
        while True:
            cursor, keys = await redis.scan(cursor=cursor, match=f"{_REDIS_KEY_PREFIX}*", count=100)
            if keys:
                values = await redis.mget(*keys)
                for key, raw in zip(keys, values):
                    if raw is None:
                        continue
                    try:
                        data = json.loads(raw)
                    except (json.JSONDecodeError, TypeError):
                        continue
                    name = key.removeprefix(_REDIS_KEY_PREFIX)
                    statuses.append(ConnectorHealthStatus.from_redis(name, data))
            if cursor == 0:
                break
        return statuses
