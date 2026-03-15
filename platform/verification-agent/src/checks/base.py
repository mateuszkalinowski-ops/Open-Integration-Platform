"""Tier 1 — Infrastructure checks applicable to all connectors."""

import time
from typing import Any

import httpx

from src.config import settings
from src.discovery import VerificationTarget

TIMEOUT = httpx.Timeout(settings.verification_timeout_seconds, connect=10.0)


def _check_result(
    name: str,
    status: str,
    response_time_ms: int,
    error: str | None = None,
    suggestion: str | None = None,
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "name": name,
        "status": status,
        "response_time_ms": response_time_ms,
    }
    if error:
        result["error"] = error
    if suggestion:
        result["suggestion"] = suggestion
    return result


async def check_health(client: httpx.AsyncClient, target: VerificationTarget) -> dict[str, Any]:
    start = time.monotonic()
    try:
        r = await client.get(f"{target.base_url}{target.manifest.health_endpoint}")
        ms = int((time.monotonic() - start) * 1000)
        if r.status_code == 200:
            data = r.json()
            if data.get("status") == "healthy":
                return _check_result("health", "PASS", ms)
            return _check_result("health", "FAIL", ms, error=f"Unhealthy: {data.get('status')}")
        return _check_result("health", "FAIL", ms, error=f"HTTP {r.status_code}")
    except httpx.ConnectError:
        ms = int((time.monotonic() - start) * 1000)
        return _check_result(
            "health",
            "FAIL",
            ms,
            error="Connection refused — container not running",
            suggestion=f"Check if {target.manifest.name} container is deployed and healthy",
        )
    except httpx.TimeoutException:
        ms = int((time.monotonic() - start) * 1000)
        return _check_result("health", "FAIL", ms, error="Timeout")
    except Exception as exc:
        ms = int((time.monotonic() - start) * 1000)
        return _check_result("health", "FAIL", ms, error=str(exc))


async def check_readiness(client: httpx.AsyncClient, target: VerificationTarget) -> dict[str, Any]:
    start = time.monotonic()
    try:
        r = await client.get(f"{target.base_url}/readiness")
        ms = int((time.monotonic() - start) * 1000)
        if r.status_code == 200:
            return _check_result("readiness", "PASS", ms)
        return _check_result("readiness", "FAIL", ms, error=f"HTTP {r.status_code}")
    except httpx.ConnectError:
        ms = int((time.monotonic() - start) * 1000)
        return _check_result("readiness", "FAIL", ms, error="Connection refused")
    except Exception as exc:
        ms = int((time.monotonic() - start) * 1000)
        return _check_result("readiness", "FAIL", ms, error=str(exc))


async def check_docs(client: httpx.AsyncClient, target: VerificationTarget) -> dict[str, Any]:
    start = time.monotonic()
    try:
        r = await client.get(f"{target.base_url}{target.manifest.docs_url}")
        ms = int((time.monotonic() - start) * 1000)
        if r.status_code == 200:
            return _check_result("docs_endpoint", "PASS", ms)
        return _check_result("docs_endpoint", "FAIL", ms, error=f"HTTP {r.status_code}")
    except Exception as exc:
        ms = int((time.monotonic() - start) * 1000)
        return _check_result("docs_endpoint", "FAIL", ms, error=str(exc))


async def run_tier1(client: httpx.AsyncClient, target: VerificationTarget) -> list[dict[str, Any]]:
    """Run all Tier 1 infrastructure checks."""
    return [
        await check_health(client, target),
        await check_readiness(client, target),
        await check_docs(client, target),
    ]
