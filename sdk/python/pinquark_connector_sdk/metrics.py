"""Prometheus metrics auto-instrumentation for connector FastAPI apps."""

from __future__ import annotations

import time
from typing import Any

from fastapi import FastAPI, Request, Response
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

from pinquark_connector_sdk.http import (
    _get_external_api_calls,
    _get_external_api_duration,
    _set_external_metrics,
)


_requests_total: Counter | None = None
_request_duration: Histogram | None = None
_errors_total: Counter | None = None


def _init_metrics(connector_name: str) -> dict[str, Any]:
    global _requests_total, _request_duration, _errors_total

    if _requests_total is None:
        _requests_total = Counter(
            "connector_requests_total",
            "Total HTTP requests handled by the connector",
            ["method", "endpoint", "status"],
        )
    if _request_duration is None:
        _request_duration = Histogram(
            "connector_request_duration_seconds",
            "HTTP request latency",
            ["method", "endpoint"],
            buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
        )
    if _errors_total is None:
        _errors_total = Counter(
            "connector_errors_total",
            "Total errors by type",
            ["type"],
        )

    ext_calls = _get_external_api_calls()
    ext_duration = _get_external_api_duration()
    _set_external_metrics(ext_calls, ext_duration)

    return {
        "requests_total": _requests_total,
        "request_duration": _request_duration,
        "external_api_calls_total": ext_calls,
        "external_api_duration": ext_duration,
        "errors_total": _errors_total,
    }


def register_metrics(app: FastAPI, connector_name: str) -> dict[str, Any]:
    """Instrument a FastAPI app with Prometheus metrics and add /metrics endpoint."""
    metrics = _init_metrics(connector_name)

    @app.middleware("http")
    async def metrics_middleware(request: Request, call_next: Any) -> Response:
        if request.url.path == "/metrics":
            return await call_next(request)

        start = time.monotonic()
        response: Response = await call_next(request)
        duration = time.monotonic() - start

        endpoint = request.url.path
        method = request.method

        assert _requests_total is not None
        assert _request_duration is not None

        _requests_total.labels(method=method, endpoint=endpoint, status=str(response.status_code)).inc()
        _request_duration.labels(method=method, endpoint=endpoint).observe(duration)

        if response.status_code >= 500 and _errors_total is not None:
            _errors_total.labels(type="http_5xx").inc()

        return response

    @app.get("/metrics", tags=["monitoring"], include_in_schema=False)
    async def prometheus_metrics() -> Response:
        return Response(
            content=generate_latest(),
            media_type=CONTENT_TYPE_LATEST,
        )

    return metrics
