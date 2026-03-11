"""HTTP client with circuit breaker, automatic retries, and Prometheus metrics."""

from __future__ import annotations

import asyncio
import enum
import time
from typing import Any
from urllib.parse import urlparse

import httpx
import structlog
from prometheus_client import Counter, Histogram

logger = structlog.get_logger(__name__)

DEFAULT_CONNECT_TIMEOUT = 10.0
DEFAULT_READ_TIMEOUT = 30.0
MAX_RETRIES = 3
BACKOFF_BASE = 0.5
BACKOFF_FACTOR = 2.0

_external_api_calls: Counter | None = None
_external_api_duration: Histogram | None = None


def _get_external_api_calls() -> Counter:
    global _external_api_calls
    if _external_api_calls is None:
        _external_api_calls = Counter(
            "connector_external_api_calls_total",
            "External API calls made by the connector",
            ["host", "method", "status"],
        )
    return _external_api_calls


def _get_external_api_duration() -> Histogram:
    global _external_api_duration
    if _external_api_duration is None:
        _external_api_duration = Histogram(
            "connector_external_api_duration_seconds",
            "External API call latency",
            ["host", "method"],
            buckets=[0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0],
        )
    return _external_api_duration


def _set_external_metrics(calls: Counter, duration: Histogram) -> None:
    """Allow metrics.py to inject pre-created collectors, avoiding duplicates."""
    global _external_api_calls, _external_api_duration
    _external_api_calls = calls
    _external_api_duration = duration


class _CBState(enum.Enum):
    CLOSED = 0
    OPEN = 1
    HALF_OPEN = 2


class CircuitBreakerOpen(Exception):
    def __init__(self, host: str, remaining: float) -> None:
        self.host = host
        self.remaining = remaining
        super().__init__(f"Circuit breaker for '{host}' is OPEN, retry after {remaining:.1f}s")


class _CircuitBreaker:
    """Lightweight per-host circuit breaker."""

    def __init__(self, failure_threshold: int = 5, reset_timeout: float = 30.0) -> None:
        self._failure_threshold = failure_threshold
        self._reset_timeout = reset_timeout
        self._state = _CBState.CLOSED
        self._failure_count = 0
        self._last_failure: float = 0.0
        self._lock = asyncio.Lock()

    async def pre_check(self) -> None:
        async with self._lock:
            if self._state == _CBState.OPEN:
                elapsed = time.monotonic() - self._last_failure
                if elapsed >= self._reset_timeout:
                    self._state = _CBState.HALF_OPEN
                else:
                    raise CircuitBreakerOpen("host", self._reset_timeout - elapsed)
            if self._state == _CBState.HALF_OPEN:
                pass

    async def on_success(self) -> None:
        async with self._lock:
            self._state = _CBState.CLOSED
            self._failure_count = 0

    async def on_failure(self) -> None:
        async with self._lock:
            self._failure_count += 1
            self._last_failure = time.monotonic()
            if self._state == _CBState.HALF_OPEN:
                self._state = _CBState.OPEN
            elif self._failure_count >= self._failure_threshold:
                self._state = _CBState.OPEN


