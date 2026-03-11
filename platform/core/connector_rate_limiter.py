"""Per-connector token bucket rate limiter backed by Redis."""

from __future__ import annotations

import asyncio
import re
import time
from dataclasses import dataclass
from typing import Any, Callable, Awaitable

import structlog

from core.connector_registry import ConnectorRegistry

logger = structlog.get_logger()

_RATE_PATTERN = re.compile(r"^(\d+)\s*/\s*(s|sec|min|h|hour)$", re.IGNORECASE)
_UNIT_SECONDS = {"s": 1, "sec": 1, "min": 60, "h": 3600, "hour": 3600}
_REDIS_KEY_PREFIX = "rate_limit:"


@dataclass
class RateLimitConfig:
    requests: int
    window_seconds: int


@dataclass
class RateLimitResult:
    allowed: bool
    remaining: int
    retry_after: float | None
    limit: int
    window_seconds: int


def _parse_rate(rate_str: str) -> RateLimitConfig:
    match = _RATE_PATTERN.match(rate_str.strip())
    if not match:
        raise ValueError(f"Invalid rate format '{rate_str}', expected e.g. '100/min', '30/s', '5000/h'")
    count = int(match.group(1))
    unit = match.group(2).lower()
    return RateLimitConfig(requests=count, window_seconds=_UNIT_SECONDS[unit])


class ConnectorRateLimiter:
    _DEFAULT_CONFIG = RateLimitConfig(requests=600, window_seconds=60)

    def __init__(
        self,
        redis_getter: Callable[[], Awaitable[Any]],
        registry: ConnectorRegistry | None = None,
    ) -> None:
        self._redis_getter = redis_getter
        self._registry = registry

    def _get_limits(
        self,
        connector_name: str,
        action: str | None = None,
        connector_version: str | None = None,
    ) -> RateLimitConfig:
        if self._registry is None:
            return self._DEFAULT_CONFIG

        manifest = self._registry.get_by_name_version(connector_name, connector_version)
        if manifest is None:
            return self._DEFAULT_CONFIG

        rate_limits: dict[str, Any] = getattr(manifest, "rate_limits", {}) or {}
        if not rate_limits:
            return self._DEFAULT_CONFIG

        if action:
            per_action = rate_limits.get("per_action", {})
            action_rate = per_action.get(action)
            if action_rate:
                try:
                    return _parse_rate(action_rate)
                except ValueError:
                    logger.warning("connector_rate_limiter.invalid_action_rate", connector=connector_name, action=action)

        global_rate = rate_limits.get("global")
        if global_rate:
            try:
                return _parse_rate(global_rate)
            except ValueError:
                logger.warning("connector_rate_limiter.invalid_global_rate", connector=connector_name)

        return self._DEFAULT_CONFIG

    async def check(
        self,
        connector_name: str,
        action: str | None = None,
        tenant_id: str | None = None,
        connector_version: str | None = None,
    ) -> RateLimitResult:
        config = self._get_limits(connector_name, action, connector_version)
        action_part = action or "global"
        tenant_part = tenant_id or "shared"
        version_part = connector_version or "latest"
        key = f"{_REDIS_KEY_PREFIX}{connector_name}:{version_part}:{action_part}:{tenant_part}"

        redis = await self._redis_getter()
        now = time.time()
        window_start = now - config.window_seconds

        pipe = redis.pipeline()
        pipe.zremrangebyscore(key, 0, window_start)
        pipe.zcard(key)
        results = await pipe.execute()
        current_count: int = results[1]

        if current_count < config.requests:
            pipe2 = redis.pipeline()
            pipe2.zadd(key, {str(now): now})
            pipe2.expire(key, config.window_seconds * 2)
            await pipe2.execute()

            return RateLimitResult(
                allowed=True,
                remaining=config.requests - current_count - 1,
                retry_after=None,
                limit=config.requests,
                window_seconds=config.window_seconds,
            )

        oldest_raw = await redis.zrange(key, 0, 0, withscores=True)
        if oldest_raw:
            oldest_ts = float(oldest_raw[0][1])
            retry_after = round((oldest_ts + config.window_seconds) - now, 2)
            retry_after = max(retry_after, 0.1)
        else:
            retry_after = float(config.window_seconds)

        logger.info(
            "connector_rate_limiter.limited",
            connector=connector_name,
            action=action_part,
            tenant=tenant_part,
            retry_after=retry_after,
        )

        return RateLimitResult(
            allowed=False,
            remaining=0,
            retry_after=retry_after,
            limit=config.requests,
            window_seconds=config.window_seconds,
        )

    async def wait_if_needed(
            self,
            connector_name: str,
            action: str | None = None,
            tenant_id: str | None = None,
            connector_version: str | None = None,
        ) -> RateLimitResult:
            result = await self.check(connector_name, action, tenant_id, connector_version)
            if result.allowed:
                return result

            wait = min(result.retry_after or 1.0, 30.0)
            logger.debug(
                "connector_rate_limiter.waiting",
                connector=connector_name,
                wait_seconds=wait,
            )
            await asyncio.sleep(wait)
            return await self.check(connector_name, action, tenant_id, connector_version)
