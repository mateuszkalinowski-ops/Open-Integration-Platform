"""Real-time connector health monitoring with Redis-backed status store.

Checks only active ConnectorInstance rows (not all manifests from the
registry). Each instance is tracked independently so multi-tenant or
multi-version deployments never cross-contaminate failure counts.
Auto-disables instances after ``auto_disable_threshold`` consecutive
health-check failures.
"""

from __future__ import annotations

import asyncio
import contextlib
import json
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

import httpx
import structlog
from prometheus_client import Gauge, Histogram
from sqlalchemy import select, update

from core.connector_registry import ConnectorManifest, ConnectorRegistry

logger = structlog.get_logger()

HEALTH_STATUS = Gauge(
    "connector_health_status",
    "Connector health status (2=healthy, 1=degraded, 0=unhealthy)",
    ["instance_key", "name", "category"],
)
HEALTH_LATENCY = Histogram(
    "connector_health_latency_ms",
    "Health check latency in milliseconds",
    ["instance_key"],
    buckets=[5, 10, 25, 50, 100, 250, 500, 1000],
)
HEALTH_FAILURES = Gauge(
    "connector_health_consecutive_failures",
    "Consecutive health check failures",
    ["instance_key"],
)

_STATUS_GAUGE_VALUES = {"healthy": 2, "degraded": 1, "unhealthy": 0}
_REDIS_KEY_PREFIX = "connector:health:"


@dataclass
class _HealthTarget:
    """Everything needed to check one connector instance."""

    manifest: ConnectorManifest
    instance_id: Any = None
    instance_key: str = ""

    def __post_init__(self) -> None:
        if not self.instance_key:
            self.instance_key = str(self.instance_id) if self.instance_id else self.manifest.name


@dataclass
class ConnectorHealthStatus:
    connector_name: str
    instance_key: str
    status: str
    latency_ms: float
    last_check: float
    consecutive_failures: int
    last_error: str | None = None
    error_rate_5m: float = 0.0
    category: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "connector_name": self.connector_name,
            "instance_key": self.instance_key,
            "status": self.status,
            "latency_ms": self.latency_ms,
            "last_check": self.last_check,
            "consecutive_failures": self.consecutive_failures,
            "last_error": self.last_error,
            "error_rate_5m": self.error_rate_5m,
            "category": self.category,
        }

    @classmethod
    def from_redis(cls, key: str, data: dict[str, Any]) -> ConnectorHealthStatus:
        return cls(
            connector_name=data.get("connector_name", key),
            instance_key=data.get("instance_key", key),
            status=data.get("status", "unhealthy"),
            latency_ms=float(data.get("latency_ms", 0)),
            last_check=float(data.get("last_check", 0)),
            consecutive_failures=int(data.get("consecutive_failures", 0)),
            last_error=data.get("last_error"),
            error_rate_5m=float(data.get("error_rate_5m", 0)),
            category=data.get("category", ""),
        )


