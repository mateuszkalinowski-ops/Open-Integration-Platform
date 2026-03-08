"""Tier 2 — Authentication and credential validation checks."""

import time
from typing import Any

import httpx

from src.discovery import VerificationTarget


async def check_connection_status(
    client: httpx.AsyncClient,
    target: VerificationTarget,
    account_name: str,
) -> dict[str, Any]:
    """Try GET /connection/{account_name}/status."""
    start = time.monotonic()
    try:
        r = await client.get(
            f"{target.base_url}/connection/{account_name}/status",
        )
        ms = int((time.monotonic() - start) * 1000)
        if r.status_code == 200:
            data = r.json()
            connected = data.get("connected", data.get("status") == "success")
            if connected:
                return {"name": "connection_status", "status": "PASS", "response_time_ms": ms}
            error = data.get("error", "Not connected")
            return {
                "name": "connection_status", "status": "FAIL", "response_time_ms": ms,
                "error": error,
                "suggestion": f"Check credentials for {target.manifest.name}",
            }
        return {
            "name": "connection_status", "status": "FAIL", "response_time_ms": ms,
            "error": f"HTTP {r.status_code}",
        }
    except Exception as exc:
        ms = int((time.monotonic() - start) * 1000)
        return {"name": "connection_status", "status": "FAIL", "response_time_ms": ms, "error": str(exc)}


async def check_auth_status(
    client: httpx.AsyncClient,
    target: VerificationTarget,
    account_name: str,
) -> dict[str, Any]:
    """Try GET /auth/{account_name}/status."""
    start = time.monotonic()
    try:
        r = await client.get(f"{target.base_url}/auth/{account_name}/status")
        ms = int((time.monotonic() - start) * 1000)
        if r.status_code == 200:
            data = r.json()
            if data.get("authenticated", False):
                return {"name": "auth_status", "status": "PASS", "response_time_ms": ms}
            return {
                "name": "auth_status", "status": "FAIL", "response_time_ms": ms,
                "error": "Not authenticated",
            }
        return {
            "name": "auth_status", "status": "FAIL", "response_time_ms": ms,
            "error": f"HTTP {r.status_code}",
        }
    except Exception as exc:
        ms = int((time.monotonic() - start) * 1000)
        return {"name": "auth_status", "status": "FAIL", "response_time_ms": ms, "error": str(exc)}


async def ensure_account(
    client: httpx.AsyncClient,
    target: VerificationTarget,
    account_name: str,
) -> bool:
    """Ensure an account exists on the connector, creating it if needed.
    Returns True if account is ready."""
    if not target.credentials:
        return False

    try:
        r = await client.get(f"{target.base_url}/accounts")
        if r.status_code == 200:
            existing = r.json()
            for acc in existing:
                if acc.get("name") == account_name:
                    return True

        payload: dict[str, Any] = {"name": account_name, **target.credentials}
        r = await client.post(f"{target.base_url}/accounts", json=payload)
        return r.status_code < 300
    except Exception:
        return False


async def run_tier2(
    client: httpx.AsyncClient,
    target: VerificationTarget,
) -> list[dict[str, Any]]:
    """Run Tier 2 auth checks. Returns empty list if no credentials available."""
    if not target.credentials or not target.tenant_id:
        return [{"name": "auth_validation", "status": "SKIP", "response_time_ms": 0,
                 "error": "No credentials configured"}]

    results: list[dict[str, Any]] = []
    account_name = target.credentials.get("account_name", "verification-agent")

    has_accounts_endpoint = target.manifest.interface in (
        "invoice-ocr", "email", "ftp-sftp",
    )

    if has_accounts_endpoint:
        ok = await ensure_account(client, target, account_name)
        if ok:
            results.append(await check_auth_status(client, target, account_name))
            results.append(await check_connection_status(client, target, account_name))
        else:
            results.append({
                "name": "account_provisioning", "status": "FAIL", "response_time_ms": 0,
                "error": "Failed to provision account on connector",
            })
    else:
        results.append(await check_connection_status(client, target, account_name))

    return results
