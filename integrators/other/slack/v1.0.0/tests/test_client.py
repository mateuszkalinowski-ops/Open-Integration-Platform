"""Tests for the Slack Web API client."""

from unittest.mock import AsyncMock, patch

import pytest
from src.slack_client.client import SlackApiError, SlackClient


@pytest.fixture
def client():
    return SlackClient(bot_token="xoxb-test-token")


class TestSlackClient:
    @pytest.mark.asyncio
    async def test_auth_test(self, client, slack_auth_test_response):
        with patch.object(client, "_call", new_callable=AsyncMock, return_value=slack_auth_test_response):
            result = await client.auth_test()
            assert result["ok"]
            assert result["team"] == "Test Workspace"
            assert result["user_id"] == "U12345"

    @pytest.mark.asyncio
    async def test_conversations_list(self, client, slack_conversations_list_response):
        with patch.object(client, "_call", new_callable=AsyncMock, return_value=slack_conversations_list_response):
            result = await client.conversations_list()
            assert result["ok"]
            assert len(result["channels"]) == 2
            assert result["channels"][0]["name"] == "general"

    @pytest.mark.asyncio
    async def test_conversations_history(self, client, slack_conversations_history_response):
        with patch.object(client, "_call", new_callable=AsyncMock, return_value=slack_conversations_history_response):
            result = await client.conversations_history("C001")
            assert result["ok"]
            assert len(result["messages"]) == 2
            assert result["messages"][0]["text"] == "Hello, world!"

    @pytest.mark.asyncio
    async def test_chat_post_message(self, client, slack_chat_post_message_response):
        with patch.object(client, "_call", new_callable=AsyncMock, return_value=slack_chat_post_message_response):
            result = await client.chat_post_message("C001", "Test message")
            assert result["ok"]
            assert result["channel"] == "C001"

    @pytest.mark.asyncio
    async def test_reactions_add(self, client, slack_api_response_ok):
        with patch.object(client, "_call", new_callable=AsyncMock, return_value=slack_api_response_ok):
            result = await client.reactions_add("C001", "1677000001.000001", "thumbsup")
            assert result["ok"]

    @pytest.mark.asyncio
    async def test_users_info(self, client, slack_users_info_response):
        with patch.object(client, "_call", new_callable=AsyncMock, return_value=slack_users_info_response):
            result = await client.users_info("U12345")
            assert result["ok"]
            assert result["user"]["real_name"] == "Test User"

    @pytest.mark.asyncio
    async def test_api_error_raises(self, client):
        error_response = {"ok": False, "error": "channel_not_found"}
        with patch.object(
            client,
            "_call",
            new_callable=AsyncMock,
            side_effect=SlackApiError("test", "channel_not_found", error_response),
        ):
            with pytest.raises(SlackApiError) as exc_info:
                await client.conversations_history("INVALID")
            assert "channel_not_found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_close(self, client):
        await client.close()
