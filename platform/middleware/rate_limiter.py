"""Redis-based sliding window rate limiter middleware (per-tenant)."""

from __future__ import annotations

import time

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import JSONResponse

from config import settings
from core.redis_client import get_redis

_BYPASS_PATHS = {"/health", "/readiness", "/metrics", "/docs", "/openapi.json"}
_RATE_LIMIT_PREFIX = "ratelimit:"


class RateLimiterMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.url.path in _BYPASS_PATHS:
            return await call_next(request)

        api_key = request.headers.get("X-API-Key", "")
        if not api_key:
            return await call_next(request)

        identifier = api_key[:16]
        window = settings.rate_limit_window_seconds
        max_requests = settings.rate_limit_requests

        try:
            redis = await get_redis()
            now = time.time()
            key = f"{_RATE_LIMIT_PREFIX}{identifier}"

            pipe = redis.pipeline()
            pipe.zremrangebyscore(key, 0, now - window)
            pipe.zadd(key, {str(now): now})
            pipe.zcard(key)
            pipe.expire(key, window)
            results = await pipe.execute()

            current_count: int = results[2]

            if current_count > max_requests:
                retry_after = int(window - (now - float(await redis.zrange(key, 0, 0)
                                                         or [str(now)])[0])) or 1
                return JSONResponse(
                    status_code=429,
                    content={
                        "error": {
                            "code": "RATE_LIMITED",
                            "message": f"Rate limit exceeded: {max_requests} requests per {window}s",
                        }
                    },
                    headers={
                        "Retry-After": str(retry_after),
                        "X-RateLimit-Limit": str(max_requests),
                        "X-RateLimit-Remaining": "0",
                        "X-RateLimit-Reset": str(int(now) + retry_after),
                    },
                )

            response = await call_next(request)
            response.headers["X-RateLimit-Limit"] = str(max_requests)
            response.headers["X-RateLimit-Remaining"] = str(max(0, max_requests - current_count))
            return response

        except Exception:
            return await call_next(request)
