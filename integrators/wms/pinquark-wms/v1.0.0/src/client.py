"""HTTP client for the Pinquark WMS Integration REST API.

Handles JWT authentication (login + token refresh) and exposes
every endpoint documented in the Pinquark Integration REST API PDF.

Write operations are asynchronous: HTTP 200 means "accepted", not
"processed". Use ``write_with_feedback`` to submit data and poll
``GET /feedbacks`` until the WMS confirms success or reports errors.
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass
from dataclasses import field as dc_field
from datetime import UTC, datetime
from typing import Any

import httpx

from src.config import settings
from src.schemas import WmsCredentials

logger = logging.getLogger("pinquark-wms-client")


@dataclass
class WriteResult:
    """Outcome of a write operation with optional feedback confirmation."""

    accepted: bool
    http_status: int
    api_response: Any = None
    confirmed: bool | None = None
    feedback_id: int | None = None
    feedback_success: bool | None = None
    feedback_errors: dict[str, str] = dc_field(default_factory=dict)
    feedback_messages: dict[str, str] = dc_field(default_factory=dict)
    timed_out: bool = False

    @property
    def ok(self) -> bool:
        if not self.accepted:
            return False
        if self.confirmed is not None:
            return self.confirmed
        return self.accepted


class _TokenCache:
    """Per-instance JWT token cache with automatic refresh."""

    def __init__(self) -> None:
        self.access_token: str = ""
        self.refresh_token: str = ""
        self.expires_at: float = 0.0


def _normalize_base_url(raw: str) -> str:
    url = raw.rstrip("/")
    for suffix in ("/auth/sign-in", "/auth/refresh-token", "/auth"):
        if url.endswith(suffix):
            url = url[: -len(suffix)]
            break
    return url


class PinquarkWmsClient:
    """Async HTTP client wrapping the Pinquark WMS Integration REST API."""

    def __init__(self) -> None:
        self._client: httpx.AsyncClient | None = None
        self._tokens: dict[str, _TokenCache] = {}

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(
                    connect=settings.http_connect_timeout,
                    read=settings.http_read_timeout,
                    write=settings.http_read_timeout,
                    pool=settings.http_connect_timeout,
                ),
            )
        return self._client

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    # --- Authentication ---

    @staticmethod
    def _base_url(creds: WmsCredentials) -> str:
        return _normalize_base_url(creds.api_url)

    def _cache_key(self, creds: WmsCredentials) -> str:
        return f"{self._base_url(creds)}|{creds.username}"

    async def _ensure_token(self, creds: WmsCredentials) -> str:
        key = self._cache_key(creds)
        cache = self._tokens.get(key)

        if cache and cache.access_token and time.time() < cache.expires_at - 60:
            return cache.access_token

        if cache and cache.refresh_token:
            try:
                return await self._refresh(creds, cache)
            except Exception:
                logger.warning("Token refresh failed, re-authenticating")

        return await self._login(creds)

    @staticmethod
    def _parse_expiry(raw: str) -> float:
        """Parse accessTokenExpirationDate into a Unix timestamp."""
        try:
            dt = datetime.fromisoformat(raw)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=UTC)
            return dt.timestamp()
        except (ValueError, TypeError):
            return time.time() + 23 * 3600

    async def _login(self, creds: WmsCredentials) -> str:
        client = await self._get_client()
        base = self._base_url(creds)
        resp = await client.post(
            f"{base}/auth/sign-in",
            json={"username": creds.username, "password": creds.password},
        )
        resp.raise_for_status()
        data = resp.json()
        cache = _TokenCache()
        cache.access_token = data["accessToken"]
        cache.refresh_token = data["refreshToken"]
        cache.expires_at = self._parse_expiry(data.get("accessTokenExpirationDate", ""))
        self._tokens[self._cache_key(creds)] = cache
        return cache.access_token

    async def _refresh(self, creds: WmsCredentials, cache: _TokenCache) -> str:
        client = await self._get_client()
        base = self._base_url(creds)
        resp = await client.post(
            f"{base}/auth/refresh-token",
            json={"refreshToken": cache.refresh_token},
        )
        resp.raise_for_status()
        data = resp.json()
        cache.access_token = data["accessToken"]
        cache.refresh_token = data["refreshToken"]
        cache.expires_at = self._parse_expiry(data.get("accessTokenExpirationDate", ""))
        return cache.access_token

    async def _headers(self, creds: WmsCredentials) -> dict[str, str]:
        token = await self._ensure_token(creds)
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    # --- Generic request helpers ---

    async def _get(self, creds: WmsCredentials, path: str) -> tuple[Any, int]:
        client = await self._get_client()
        headers = await self._headers(creds)
        base = self._base_url(creds)
        resp = await client.get(f"{base}{path}", headers=headers)
        return resp.json(), resp.status_code

    async def _post(self, creds: WmsCredentials, path: str, body: Any) -> tuple[Any, int]:
        client = await self._get_client()
        headers = await self._headers(creds)
        base = self._base_url(creds)
        resp = await client.post(f"{base}{path}", headers=headers, json=body)
        return resp.json(), resp.status_code

    # --- Feedback-aware write --------------------------------------------------

    async def _snapshot_feedback_ids(self, creds: WmsCredentials) -> set[int]:
        try:
            data, status = await self.get_feedbacks(creds)
            if status < 400 and isinstance(data, list):
                return {f["id"] for f in data if isinstance(f, dict) and "id" in f}
        except Exception:
            logger.debug("Could not snapshot feedbacks, proceeding without")
        return set()

    async def _poll_feedback(
        self,
        creds: WmsCredentials,
        entity: str,
        action: str,
        known_ids: set[int],
    ) -> dict[str, Any] | None:
        interval = settings.feedback_poll_interval
        for attempt in range(settings.feedback_poll_max_attempts):
            await asyncio.sleep(interval)
            try:
                data, status = await self.get_feedbacks(creds)
            except Exception:
                logger.warning("Feedback poll attempt %d failed", attempt + 1)
                interval *= settings.feedback_poll_backoff
                continue

            if status >= 400 or not isinstance(data, list):
                interval *= settings.feedback_poll_backoff
                continue

            for fb in data:
                if not isinstance(fb, dict):
                    continue
                fb_id = fb.get("id")
                if fb_id in known_ids:
                    continue
                fb_entity = (fb.get("entity") or "").upper()
                fb_action = (fb.get("action") or "").upper()
                if fb_entity == entity.upper() and fb_action == action.upper():
                    return fb

            interval = min(interval * settings.feedback_poll_backoff, 10.0)
        return None

    async def write_with_feedback(
        self,
        creds: WmsCredentials,
        entity: str,
        action: str,
        path: str,
        body: Any,
    ) -> WriteResult:
        known_ids = await self._snapshot_feedback_ids(creds)

        api_resp, http_status = await self._post(creds, path, body)

        if http_status >= 400:
            return WriteResult(
                accepted=False,
                http_status=http_status,
                api_response=api_resp,
            )

        logger.info("Write accepted (HTTP %d) for %s/%s, polling feedback…", http_status, entity, action)

        fb = await self._poll_feedback(creds, entity, action, known_ids)
        if fb is None:
            logger.warning("Feedback timeout for %s/%s", entity, action)
            return WriteResult(
                accepted=True,
                http_status=http_status,
                api_response=api_resp,
                timed_out=True,
            )

        success = fb.get("success", False)
        result = WriteResult(
            accepted=True,
            http_status=http_status,
            api_response=api_resp,
            confirmed=success,
            feedback_id=fb.get("id"),
            feedback_success=success,
            feedback_errors=fb.get("errors") or {},
            feedback_messages=fb.get("responseMessages") or {},
        )
        if success:
            logger.info("Feedback confirmed success for %s/%s (id=%s)", entity, action, fb.get("id"))
        else:
            logger.error("Feedback reports failure for %s/%s: %s", entity, action, result.feedback_errors)
        return result

    # --- Articles ---

    async def get_articles(self, creds: WmsCredentials) -> tuple[Any, int]:
        return await self._get(creds, "/articles")

    async def get_articles_delete_commands(self, creds: WmsCredentials) -> tuple[Any, int]:
        return await self._get(creds, "/articles/delete-commands")

    async def create_article(self, creds: WmsCredentials, article: dict) -> tuple[Any, int]:
        return await self._post(creds, "/articles", article)

    async def create_articles(self, creds: WmsCredentials, articles: list[dict]) -> tuple[Any, int]:
        return await self._post(creds, "/articles/list", articles)

    async def delete_article(self, creds: WmsCredentials, command: dict) -> tuple[Any, int]:
        return await self._post(creds, "/articles/delete-commands", command)

    async def delete_articles(self, creds: WmsCredentials, commands: list[dict]) -> tuple[Any, int]:
        return await self._post(creds, "/articles/delete-commands/list", commands)

    # --- Article Batches ---

    async def get_batches(self, creds: WmsCredentials) -> tuple[Any, int]:
        return await self._get(creds, "/article-batches")

    async def create_batch(self, creds: WmsCredentials, batch: dict) -> tuple[Any, int]:
        return await self._post(creds, "/article-batches", batch)

    async def create_batches(self, creds: WmsCredentials, batches: list[dict]) -> tuple[Any, int]:
        return await self._post(creds, "/article-batches/list", batches)

    # --- Documents ---

    async def get_documents(self, creds: WmsCredentials) -> tuple[Any, int]:
        return await self._get(creds, "/documents")

    async def get_documents_delete_commands(self, creds: WmsCredentials) -> tuple[Any, int]:
        return await self._get(creds, "/documents/delete-commands")

    async def create_document(self, creds: WmsCredentials, document: dict) -> tuple[Any, int]:
        return await self._post(creds, "/documents", document)

    async def create_documents(self, creds: WmsCredentials, wrapper: dict) -> tuple[Any, int]:
        return await self._post(creds, "/documents/wrappers", wrapper)

    async def delete_document(self, creds: WmsCredentials, command: dict) -> tuple[Any, int]:
        return await self._post(creds, "/documents/delete-commands", command)

    async def delete_documents(self, creds: WmsCredentials, commands: list[dict]) -> tuple[Any, int]:
        return await self._post(creds, "/documents/delete-commands/list", commands)

    # --- Positions ---

    async def get_positions(self, creds: WmsCredentials) -> tuple[Any, int]:
        return await self._get(creds, "/positions")

    async def get_positions_delete_commands(self, creds: WmsCredentials) -> tuple[Any, int]:
        return await self._get(creds, "/positions/delete-commands")

    async def create_position(self, creds: WmsCredentials, position: dict) -> tuple[Any, int]:
        return await self._post(creds, "/positions", position)

    async def create_positions(self, creds: WmsCredentials, positions: list[dict]) -> tuple[Any, int]:
        return await self._post(creds, "/positions/list", positions)

    async def delete_position(self, creds: WmsCredentials, command: dict) -> tuple[Any, int]:
        return await self._post(creds, "/positions/delete-commands", command)

    async def delete_positions(self, creds: WmsCredentials, commands: list[dict]) -> tuple[Any, int]:
        return await self._post(creds, "/positions/delete-commands/list", commands)

    # --- Contractors ---

    async def get_contractors(self, creds: WmsCredentials) -> tuple[Any, int]:
        return await self._get(creds, "/contractors")

    async def get_contractors_delete_commands(self, creds: WmsCredentials) -> tuple[Any, int]:
        return await self._get(creds, "/contractors/delete-commands")

    async def create_contractor(self, creds: WmsCredentials, contractor: dict) -> tuple[Any, int]:
        return await self._post(creds, "/contractors", contractor)

    async def create_contractors(self, creds: WmsCredentials, contractors: list[dict]) -> tuple[Any, int]:
        return await self._post(creds, "/contractors/list", contractors)

    async def delete_contractor(self, creds: WmsCredentials, command: dict) -> tuple[Any, int]:
        return await self._post(creds, "/contractors/delete-commands", command)

    async def delete_contractors(self, creds: WmsCredentials, commands: list[dict]) -> tuple[Any, int]:
        return await self._post(creds, "/contractors/delete-commands/list", commands)

    # --- Feedback & Errors ---

    async def get_feedbacks(self, creds: WmsCredentials) -> tuple[Any, int]:
        return await self._get(creds, "/feedbacks")

    async def get_errors(self, creds: WmsCredentials) -> tuple[Any, int]:
        return await self._get(creds, "/errors")