class ConnectorHttpClient:
    """Async HTTP client with per-host circuit breakers, retries, and metrics.

    Usage::

        client = ConnectorHttpClient()
        response = await client.get("https://api.example.com/v1/items")
        await client.close()
    """

    def __init__(
        self,
        *,
        connect_timeout: float = DEFAULT_CONNECT_TIMEOUT,
        read_timeout: float = DEFAULT_READ_TIMEOUT,
        max_retries: int = MAX_RETRIES,
        cb_failure_threshold: int = 5,
        cb_reset_timeout: float = 30.0,
    ) -> None:
        self._connect_timeout = connect_timeout
        self._read_timeout = read_timeout
        self._max_retries = max_retries
        self._cb_failure_threshold = cb_failure_threshold
        self._cb_reset_timeout = cb_reset_timeout
        self._breakers: dict[str, _CircuitBreaker] = {}
        self._client: httpx.AsyncClient | None = None

    def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(
                    connect=self._connect_timeout,
                    read=self._read_timeout,
                    write=self._read_timeout,
                    pool=self._connect_timeout,
                ),
                limits=httpx.Limits(max_connections=200, max_keepalive_connections=50),
            )
        return self._client

    def _breaker_for(self, url: str) -> _CircuitBreaker:
        parsed = urlparse(url)
        host = f"{parsed.scheme}://{parsed.netloc}"
        if host not in self._breakers:
            self._breakers[host] = _CircuitBreaker(
                failure_threshold=self._cb_failure_threshold,
                reset_timeout=self._cb_reset_timeout,
            )
        return self._breakers[host]

    @staticmethod
    def _host_label(url: str) -> str:
        parsed = urlparse(url)
        return parsed.netloc or "unknown"

    async def request(
        self,
        method: str,
        url: str,
        *,
        headers: dict[str, str] | None = None,
        json: Any | None = None,
        params: dict[str, Any] | None = None,
        data: Any | None = None,
        files: Any | None = None,
        content: bytes | None = None,
    ) -> httpx.Response:
        breaker = self._breaker_for(url)
        host_label = self._host_label(url)
        last_exc: Exception | None = None

        for attempt in range(self._max_retries + 1):
            await breaker.pre_check()

            start = time.monotonic()
            try:
                response = await self._get_client().request(
                    method,
                    url,
                    headers=headers,
                    json=json,
                    params=params,
                    data=data,
                    files=files,
                    content=content,
                )
                duration = time.monotonic() - start

                _get_external_api_duration().labels(host=host_label, method=method).observe(duration)
                _get_external_api_calls().labels(host=host_label, method=method, status=str(response.status_code)).inc()

                logger.debug(
                    "http_request",
                    method=method,
                    url=url,
                    status=response.status_code,
                    duration_ms=round(duration * 1000, 1),
                    attempt=attempt + 1,
                )

                if response.status_code >= 500 and attempt < self._max_retries:
                    await breaker.on_failure()
                    last_exc = httpx.HTTPStatusError(
                        f"Server error {response.status_code}",
                        request=response.request,
                        response=response,
                    )
                    await self._backoff(attempt)
                    continue

                await breaker.on_success()
                return response

            except (httpx.ConnectError, httpx.ReadTimeout, httpx.WriteTimeout, httpx.PoolTimeout) as exc:
                duration = time.monotonic() - start
                _get_external_api_duration().labels(host=host_label, method=method).observe(duration)
                _get_external_api_calls().labels(host=host_label, method=method, status="error").inc()

                logger.warning(
                    "http_request_failed",
                    method=method,
                    url=url,
                    error=str(exc),
                    attempt=attempt + 1,
                )
                await breaker.on_failure()
                last_exc = exc

                if attempt < self._max_retries:
                    await self._backoff(attempt)
                    continue
                raise

        if last_exc is not None:
            raise last_exc
        raise RuntimeError("Unexpected retry loop exit")

    @staticmethod
    async def _backoff(attempt: int) -> None:
        delay = BACKOFF_BASE * (BACKOFF_FACTOR ** attempt)
        await asyncio.sleep(delay)

    async def get(self, url: str, **kwargs: Any) -> httpx.Response:
        return await self.request("GET", url, **kwargs)

    async def post(self, url: str, **kwargs: Any) -> httpx.Response:
        return await self.request("POST", url, **kwargs)

    async def put(self, url: str, **kwargs: Any) -> httpx.Response:
        return await self.request("PUT", url, **kwargs)

    async def patch(self, url: str, **kwargs: Any) -> httpx.Response:
        return await self.request("PATCH", url, **kwargs)

    async def delete(self, url: str, **kwargs: Any) -> httpx.Response:
        return await self.request("DELETE", url, **kwargs)

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None
        self._breakers.clear()
