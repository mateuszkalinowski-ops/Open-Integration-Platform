"""API Version Check — detects newer external API versions.

Supports three check methods:
- openapi: fetch an OpenAPI/Swagger spec and extract info.version
- json: fetch a JSON endpoint and extract a version field by dot-path
- html: fetch an HTML page and search for a version pattern via regex
"""

from __future__ import annotations

import logging
import re
import time
from typing import Any

import httpx

from src.checks.common import result
from src.discovery import ApiVersionCheck, VerificationTarget

logger = logging.getLogger(__name__)

_VERSION_RE = re.compile(
    r"(?:v(?:ersion)?\.?\s*)?(\d+(?:\.\d+){0,3})",
    re.IGNORECASE,
)


def _extract_field(data: Any, path: str) -> str | None:
    """Extract a nested field from a dict using dot-notation (e.g. 'info.version')."""
    parts = path.split(".")
    current = data
    for part in parts:
        if isinstance(current, dict):
            current = current.get(part)
        else:
            return None
    return str(current) if current is not None else None


def _normalize_version(v: str) -> list[int]:
    """Convert '3.2.0' → [3, 2, 0] for comparison."""
    nums = re.findall(r"\d+", v)
    return [int(n) for n in nums] if nums else []


def _is_newer(remote: str, current: str) -> bool:
    return _normalize_version(remote) > _normalize_version(current)


async def _check_openapi(
    client: httpx.AsyncClient, avc: ApiVersionCheck,
) -> tuple[str | None, str | None]:
    r = await client.get(avc.check_url, follow_redirects=True)
    if r.status_code != 200:
        return None, f"HTTP {r.status_code} fetching OpenAPI spec"
    try:
        data = r.json()
    except Exception:
        return None, "Response is not valid JSON"
    version = _extract_field(data, avc.version_field or "info.version")
    return version, None


async def _check_json(
    client: httpx.AsyncClient, avc: ApiVersionCheck,
) -> tuple[str | None, str | None]:
    r = await client.get(avc.check_url, follow_redirects=True)
    if r.status_code != 200:
        return None, f"HTTP {r.status_code}"
    try:
        data = r.json()
    except Exception:
        return None, "Response is not valid JSON"
    version = _extract_field(data, avc.version_field)
    return version, None


async def _check_html(
    client: httpx.AsyncClient, avc: ApiVersionCheck,
) -> tuple[str | None, str | None]:
    r = await client.get(avc.check_url, follow_redirects=True)
    if r.status_code != 200:
        return None, f"HTTP {r.status_code}"
    text = r.text
    if avc.version_field:
        pattern = re.compile(avc.version_field)
        m = pattern.search(text)
        if m:
            return m.group(1) if m.lastindex else m.group(0), None
    matches = _VERSION_RE.findall(text)
    if matches:
        return matches[0], None
    return None, "No version pattern found in HTML"


_CHECKERS = {
    "openapi": _check_openapi,
    "json": _check_json,
    "html": _check_html,
}


async def check_api_version(
    client: httpx.AsyncClient,
    target: VerificationTarget,
) -> dict[str, Any] | None:
    """Check if a newer version of the external API is available.

    Returns a check result dict, or None if no api_version_check is configured.
    """
    avc = target.manifest.api_version_check
    if not avc or not avc.check_url:
        return None

    start = time.monotonic()
    checker = _CHECKERS.get(avc.check_type, _check_openapi)

    try:
        remote_version, error = await checker(client, avc)
        ms = int((time.monotonic() - start) * 1000)

        if error:
            return result(
                "api_version_check", "SKIP", ms,
                error=f"Could not fetch remote version: {error}",
            )

        if remote_version is None:
            return result(
                "api_version_check", "SKIP", ms,
                error="Remote version not found",
            )

        current = avc.current_api_version
        if _is_newer(remote_version, current):
            return {
                "name": "api_version_check",
                "status": "WARN",
                "response_time_ms": ms,
                "current_api_version": current,
                "latest_api_version": remote_version,
                "docs_url": avc.docs_url or avc.check_url,
                "error": f"Newer API version available: {remote_version} (current: {current})",
                "suggestion": f"Update connector to API version {remote_version}",
            }

        return {
            "name": "api_version_check",
            "status": "PASS",
            "response_time_ms": ms,
            "current_api_version": current,
            "latest_api_version": remote_version,
        }

    except Exception as exc:
        ms = int((time.monotonic() - start) * 1000)
        return result(
            "api_version_check", "SKIP", ms,
            error=f"Version check failed: {exc}",
        )
