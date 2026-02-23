"""Async Redis client singleton with connection pooling."""

from __future__ import annotations

import json
import logging
from typing import Any

import redis.asyncio as aioredis

from config import settings

logger = logging.getLogger(__name__)

_pool: aioredis.ConnectionPool | None = None
_client: aioredis.Redis | None = None


async def get_redis() -> aioredis.Redis:
    global _pool, _client
    if _client is None:
        _pool = aioredis.ConnectionPool.from_url(
            settings.redis_url,
            max_connections=settings.redis_max_connections,
            socket_timeout=settings.redis_socket_timeout,
            socket_connect_timeout=settings.redis_socket_timeout,
            decode_responses=True,
        )
        _client = aioredis.Redis(connection_pool=_pool)
        logger.info(
            "Redis pool created: max_connections=%d, url=%s",
            settings.redis_max_connections,
            settings.redis_url.split("@")[-1],
        )
    return _client


async def close_redis() -> None:
    global _pool, _client
    if _client is not None:
        await _client.aclose()
        _client = None
    if _pool is not None:
        await _pool.aclose()
        _pool = None
    logger.info("Redis connection closed")


async def cache_get(key: str) -> dict | None:
    r = await get_redis()
    raw = await r.get(key)
    if raw is None:
        return None
    return json.loads(raw)


async def cache_set(key: str, value: Any, ttl: int | None = None) -> None:
    r = await get_redis()
    ttl = ttl or settings.redis_cache_ttl
    await r.set(key, json.dumps(value, default=str), ex=ttl)


async def cache_delete(pattern: str) -> int:
    r = await get_redis()
    cursor: int | bytes = 0
    deleted = 0
    while True:
        cursor, keys = await r.scan(cursor=cursor, match=pattern, count=100)
        if keys:
            deleted += await r.delete(*keys)
        if cursor == 0:
            break
    return deleted


async def redis_health() -> bool:
    try:
        r = await get_redis()
        return await r.ping()
    except Exception:
        return False
