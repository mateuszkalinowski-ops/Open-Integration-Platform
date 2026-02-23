"""Shared async REST client with connection pooling and circuit breaker."""

from __future__ import annotations

import logging
from typing import Any
from urllib.parse import urlparse

import httpx

from pinquark_common.resilience.circuit_breaker import CircuitBreaker, CircuitBreakerOpen

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 30.0
DEFAULT_MAX_CONNECTIONS = 200
DEFAULT_MAX_KEEPALIVE = 50

_client_pool: dict[str, httpx.AsyncClient] = {}
_circuit_breakers: dict[str, CircuitBreaker] = {}


def _host_key(url: str) -> str:
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}"


def get_pooled_client(
    base_url: str | None = None,
    max_connections: int = DEFAULT_MAX_CONNECTIONS,
    max_keepalive_connections: int = DEFAULT_MAX_KEEPALIVE,
    timeout: float = DEFAULT_TIMEOUT,
) -> httpx.AsyncClient:
    """Get or create a pooled httpx.AsyncClient for a given base URL."""
    key = base_url or "__default__"
    if key not in _client_pool:
        limits = httpx.Limits(
            max_connections=max_connections,
            max_keepalive_connections=max_keepalive_connections,
        )
        _client_pool[key] = httpx.AsyncClient(
            base_url=base_url or "",
            limits=limits,
            timeout=httpx.Timeout(timeout),
        )
    return _client_pool[key]


def get_circuit_breaker(
    name: str,
    failure_threshold: int = 5,
    reset_timeout: float = 30.0,
) -> CircuitBreaker:
    if name not in _circuit_breakers:
        _circuit_breakers[name] = CircuitBreaker(
            name=name,
            failure_threshold=failure_threshold,
            reset_timeout_seconds=reset_timeout,
            excluded_exceptions=(RestClientError,),
        )
    return _circuit_breakers[name]


async def close_all_clients() -> None:
    for client in _client_pool.values():
        await client.aclose()
    _client_pool.clear()


class RestClientError(Exception):
    """Raised when a REST API call fails."""
    def __init__(self, message: str, status_code: int = 400, details: Any = None):
        super().__init__(message)
        self.status_code = status_code
        self.details = details


async def request(
    method: str,
    url: str,
    *,
    headers: dict[str, str] | None = None,
    json: dict | None = None,
    params: dict | None = None,
    data: dict | None = None,
    timeout: float = DEFAULT_TIMEOUT,
    expected_status: set[int] | None = None,
    use_circuit_breaker: bool = True,
) -> httpx.Response:
    """Make an async HTTP request with connection pooling and circuit breaker.

    Uses a pooled client per host for connection reuse. Wraps calls in a
    circuit breaker keyed by host to prevent cascading failures.
    """
    host_key = _host_key(url)
    client = get_pooled_client(timeout=timeout)

    async def _do_request() -> httpx.Response:
        return await client.request(
            method,
            url,
            headers=headers,
            json=json,
            params=params,
            data=data,
            timeout=timeout,
        )

    if use_circuit_breaker:
        cb = get_circuit_breaker(host_key)
        try:
            response = await cb.call(_do_request)
        except CircuitBreakerOpen:
            raise RestClientError(
                f"Service {host_key} is unavailable (circuit breaker open)",
                status_code=503,
            )
    else:
        response = await _do_request()

    if expected_status and response.status_code not in expected_status:
        error_msg = _extract_error_message(response)
        logger.error(
            "REST %s %s returned %d: %s",
            method, url, response.status_code, error_msg,
        )
        raise RestClientError(
            error_msg,
            status_code=response.status_code,
            details=_safe_json(response),
        )

    return response


async def get(url: str, **kwargs: Any) -> httpx.Response:
    return await request("GET", url, **kwargs)


async def post(url: str, **kwargs: Any) -> httpx.Response:
    return await request("POST", url, **kwargs)


async def put(url: str, **kwargs: Any) -> httpx.Response:
    return await request("PUT", url, **kwargs)


async def delete(url: str, **kwargs: Any) -> httpx.Response:
    return await request("DELETE", url, **kwargs)


def bearer_headers(token: str, extra: dict[str, str] | None = None) -> dict[str, str]:
    """Build standard headers with Bearer token auth."""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    if extra:
        headers.update(extra)
    return headers


def _extract_error_message(response: httpx.Response) -> str:
    """Try to extract a human-readable error from the response."""
    data = _safe_json(response)
    if data:
        for key in ("message", "error", "detail", "errorMessage", "error_description"):
            if key in data:
                msg = data[key]
                if isinstance(msg, str):
                    return msg
                return str(msg)
        return str(data)
    return response.text[:500] if response.text else f"HTTP {response.status_code}"


def _safe_json(response: httpx.Response) -> dict | None:
    try:
        return response.json()
    except Exception:
        return None
