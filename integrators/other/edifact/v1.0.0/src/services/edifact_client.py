"""Async HTTP client for communicating with external terminal/TOS/PCS systems."""

from __future__ import annotations

import logging
import random
from typing import Any

import httpx

from src.config import settings

logger = logging.getLogger(__name__)


class EdifactClientError(Exception):
    """Raised when the external system returns an error."""

    def __init__(self, status_code: int, message: str, details: dict | None = None) -> None:
        self.status_code = status_code
        self.message = message
        self.details = details or {}
        super().__init__(message)


class EdifactClient:
    """HTTP client wrapping calls to an external container terminal / TOS / PCS system."""

    def __init__(self, base_url: str, api_key: str = "", name: str = "default") -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.name = name
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            headers: dict[str, str] = {
                "User-Agent": f"OIP-EDIFACT-Connector/{settings.app_version}",
                "Accept": "application/json",
            }
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"

            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers=headers,
                timeout=httpx.Timeout(
                    connect=settings.api_timeout_connect,
                    read=settings.api_timeout_read,
                    write=settings.api_timeout_read,
                    pool=settings.api_timeout_connect,
                ),
            )
        return self._client

    async def _request_with_retry(
        self,
        method: str,
        path: str,
        *,
        json: dict | None = None,
        params: dict | None = None,
    ) -> dict[str, Any]:
        """Execute HTTP request with exponential backoff retry."""
        client = await self._get_client()
        last_exc: Exception | None = None

        for attempt in range(1, settings.max_retries + 1):
            try:
                response = await client.request(method, path, json=json, params=params)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as exc:
                if exc.response.status_code < 500:
                    try:
                        detail = exc.response.json()
                    except Exception:
                        detail = {"raw": exc.response.text[:500]}
                    raise EdifactClientError(
                        status_code=exc.response.status_code,
                        message=f"External system error: {exc.response.status_code}",
                        details=detail,
                    ) from exc
                last_exc = exc
                logger.warning(
                    "Attempt %d/%d failed (HTTP %d) for %s %s",
                    attempt,
                    settings.max_retries,
                    exc.response.status_code,
                    method,
                    path,
                )
            except httpx.RequestError as exc:
                last_exc = exc
                logger.warning(
                    "Attempt %d/%d connection error for %s %s: %s",
                    attempt,
                    settings.max_retries,
                    method,
                    path,
                    exc,
                )

            if attempt < settings.max_retries:
                jitter = random.uniform(0, 0.5)
                backoff = min(2 ** (attempt - 1) + jitter, 30.0)
                import asyncio

                await asyncio.sleep(backoff)

        raise EdifactClientError(
            status_code=502,
            message=f"All {settings.max_retries} attempts failed for {method} {path}",
            details={"last_error": str(last_exc)},
        )

    # --- CODECO endpoints ---

    async def create_gate_event(self, payload: dict[str, Any]) -> dict[str, Any]:
        return await self._request_with_retry("POST", "/codeco/gate-events", json=payload)

    async def list_gate_events(self, params: dict[str, Any]) -> dict[str, Any]:
        return await self._request_with_retry("GET", "/codeco/gate-events", params=params)

    async def get_gate_event(self, event_id: str) -> dict[str, Any]:
        return await self._request_with_retry("GET", f"/codeco/gate-events/{event_id}")

    async def update_gate_event(self, event_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        return await self._request_with_retry("PUT", f"/codeco/gate-events/{event_id}", json=payload)

    async def cancel_gate_event(self, event_id: str) -> dict[str, Any]:
        return await self._request_with_retry("DELETE", f"/codeco/gate-events/{event_id}")

    # --- BAPLIE endpoints ---

    async def create_bay_plan(self, payload: dict[str, Any]) -> dict[str, Any]:
        return await self._request_with_retry("POST", "/baplie/bay-plans", json=payload)

    async def list_bay_plans(self, params: dict[str, Any]) -> dict[str, Any]:
        return await self._request_with_retry("GET", "/baplie/bay-plans", params=params)

    async def get_bay_plan(self, plan_id: str) -> dict[str, Any]:
        return await self._request_with_retry("GET", f"/baplie/bay-plans/{plan_id}")

    async def update_bay_plan(self, plan_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        return await self._request_with_retry("PUT", f"/baplie/bay-plans/{plan_id}", json=payload)

    async def get_bay_plan_locations(self, plan_id: str, params: dict | None = None) -> dict[str, Any]:
        return await self._request_with_retry("GET", f"/baplie/bay-plans/{plan_id}/locations", params=params)

    # --- IFTMIN endpoints ---

    async def create_instruction(self, payload: dict[str, Any]) -> dict[str, Any]:
        return await self._request_with_retry("POST", "/iftmin/instructions", json=payload)

    async def list_instructions(self, params: dict[str, Any]) -> dict[str, Any]:
        return await self._request_with_retry("GET", "/iftmin/instructions", params=params)

    async def get_instruction(self, instruction_id: str) -> dict[str, Any]:
        return await self._request_with_retry("GET", f"/iftmin/instructions/{instruction_id}")

    async def amend_instruction(self, instruction_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        return await self._request_with_retry("PUT", f"/iftmin/instructions/{instruction_id}", json=payload)

    async def cancel_instruction(self, instruction_id: str) -> dict[str, Any]:
        return await self._request_with_retry("DELETE", f"/iftmin/instructions/{instruction_id}")

    # --- Health ---

    async def check_health(self) -> dict[str, str]:
        try:
            client = await self._get_client()
            response = await client.get("/health")
            response.raise_for_status()
            return {"status": "healthy"}
        except Exception as exc:
            return {"status": "unhealthy", "error": str(exc)}

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None
