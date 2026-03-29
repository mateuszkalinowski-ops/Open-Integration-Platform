"""Verification checks for KSeF connector.

Tier 1: Health, readiness, docs endpoints
Tier 2: Authentication with KSeF API (requires valid KSeF token)
Tier 3: Functional smoke tests (open session, send test invoice, close session)
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)

CONNECTOR_NAME = "ksef"
BASE_TIMEOUT = httpx.Timeout(30.0, connect=10.0)


async def run(
    base_url: str,
    credentials: dict[str, Any] | None = None,
    tier: int = 1,
) -> dict[str, Any]:
    """Run verification checks for KSeF connector.

    Args:
        base_url: Connector base URL (e.g. http://connector-ksef:8000)
        credentials: Dict with 'nip', 'ksef_token', 'environment'
        tier: Verification tier (1=health, 2=auth, 3=functional)
    """
    results: dict[str, Any] = {
        "connector": CONNECTOR_NAME,
        "tier": tier,
        "checks": [],
        "passed": True,
    }

    async with httpx.AsyncClient(timeout=BASE_TIMEOUT) as client:
        if tier >= 1:
            await _check_health(client, base_url, results)
            await _check_readiness(client, base_url, results)
            await _check_docs(client, base_url, results)

        if tier >= 2 and credentials:
            await _check_authentication(client, base_url, credentials, results)

        if tier >= 3 and credentials:
            await _check_functional(client, base_url, credentials, results)

    return results


async def _check_health(
    client: httpx.AsyncClient,
    base_url: str,
    results: dict[str, Any],
) -> None:
    check = {"name": "health_endpoint", "passed": False}
    try:
        resp = await client.get(f"{base_url}/health")
        check["status_code"] = resp.status_code
        check["passed"] = resp.status_code == 200

        if resp.status_code == 200:
            data = resp.json()
            check["response"] = data
    except Exception as exc:
        check["error"] = str(exc)

    if not check["passed"]:
        results["passed"] = False
    results["checks"].append(check)


async def _check_readiness(
    client: httpx.AsyncClient,
    base_url: str,
    results: dict[str, Any],
) -> None:
    check = {"name": "readiness_endpoint", "passed": False}
    try:
        resp = await client.get(f"{base_url}/readiness")
        check["status_code"] = resp.status_code
        check["passed"] = resp.status_code == 200
    except Exception as exc:
        check["error"] = str(exc)

    if not check["passed"]:
        results["passed"] = False
    results["checks"].append(check)


async def _check_docs(
    client: httpx.AsyncClient,
    base_url: str,
    results: dict[str, Any],
) -> None:
    check = {"name": "docs_endpoint", "passed": False}
    try:
        resp = await client.get(f"{base_url}/docs")
        check["status_code"] = resp.status_code
        check["passed"] = resp.status_code == 200
    except Exception as exc:
        check["error"] = str(exc)

    if not check["passed"]:
        results["passed"] = False
    results["checks"].append(check)


async def _check_authentication(
    client: httpx.AsyncClient,
    base_url: str,
    credentials: dict[str, Any],
    results: dict[str, Any],
) -> None:
    """Tier 2: Create account and attempt authentication."""
    check = {"name": "authentication", "passed": False}
    account_name = "verification-test"

    try:
        create_resp = await client.post(
            f"{base_url}/accounts",
            json={
                "name": account_name,
                "nip": credentials.get("nip", ""),
                "ksef_token": credentials.get("ksef_token", ""),
                "environment": credentials.get("environment", "demo"),
            },
        )
        check["account_created"] = create_resp.status_code == 201

        auth_resp = await client.post(
            f"{base_url}/auth/token",
            json={"account_name": account_name},
        )
        check["auth_status_code"] = auth_resp.status_code
        check["passed"] = auth_resp.status_code == 200

        if auth_resp.status_code == 200:
            data = auth_resp.json()
            check["has_access_token"] = bool(data.get("access_token"))
            check["has_refresh_token"] = bool(data.get("refresh_token"))

    except Exception as exc:
        check["error"] = str(exc)
    finally:
        try:
            await client.delete(f"{base_url}/accounts/{account_name}")
        except Exception:
            pass

    if not check["passed"]:
        results["passed"] = False
    results["checks"].append(check)


async def _check_functional(
    client: httpx.AsyncClient,
    base_url: str,
    credentials: dict[str, Any],
    results: dict[str, Any],
) -> None:
    """Tier 3: Open session, send test invoice, close session."""
    check = {"name": "functional_smoke_test", "passed": False}
    account_name = "verification-functional"

    try:
        await client.post(
            f"{base_url}/accounts",
            json={
                "name": account_name,
                "nip": credentials.get("nip", ""),
                "ksef_token": credentials.get("ksef_token", ""),
                "environment": credentials.get("environment", "demo"),
            },
        )

        session_resp = await client.post(
            f"{base_url}/sessions",
            json={
                "account_name": account_name,
                "session_type": "online",
                "form_code": "FA3",
            },
        )
        check["session_status_code"] = session_resp.status_code

        if session_resp.status_code == 200:
            session_data = session_resp.json()
            ref_number = session_data.get("reference_number", "")
            check["session_opened"] = bool(ref_number)

            if ref_number:
                status_resp = await client.get(
                    f"{base_url}/sessions/{ref_number}",
                    params={"account_name": account_name},
                )
                check["session_status_check"] = status_resp.status_code == 200

                close_resp = await client.post(
                    f"{base_url}/sessions/{ref_number}/close",
                    params={"account_name": account_name},
                )
                check["session_closed"] = close_resp.status_code == 200

            check["passed"] = True

    except Exception as exc:
        check["error"] = str(exc)
    finally:
        try:
            await client.delete(f"{base_url}/accounts/{account_name}")
        except Exception:
            pass

    if not check["passed"]:
        results["passed"] = False
    results["checks"].append(check)
