"""Slack Web API async HTTP client with retry and rate-limit handling."""

import asyncio
import base64
import logging
import time
from typing import Any

import httpx
from pinquark_common.monitoring.metrics import setup_metrics

from src.config import settings

logger = logging.getLogger(__name__)

SLACK_API_BASE = "https://slack.com/api"

metrics = setup_metrics("slack")


class SlackApiError(Exception):
    def __init__(self, method: str, error: str, raw: dict | None = None):
        self.method = method
        self.error = error
        self.raw = raw or {}
        super().__init__(f"Slack API {method}: {error}")


class SlackClient:
    """Async HTTP client for Slack Web API."""

    def __init__(self, bot_token: str):
        self._token = bot_token
        self._http: httpx.AsyncClient | None = None

    def _get_http(self) -> httpx.AsyncClient:
        if self._http is None or self._http.is_closed:
            self._http = httpx.AsyncClient(
                base_url=SLACK_API_BASE,
                timeout=httpx.Timeout(
                    connect=settings.http_connect_timeout,
                    read=settings.http_read_timeout,
                    write=settings.http_connect_timeout,
                    pool=settings.http_connect_timeout,
                ),
            )
        return self._http

    async def close(self) -> None:
        if self._http and not self._http.is_closed:
            await self._http.aclose()

    async def _call(self, method: str, **kwargs: Any) -> dict[str, Any]:
        """Call a Slack Web API method with automatic retry on rate limiting."""
        http = self._get_http()
        headers = {"Authorization": f"Bearer {self._token}"}

        for attempt in range(settings.max_retries):
            start = time.monotonic()
            response = await http.post(method, headers=headers, **kwargs)
            duration = time.monotonic() - start

            metrics["external_api_calls_total"].labels(
                system="slack",
                operation=method,
                status=response.status_code,
            ).inc()
            metrics["external_api_duration"].labels(
                system="slack",
                operation=method,
            ).observe(duration)

            if response.status_code == 429:
                retry_after = int(response.headers.get("Retry-After", "5"))
                logger.warning("Slack rate limited on %s, waiting %ds", method, retry_after)
                await asyncio.sleep(retry_after)
                continue

            data = response.json()

            if not data.get("ok", False):
                error = data.get("error", "unknown_error")
                if error == "ratelimited":
                    backoff = settings.retry_backoff_factor * (2**attempt)
                    await asyncio.sleep(backoff)
                    continue
                raise SlackApiError(method, error, data)

            return data

        raise SlackApiError(method, f"Failed after {settings.max_retries} retries")

    # --- Auth ---

    async def auth_test(self) -> dict[str, Any]:
        return await self._call("auth.test")

    # --- Channels ---

    async def conversations_list(
        self,
        types: str = "public_channel,private_channel",
        limit: int = 200,
        cursor: str = "",
    ) -> dict[str, Any]:
        params: dict[str, Any] = {"types": types, "limit": limit, "exclude_archived": True}
        if cursor:
            params["cursor"] = cursor
        return await self._call("conversations.list", params=params)

    async def conversations_history(
        self,
        channel: str,
        limit: int = 100,
        oldest: str = "",
        latest: str = "",
    ) -> dict[str, Any]:
        params: dict[str, Any] = {"channel": channel, "limit": limit}
        if oldest:
            params["oldest"] = oldest
        if latest:
            params["latest"] = latest
        return await self._call("conversations.history", params=params)

    async def conversations_info(self, channel: str) -> dict[str, Any]:
        return await self._call("conversations.info", params={"channel": channel})

    # --- Messages ---

    async def chat_post_message(
        self,
        channel: str,
        text: str,
        thread_ts: str = "",
        blocks: list[dict[str, Any]] | None = None,
        unfurl_links: bool = True,
        unfurl_media: bool = True,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "channel": channel,
            "text": text,
            "unfurl_links": unfurl_links,
            "unfurl_media": unfurl_media,
        }
        if thread_ts:
            payload["thread_ts"] = thread_ts
        if blocks:
            payload["blocks"] = blocks
        return await self._call("chat.postMessage", json=payload)

    # --- Reactions ---

    async def reactions_add(self, channel: str, timestamp: str, name: str) -> dict[str, Any]:
        return await self._call(
            "reactions.add",
            json={
                "channel": channel,
                "timestamp": timestamp,
                "name": name,
            },
        )

    # --- Files ---

    async def files_upload_v2(
        self,
        channels: list[str],
        filename: str,
        content_base64: str,
        title: str = "",
        initial_comment: str = "",
    ) -> dict[str, Any]:
        file_bytes = base64.b64decode(content_base64)
        files = {"file": (filename, file_bytes)}
        data: dict[str, Any] = {"filename": filename, "channels": ",".join(channels)}
        if title:
            data["title"] = title
        if initial_comment:
            data["initial_comment"] = initial_comment

        http = self._get_http()
        headers = {"Authorization": f"Bearer {self._token}"}
        response = await http.post("files.upload", headers=headers, data=data, files=files)
        result = response.json()
        if not result.get("ok"):
            raise SlackApiError("files.upload", result.get("error", "unknown"))
        return result

    # --- Users ---

    async def users_info(self, user_id: str) -> dict[str, Any]:
        return await self._call("users.info", params={"user": user_id})
