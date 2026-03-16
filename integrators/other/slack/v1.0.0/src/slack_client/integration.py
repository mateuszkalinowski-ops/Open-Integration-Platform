"""Slack integration layer — orchestrates Slack Web API operations per account."""

import logging
from typing import Any

import httpx

from src.config import SlackAccountConfig
from src.services.account_manager import AccountManager
from src.slack_client.client import SlackClient
from src.slack_client.schemas import (
    AddReactionRequest,
    AuthStatusResponse,
    FileUploadRequest,
    FileUploadResponse,
    SendMessageRequest,
    SendMessageResponse,
    SlackChannel,
    SlackMessage,
    SlackMessagesPage,
)

logger = logging.getLogger(__name__)


class SlackIntegration:
    """Facade over Slack Web API operations with multi-workspace support."""

    def __init__(self, account_manager: AccountManager):
        self._accounts = account_manager
        self._clients: dict[str, SlackClient] = {}
        self._user_cache: dict[str, str] = {}

    def _get_client(self, account_name: str) -> SlackClient:
        if account_name not in self._clients:
            account = self._require_account(account_name)
            self._clients[account_name] = SlackClient(account.bot_token)
        return self._clients[account_name]

    def _require_account(self, account_name: str) -> SlackAccountConfig:
        account = self._accounts.get_account(account_name)
        if not account:
            raise ValueError(f"Account '{account_name}' not found")
        return account

    async def get_auth_status(self, account_name: str) -> AuthStatusResponse:
        try:
            client = self._get_client(account_name)
            data = await client.auth_test()
            return AuthStatusResponse(
                account_name=account_name,
                authenticated=True,
                bot_user_id=data.get("user_id", ""),
                team_name=data.get("team", ""),
                team_id=data.get("team_id", ""),
            )
        except (httpx.HTTPError, ValueError, KeyError) as exc:
            logger.debug("Auth check failed for account %s: %s", account_name, exc)
            return AuthStatusResponse(account_name=account_name, authenticated=False)

    async def list_channels(
        self,
        account_name: str,
        types: str = "public_channel,private_channel",
        limit: int = 200,
    ) -> list[SlackChannel]:
        client = self._get_client(account_name)
        data = await client.conversations_list(types=types, limit=limit)
        channels: list[SlackChannel] = []
        for ch in data.get("channels", []):
            channels.append(SlackChannel.model_validate(ch))
        return channels

    async def get_channel_history(
        self,
        account_name: str,
        channel: str,
        limit: int = 50,
        oldest: str = "",
        latest: str = "",
    ) -> SlackMessagesPage:
        client = self._get_client(account_name)
        data = await client.conversations_history(channel, limit=limit, oldest=oldest, latest=latest)

        messages: list[SlackMessage] = []
        for msg_data in data.get("messages", []):
            user_name = await self._resolve_user_name(account_name, msg_data.get("user", ""))
            messages.append(
                SlackMessage(
                    channel_id=channel,
                    user_id=msg_data.get("user", ""),
                    user_name=user_name,
                    text=msg_data.get("text", ""),
                    ts=msg_data.get("ts", ""),
                    thread_ts=msg_data.get("thread_ts", ""),
                    reply_count=msg_data.get("reply_count", 0),
                    bot_id=msg_data.get("bot_id", ""),
                    attachments=msg_data.get("attachments", []),
                    blocks=msg_data.get("blocks", []),
                    files=msg_data.get("files", []),
                    account_name=account_name,
                )
            )

        return SlackMessagesPage(
            messages=messages,
            total=len(messages),
            has_more=data.get("has_more", False),
            channel_id=channel,
        )

    async def send_message(
        self,
        account_name: str,
        request: SendMessageRequest,
    ) -> SendMessageResponse:
        client = self._get_client(account_name)
        data = await client.chat_post_message(
            channel=request.channel,
            text=request.text,
            thread_ts=request.thread_ts,
            blocks=request.blocks or None,
            unfurl_links=request.unfurl_links,
            unfurl_media=request.unfurl_media,
        )
        return SendMessageResponse(
            ok=True,
            channel=data.get("channel", ""),
            ts=data.get("ts", ""),
            message_text=request.text,
            account_name=account_name,
        )

    async def add_reaction(
        self,
        account_name: str,
        request: AddReactionRequest,
    ) -> dict[str, Any]:
        client = self._get_client(account_name)
        await client.reactions_add(request.channel, request.timestamp, request.name)
        return {"ok": True, "channel": request.channel, "reaction": request.name}

    async def upload_file(
        self,
        account_name: str,
        request: FileUploadRequest,
    ) -> FileUploadResponse:
        client = self._get_client(account_name)
        data = await client.files_upload_v2(
            channels=request.channels,
            filename=request.filename,
            content_base64=request.content_base64,
            title=request.title,
            initial_comment=request.initial_comment,
        )
        file_data = data.get("file", {})
        return FileUploadResponse(
            ok=True,
            file_id=file_data.get("id", ""),
            file_url=file_data.get("permalink", ""),
        )

    async def _resolve_user_name(self, account_name: str, user_id: str) -> str:
        if not user_id:
            return ""
        cache_key = f"{account_name}:{user_id}"
        if cache_key in self._user_cache:
            return self._user_cache[cache_key]
        try:
            client = self._get_client(account_name)
            data = await client.users_info(user_id)
            name = data.get("user", {}).get("real_name", "") or data.get("user", {}).get("name", "")
            self._user_cache[cache_key] = name
            return name
        except (httpx.HTTPError, ValueError, KeyError) as exc:
            logger.debug("Failed to resolve user %s in account %s: %s", user_id, account_name, exc)
            return ""

    async def close(self) -> None:
        for client in self._clients.values():
            await client.close()
        self._clients.clear()
