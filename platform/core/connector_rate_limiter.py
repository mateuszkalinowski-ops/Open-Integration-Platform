"""Per-connector token bucket rate limiter backed by Redis."""

from __future__ import annotations

import asyncio
import re
import time
from dataclasses import dataclass
from typing import Any, Awaitable, Callable

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
    def __init__(
        self,
        redis_getter: Callable[[], Awaitable[Any]],
        registry: ConnectorRegistry | None = None,
        *,
        default_rate: str = "600/min",
        enabled: bool = True,
    ) -> None:
        self._redis_getter = redis_getter
        self._registry = registry
        self._enabled = enabled
        self._default_config = _parse_rate(default_rate)

    def _get_limits(
        self,
        connector_name: str,
        action: str | None = None,
        connector_version: str | None = None,
    ) -> RateLimitConfig:
        if self._registry is None:
            return self._default_config

        manifest = self._registry.get_by_name_version(connector_name, connector_version)
        if manifest is None:
            return self._default_config

        rate_limits: dict[str, Any] = getattr(manifest, "rate_limits", {}) or {}
        if not rate_limits:
            return self._default_config

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

        return self._default_config

    async def check(
        self,
        connector_name: str,
        action: str | None = None,
        tenant_id: str | None = None,
        connector_version: str | None = None,
    ) -> RateLimitResult:
        if not self._enabled:
            config = self._get_limits(connector_name, action, connector_version)
            return RateLimitResult(
                allowed=True,
                remaining=config.requests,
                retry_after=None,
                limit=config.requests,
                window_seconds=config.window_seconds,
            )
        config = self._get_limits(connector_name, action, connector_version)
        action_part = action or "global"
        tenant_part = tenant_id or "shared"
        version_part = connector_version or "latest"
        bucket_key = f"{_REDIS_KEY_PREFIX}{connector_name}:{version_part}:{action_part}:{tenant_part}"
        tokens_key = f"{bucket_key}:tokens"
        last_key = f"{bucket_key}:last"

        redis = await self._redis_getter()
        now = time.time()
        refill_rate = config.requests / config.window_seconds

        raw_tokens, raw_last = await redis.mget(tokens_key, last_key)
        tokens = float(raw_tokens) if raw_tokens is not None else float(config.requests)
        last_refill = float(raw_last) if raw_last is not None else now

        elapsed = max(0.0, now - last_refill)
        tokens = min(float(config.requests), tokens + elapsed * refill_rate)

        allowed = tokens >= 1.0
        retry_after: float | None = None
        if allowed:
            tokens -= 1.0
            remaining = max(0, int(tokens))
        else:
            deficit = 1.0 - tokens
            retry_after = max(round(deficit / refill_rate, 2), 0.1)
            remaining = 0

        pipe = redis.pipeline()
        pipe.set(tokens_key, tokens, ex=config.window_seconds * 2)
        pipe.set(last_key, now, ex=config.window_seconds * 2)
        await pipe.execute()

        if allowed:
            return RateLimitResult(
                allowed=True,
                remaining=remaining,
                retry_after=None,
                limit=config.requests,
                window_seconds=config.window_seconds,
            )

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
