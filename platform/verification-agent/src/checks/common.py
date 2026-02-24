"""Shared utilities for Tier 3 functional checks."""

import time
from typing import Any

import httpx

PDF_STUB = (
    b"%PDF-1.0\n1 0 obj<</Pages 2 0 R>>endobj\n"
    b"2 0 obj<</Kids[3 0 R]/Count 1>>endobj\n"
    b"3 0 obj<</MediaBox[0 0 612 792]>>endobj\n"
    b"trailer<</Root 1 0 R>>\n%%EOF"
)


def result(
    name: str,
    status: str,
    ms: int,
    error: str | None = None,
    suggestion: str | None = None,
) -> dict[str, Any]:
    r: dict[str, Any] = {"name": name, "status": status, "response_time_ms": ms}
    if error:
        r["error"] = error
    if suggestion:
        r["suggestion"] = suggestion
    return r


async def get_check(
    client: httpx.AsyncClient,
    url: str,
    name: str,
    params: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Execute a GET request and return a check result dict."""
    start = time.monotonic()
    try:
        r = await client.get(url, params=params)
        ms = int((time.monotonic() - start) * 1000)
        if r.status_code == 200:
            return result(name, "PASS", ms)
        if r.status_code == 404:
            return result(name, "SKIP", ms, error="Endpoint not found (404)")
        return result(name, "FAIL", ms, error=f"HTTP {r.status_code}: {r.text[:200]}")
    except Exception as exc:
        ms = int((time.monotonic() - start) * 1000)
        return result(name, "FAIL", ms, error=str(exc))


async def req_check(
    client: httpx.AsyncClient,
    method: str,
    url: str,
    name: str,
    *,
    params: dict[str, str] | None = None,
    json_body: Any = None,
    files: dict[str, Any] | None = None,
    accept_statuses: tuple[int, ...] = (200, 201),
) -> tuple[dict[str, Any], httpx.Response | None]:
    """Execute an arbitrary HTTP request and return (check_result, response)."""
    start = time.monotonic()
    try:
        kwargs: dict[str, Any] = {"params": params}
        if json_body is not None:
            kwargs["json"] = json_body
        if files is not None:
            kwargs["files"] = files
        r = await client.request(method, url, **kwargs)
        ms = int((time.monotonic() - start) * 1000)
        if r.status_code in accept_statuses:
            return result(name, "PASS", ms), r
        if r.status_code == 404:
            return result(name, "SKIP", ms, error="Endpoint not found (404)"), r
        return result(name, "FAIL", ms, error=f"HTTP {r.status_code}: {r.text[:200]}"), r
    except Exception as exc:
        ms = int((time.monotonic() - start) * 1000)
        return result(name, "FAIL", ms, error=str(exc)), None
