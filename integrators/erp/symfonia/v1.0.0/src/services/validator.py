"""Credential validator for Symfonia ERP WebAPI.

Validates that the provided WebAPI URL and Application GUID
can successfully open a session and reach the Ping endpoint.
"""

import logging
from typing import Any

import httpx

from src.services.session_manager import SessionManager

logger = logging.getLogger(__name__)


class SymfoniaValidator:
    """Validates connectivity and credentials for Symfonia WebAPI."""

    async def validate(
        self,
        webapi_url: str,
        application_guid: str,
        device_name: str = "pinquark-validator",
    ) -> dict[str, Any]:
        result: dict[str, Any] = {
            "valid": False,
            "webapi_url": webapi_url,
            "checks": {},
        }

        async with httpx.AsyncClient(timeout=15.0, verify=False) as client:
            if not await self._check_alive(client, webapi_url, result):
                return result

            if not await self._check_ping(client, webapi_url, result):
                return result

        session = SessionManager(
            base_url=webapi_url,
            application_guid=application_guid,
            device_name=device_name,
        )
        try:
            if not await self._check_session(session, result):
                return result

            result["valid"] = True
            result["message"] = "Symfonia WebAPI connection validated successfully"
        finally:
            await session.close()

        return result

    async def _check_alive(
        self,
        client: httpx.AsyncClient,
        base_url: str,
        result: dict[str, Any],
    ) -> bool:
        try:
            resp = await client.get(f"{base_url.rstrip('/')}/api/Alive")
            resp.raise_for_status()
            result["checks"]["alive"] = {"status": "ok", "server_time": resp.text.strip()}
            return True
        except Exception as exc:
            result["checks"]["alive"] = {"status": "error", "error": str(exc)}
            result["message"] = f"WebAPI unreachable at {base_url}: {exc}"
            return False

    async def _check_ping(
        self,
        client: httpx.AsyncClient,
        base_url: str,
        result: dict[str, Any],
    ) -> bool:
        try:
            resp = await client.get(f"{base_url.rstrip('/')}/api/Ping")
            resp.raise_for_status()
            ping_data = resp.json()
            result["checks"]["ping"] = {"status": "ok", "data": ping_data}
            return True
        except Exception as exc:
            result["checks"]["ping"] = {"status": "error", "error": str(exc)}
            result["message"] = f"Ping check failed: {exc}"
            return False

    async def _check_session(
        self,
        session: SessionManager,
        result: dict[str, Any],
    ) -> bool:
        try:
            token = await session.get_session_token()
            result["checks"]["session"] = {
                "status": "ok",
                "token_obtained": bool(token),
            }
            return True
        except Exception as exc:
            result["checks"]["session"] = {"status": "error", "error": str(exc)}
            result["message"] = f"Session authentication failed: {exc}"
            return False
