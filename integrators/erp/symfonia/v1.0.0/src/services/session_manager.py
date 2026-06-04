"""Session lifecycle management for Symfonia WebAPI.

Symfonia WebAPI uses a two-step auth flow:
1. Open session: GET /api/Sessions/OpenNewSession?deviceName=...
   with header Authorization: Application {GUID}
2. Use session: Authorization: Session {token} on all subsequent requests

Sessions can expire — this manager handles automatic renewal.
"""

import asyncio
import logging
import time
from typing import Any

import httpx

logger = logging.getLogger(__name__)

SESSION_RENEWAL_BUFFER_SECONDS = 60


class SessionManager:
    """Manages Symfonia WebAPI session tokens with automatic renewal."""

    def __init__(
        self,
        base_url: str,
        application_guid: str,
        device_name: str = "pinquark-oip",
        session_timeout_minutes: int = 30,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._application_guid = application_guid
        self._device_name = device_name
        self._session_timeout_seconds = session_timeout_minutes * 60
        self._session_token: str | None = None
        self._session_created_at: float = 0.0
        self._lock = asyncio.Lock()
        self._owns_client = http_client is None
        self._client = http_client or httpx.AsyncClient(
            timeout=httpx.Timeout(connect=30.0, read=60.0, write=60.0, pool=30.0),
            verify=False,
        )

    @property
    def is_session_valid(self) -> bool:
        if not self._session_token:
            return False
        elapsed = time.monotonic() - self._session_created_at
        return elapsed < (self._session_timeout_seconds - SESSION_RENEWAL_BUFFER_SECONDS)

    async def get_session_token(self) -> str:
        """Return a valid session token, creating or renewing as needed."""
        if self.is_session_valid and self._session_token:
            return self._session_token

        async with self._lock:
            if self.is_session_valid and self._session_token:
                return self._session_token
            return await self._open_session()

    async def _open_session(self) -> str:
        url = f"{self._base_url}/api/Sessions/OpenNewSession"
        headers = {"Authorization": f"Application {self._application_guid}"}
        params = {"deviceName": self._device_name}

        logger.info("Opening new Symfonia WebAPI session (device=%s)", self._device_name)

        resp = await self._client.get(url, headers=headers, params=params)
        resp.raise_for_status()

        token = resp.text.strip().strip('"')
        if not token:
            raise ValueError("Symfonia WebAPI returned empty session token")

        self._session_token = token
        self._session_created_at = time.monotonic()
        logger.info("Symfonia WebAPI session opened successfully")
        return token

    def get_auth_headers(self) -> dict[str, str]:
        """Return headers with the current session token (synchronous, for pre-fetched tokens)."""
        if not self._session_token:
            raise RuntimeError("No active session — call get_session_token() first")
        return {
            "Authorization": f"Session {self._session_token}",
            "Content-Type": "application/json",
        }

    async def invalidate(self) -> None:
        """Force session renewal on next request."""
        self._session_token = None
        self._session_created_at = 0.0

    async def close(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    async def ping(self) -> dict[str, Any]:
        """Call the open /api/Ping endpoint to verify WebAPI connectivity."""
        resp = await self._client.get(f"{self._base_url}/api/Ping")
        resp.raise_for_status()
        return resp.json()

    async def alive(self) -> str:
        """Call the open /api/Alive endpoint to get server time."""
        resp = await self._client.get(f"{self._base_url}/api/Alive")
        resp.raise_for_status()
        return resp.text
