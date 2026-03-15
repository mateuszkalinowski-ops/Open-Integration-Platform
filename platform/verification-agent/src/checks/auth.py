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
                "name": "connection_status",
                "status": "FAIL",
                "response_time_ms": ms,
                "error": error,
                "suggestion": f"Check credentials for {target.manifest.name}",
            }
        return {
            "name": "connection_status",
            "status": "FAIL",
            "response_time_ms": ms,
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
                "name": "auth_status",
                "status": "FAIL",
                "response_time_ms": ms,
                "error": "Not authenticated",
            }
        return {
            "name": "auth_status",
            "status": "FAIL",
            "response_time_ms": ms,
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


async def check_manifest_validate_endpoint(
    client: httpx.AsyncClient,
    target: VerificationTarget,
    account_name: str,
) -> dict[str, Any]:
    """Use the connector's own validate_endpoint from credential_validation."""
    validation = getattr(target.manifest, "credential_validation", None) or {}
    endpoint_template = validation.get("validate_endpoint", "")
    if not endpoint_template:
        return {
            "name": "manifest_validation",
            "status": "SKIP",
            "response_time_ms": 0,
            "error": "No validate_endpoint in manifest",
        }

    endpoint = endpoint_template.replace("{account_name}", account_name)
    url = f"{target.base_url}{endpoint}"
    start = time.monotonic()
    try:
        r = await client.get(url)
        ms = int((time.monotonic() - start) * 1000)
        if r.status_code == 200:
            return {"name": "manifest_validation", "status": "PASS", "response_time_ms": ms}
        return {
            "name": "manifest_validation",
            "status": "FAIL",
            "response_time_ms": ms,
            "error": f"HTTP {r.status_code}",
        }
    except Exception as exc:
        ms = int((time.monotonic() - start) * 1000)
        return {"name": "manifest_validation", "status": "FAIL", "response_time_ms": ms, "error": str(exc)}


async def run_tier2(
    client: httpx.AsyncClient,
    target: VerificationTarget,
) -> list[dict[str, Any]]:
    """Run Tier 2 auth checks. Returns empty list if no credentials available.

    Uses ``credential_provisioning`` from the connector manifest to decide
    whether an account should be provisioned before auth checks.
    Falls back to ``credential_validation.validate_endpoint`` when the
    connector does not use account-based provisioning.
    """
    if not target.credentials or not target.tenant_id:
        return [
            {"name": "auth_validation", "status": "SKIP", "response_time_ms": 0, "error": "No credentials configured"}
        ]

    results: list[dict[str, Any]] = []
    account_name = target.credentials.get("account_name", "verification-agent")

    provisioning = getattr(target.manifest, "credential_provisioning", None) or {}
    has_account_provisioning = provisioning.get("mode") == "account"

    validation = getattr(target.manifest, "credential_validation", None) or {}
    has_validate_endpoint = bool(validation.get("validate_endpoint"))

    if has_account_provisioning:
        ok = await ensure_account(client, target, account_name)
        if not ok:
            results.append(
                {
                    "name": "account_provisioning",
                    "status": "FAIL",
                    "response_time_ms": 0,
                    "error": "Failed to provision account on connector",
                }
            )
            return results

    if has_validate_endpoint:
        results.append(await check_manifest_validate_endpoint(client, target, account_name))
    elif has_account_provisioning:
        results.append(await check_auth_status(client, target, account_name))
        results.append(await check_connection_status(client, target, account_name))
    else:
        results.append(await check_connection_status(client, target, account_name))

    return results
