"""Proxy service — forwards REST requests to the on-premise Nexo agent."""

import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class AgentProxy:
    """Proxies requests from the cloud platform to a remote on-premise agent."""

    def __init__(self, agent_url: str, agent_api_key: str = "", timeout: float = 60.0):
        self._agent_url = agent_url.rstrip("/")
        self._api_key = agent_api_key
        self._client = httpx.AsyncClient(timeout=timeout)

    async def close(self) -> None:
        await self._client.aclose()

    def _headers(self) -> dict[str, str]:
        h: dict[str, str] = {"Content-Type": "application/json"}
        if self._api_key:
            h["Authorization"] = f"Bearer {self._api_key}"
        return h

    async def health(self) -> dict[str, Any]:
        resp = await self._client.get(f"{self._agent_url}/health", headers=self._headers())
        resp.raise_for_status()
        return resp.json()

    async def get(self, path: str, params: dict | None = None) -> dict[str, Any]:
        resp = await self._client.get(
            f"{self._agent_url}{path}",
            params=params,
            headers=self._headers(),
        )
        resp.raise_for_status()
        return resp.json()

    async def post(self, path: str, json_body: dict | None = None) -> dict[str, Any]:
        resp = await self._client.post(
            f"{self._agent_url}{path}",
            json=json_body,
            headers=self._headers(),
        )
        resp.raise_for_status()
        return resp.json()

    async def put(self, path: str, json_body: dict | None = None) -> dict[str, Any]:
        resp = await self._client.put(
            f"{self._agent_url}{path}",
            json=json_body,
            headers=self._headers(),
        )
        resp.raise_for_status()
        return resp.json()

    async def delete(self, path: str) -> dict[str, Any]:
        resp = await self._client.delete(
            f"{self._agent_url}{path}",
            headers=self._headers(),
        )
        resp.raise_for_status()
        return resp.json()