class ConnectorHealthMonitor:
    """Polls active ConnectorInstance rows and auto-disables after repeated failures.

    Every piece of state (failure counts, error timestamps, Redis keys,
    Prometheus labels) is keyed by *instance_id* — not connector name —
    so multiple instances of the same connector type are fully isolated.
    """

    def __init__(
        self,
        registry: ConnectorRegistry,
        redis_getter: Callable[[], Awaitable[Any]],
        session_factory: Any = None,
        check_interval: int = 30,
        request_timeout: float = 5.0,
        auto_disable_threshold: int = 5,
    ) -> None:
        self._registry = registry
        self._redis_getter = redis_getter
        self._session_factory = session_factory
        self._check_interval = check_interval
        self._request_timeout = request_timeout
        self._auto_disable_threshold = auto_disable_threshold
        self._task: asyncio.Task[None] | None = None
        self._failure_counts: dict[str, int] = {}
        self._error_timestamps: dict[str, list[float]] = {}

    async def start(self) -> None:
        if self._task is not None:
            return
        self._task = asyncio.create_task(self._poll_loop())
        logger.info(
            "connector_health_monitor.started",
            interval=self._check_interval,
            request_timeout=self._request_timeout,
            auto_disable_threshold=self._auto_disable_threshold,
        )

    async def stop(self) -> None:
        if self._task is None:
            return
        self._task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await self._task
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
        targets = await self._get_active_targets()
        if not targets:
            return
        async with httpx.AsyncClient(timeout=httpx.Timeout(self._request_timeout)) as client:
            tasks = [self._check_one(client, t) for t in targets]
            await asyncio.gather(*tasks, return_exceptions=True)

    async def _get_active_targets(self) -> list[_HealthTarget]:
        if self._session_factory is None:
            return [_HealthTarget(manifest=m) for m in self._registry.get_all()]

        from db.base import set_rls_bypass
        from db.models import ConnectorInstance

        targets: list[_HealthTarget] = []
        async with self._session_factory() as db:
            await set_rls_bypass(db)
            result = await db.execute(select(ConnectorInstance).where(ConnectorInstance.is_enabled.is_(True)))
            instances = result.scalars().all()
            for inst in instances:
                manifest = self._registry.get_by_name_version(
                    inst.connector_name,
                    inst.connector_version,
                )
                if not manifest:
                    fallbacks = self._registry.get_by_name(inst.connector_name)
                    manifest = fallbacks[0] if fallbacks else None
                if manifest:
                    targets.append(
                        _HealthTarget(
                            manifest=manifest,
                            instance_id=inst.id,
                            instance_key=str(inst.id),
                        )
                    )
        return targets

    async def _check_one(self, client: httpx.AsyncClient, target: _HealthTarget) -> None:
        ikey = target.instance_key
        manifest = target.manifest
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
                self._failure_counts[ikey] = 0
            else:
                status = "degraded"
                self._failure_counts[ikey] = self._failure_counts.get(ikey, 0) + 1
                error_msg = f"HTTP {resp.status_code}"
        except httpx.TimeoutException:
            latency_ms = (time.monotonic() - start) * 1000
            status = "degraded"
            self._failure_counts[ikey] = self._failure_counts.get(ikey, 0) + 1
            error_msg = "Health check timed out"
        except Exception as exc:
            latency_ms = (time.monotonic() - start) * 1000
            status = "unhealthy"
            self._failure_counts[ikey] = self._failure_counts.get(ikey, 0) + 1
            error_msg = str(exc)

        if status != "healthy":
            ts_list = self._error_timestamps.setdefault(ikey, [])
            ts_list.append(now)

        error_rate = self._compute_error_rate_5m(ikey, now)
        consecutive = self._failure_counts.get(ikey, 0)

        if consecutive >= self._auto_disable_threshold and target.instance_id is not None:
            await self._auto_disable_instance(target.instance_id, ikey, name, consecutive)

        health = ConnectorHealthStatus(
            connector_name=name,
            instance_key=ikey,
            status=status,
            latency_ms=round(latency_ms, 2),
            last_check=now,
            consecutive_failures=consecutive,
            last_error=error_msg,
            error_rate_5m=round(error_rate, 4),
            category=manifest.category,
        )

        await self._store_status(ikey, health)

        HEALTH_STATUS.labels(instance_key=ikey, name=name, category=manifest.category).set(
            _STATUS_GAUGE_VALUES.get(status, 0)
        )
        HEALTH_LATENCY.labels(instance_key=ikey).observe(latency_ms)
        HEALTH_FAILURES.labels(instance_key=ikey).set(consecutive)

        logger.debug(
            "connector_health_check",
            connector=name,
            instance_key=ikey,
            status=status,
            latency_ms=round(latency_ms, 2),
            consecutive_failures=consecutive,
        )

    async def _auto_disable_instance(
        self,
        instance_id: Any,
        ikey: str,
        connector_name: str,
        consecutive: int,
    ) -> None:
        if self._session_factory is None:
            return
        try:
            from db.base import set_rls_bypass
            from db.models import ConnectorInstance

            async with self._session_factory() as db:
                await set_rls_bypass(db)
                await db.execute(
                    update(ConnectorInstance).where(ConnectorInstance.id == instance_id).values(is_enabled=False)
                )
                await db.commit()
            self._failure_counts[ikey] = 0
            logger.warning(
                "connector_health_auto_disabled",
                connector=connector_name,
                instance_id=str(instance_id),
                consecutive_failures=consecutive,
            )
        except Exception:
            logger.exception(
                "connector_health_auto_disable_failed",
                connector=connector_name,
                instance_id=str(instance_id),
            )

    def _compute_error_rate_5m(self, key: str, now: float) -> float:
        ts_list = self._error_timestamps.get(key, [])
        cutoff = now - 300
        ts_list[:] = [t for t in ts_list if t > cutoff]
        expected_checks = max(1, 300 / self._check_interval)
        return len(ts_list) / expected_checks

    async def _store_status(self, key: str, health: ConnectorHealthStatus) -> None:
        redis = await self._redis_getter()
        redis_key = f"{_REDIS_KEY_PREFIX}{key}"
        ttl = self._check_interval * 4
        await redis.set(redis_key, json.dumps(health.to_dict()), ex=ttl)

    async def get_statuses_by_name(self, connector_name: str) -> list[ConnectorHealthStatus]:
        """Get health statuses for all instances of a given connector name."""
        all_statuses = await self.get_all_statuses()
        return [s for s in all_statuses if s.connector_name == connector_name]

    async def get_status_by_instance(self, instance_key: str) -> ConnectorHealthStatus | None:
        """Get health status for a specific instance by its key."""
        redis = await self._redis_getter()
        raw = await redis.get(f"{_REDIS_KEY_PREFIX}{instance_key}")
        if raw is None:
            return None
        try:
            data = json.loads(raw)
            return ConnectorHealthStatus.from_redis(instance_key, data)
        except (json.JSONDecodeError, TypeError):
            return None

    async def get_all_statuses(self) -> list[ConnectorHealthStatus]:
        redis = await self._redis_getter()
        statuses: list[ConnectorHealthStatus] = []
        cursor: int | bytes = 0
        while True:
            cursor, keys = await redis.scan(cursor=cursor, match=f"{_REDIS_KEY_PREFIX}*", count=100)
            if keys:
                values = await redis.mget(*keys)
                for key, raw in zip(keys, values, strict=False):
                    if raw is None:
                        continue
                    try:
                        data = json.loads(raw)
                    except (json.JSONDecodeError, TypeError):
                        continue
                    short_key = key.removeprefix(_REDIS_KEY_PREFIX)
                    statuses.append(ConnectorHealthStatus.from_redis(short_key, data))
            if cursor == 0:
                break
        return statuses
