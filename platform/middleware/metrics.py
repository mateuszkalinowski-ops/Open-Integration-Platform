"""Prometheus metrics middleware and /metrics endpoint."""

from __future__ import annotations

import time

from fastapi import Request, Response
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Histogram,
    generate_latest,
)
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response as StarletteResponse

REQUEST_COUNT = Counter(
    "integrator_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"],
)
REQUEST_DURATION = Histogram(
    "integrator_request_duration_seconds",
    "HTTP request latency",
    ["method", "endpoint"],
    buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0),
)
ERRORS_TOTAL = Counter(
    "integrator_errors_total",
    "Total errors",
    ["type"],
)

_SKIP_PATHS = {"/metrics", "/health", "/readiness"}


class PrometheusMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.url.path in _SKIP_PATHS:
            return await call_next(request)

        method = request.method
        path = request.url.path
        start = time.monotonic()

        try:
            response = await call_next(request)
        except Exception:
            ERRORS_TOTAL.labels(type="unhandled").inc()
            raise

        duration = time.monotonic() - start
        status = str(response.status_code)

        REQUEST_COUNT.labels(method=method, endpoint=path, status=status).inc()
        REQUEST_DURATION.labels(method=method, endpoint=path).observe(duration)

        if response.status_code >= 500:
            ERRORS_TOTAL.labels(type="http_5xx").inc()

        return response


async def metrics_endpoint() -> StarletteResponse:
    return StarletteResponse(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
    )
