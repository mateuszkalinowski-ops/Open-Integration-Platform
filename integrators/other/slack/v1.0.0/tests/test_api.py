"""Tests for Slack integrator API routes."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from fastapi.testclient import TestClient

from src.api.dependencies import app_state
from src.config import SlackAccountConfig
from src.slack_client.integration import SlackIntegration
from src.slack_client.schemas import (
    AuthStatusResponse,
    FileUploadResponse,
    SendMessageResponse,
    SlackChannel,
    SlackMessagesPage,
    SlackMessage,
)
from src.main import create_app
from src.services.account_manager import AccountManager


@pytest.fixture
def test_app():
    application = create_app()

    account_manager = AccountManager()
    account_manager.add_account(SlackAccountConfig(
        name="test",
        bot_token="xoxb-test-token",
    ))
    app_state.account_manager = account_manager

    integration = MagicMock(spec=SlackIntegration)
    integration.get_auth_status = AsyncMock(return_value=AuthStatusResponse(
        account_name="test", authenticated=True, bot_user_id="U001", team_name="TestTeam",
    ))
    app_state.integration = integration

    return application


@pytest.fixture
def client(test_app):
    with TestClient(test_app, raise_server_exceptions=False) as c:
        yield c


class TestHealthEndpoints:
    def test_health_returns_ok(self, client: TestClient) -> None:
        response = client.get("/health")
        assert response.status_code == 200

    def test_readiness_returns_ok(self, client: TestClient) -> None:
        response = client.get("/readiness")
        assert response.status_code == 200


class TestAccountEndpoints:
    def test_list_accounts(self, client: TestClient) -> None:
        response = client.get("/accounts")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "test"

    def test_add_account(self, client: TestClient) -> None:
        response = client.post("/accounts", json={
            "name": "new-workspace",
            "bot_token": "xoxb-new-token",
        })
        assert response.status_code == 201
        assert response.json()["name"] == "new-workspace"

    def test_remove_account(self, client: TestClient) -> None:
        client.post("/accounts", json={
            "name": "to-remove",
            "bot_token": "xoxb-remove-token",
        })
        response = client.delete("/accounts/to-remove")
        assert response.status_code == 200

    def test_remove_nonexistent_account(self, client: TestClient) -> None:
        response = client.delete("/accounts/nonexistent")
        assert response.status_code == 404


class TestAuthEndpoints:
    def test_auth_status(self, client: TestClient) -> None:
        response = client.get("/auth/test/status")
        assert response.status_code == 200
        data = response.json()
        assert data["account_name"] == "test"
        assert data["authenticated"]
        assert data["team_name"] == "TestTeam"

    def test_all_auth_statuses(self, client: TestClient) -> None:
        response = client.get("/auth/status")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1

    def test_test_connection(self, client: TestClient) -> None:
        response = client.post("/auth/test/test")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "connected"

    def test_test_connection_unknown_account(self, client: TestClient) -> None:
        response = client.post("/auth/nonexistent/test")
        assert response.status_code == 404


class TestChannelEndpoints:
    def test_list_channels(self, client: TestClient) -> None:
        app_state.integration.list_channels = AsyncMock(return_value=[
            SlackChannel(id="C001", name="general", is_channel=True, num_members=42),
            SlackChannel(id="C002", name="random", is_channel=True, num_members=38),
        ])
        response = client.get("/channels?account_name=test")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["name"] == "general"

    def test_list_channels_unknown_account(self, client: TestClient) -> None:
        response = client.get("/channels?account_name=nonexistent")
        assert response.status_code == 404


class TestMessageEndpoints:
    def test_get_channel_messages(self, client: TestClient) -> None:
        app_state.integration.get_channel_history = AsyncMock(return_value=SlackMessagesPage(
            messages=[
                SlackMessage(channel_id="C001", user_id="U001", text="Hello!", ts="1677000001.000001"),
            ],
            total=1,
            has_more=False,
            channel_id="C001",
        ))
        response = client.get("/messages?account_name=test&channel=C001")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["messages"][0]["text"] == "Hello!"

    def test_send_message(self, client: TestClient) -> None:
        app_state.integration.send_message = AsyncMock(return_value=SendMessageResponse(
            ok=True, channel="C001", ts="1677000003.000003",
            message_text="Test message", account_name="test",
        ))
        response = client.post("/messages/send?account_name=test", json={
            "channel": "C001",
            "text": "Test message",
        })
        assert response.status_code == 200
        assert response.json()["ok"]

    def test_send_message_unknown_account(self, client: TestClient) -> None:
        response = client.post("/messages/send?account_name=nonexistent", json={
            "channel": "C001",
            "text": "Test",
        })
        assert response.status_code == 404


class TestReactionEndpoints:
    def test_add_reaction(self, client: TestClient) -> None:
        app_state.integration.add_reaction = AsyncMock(return_value={
            "ok": True, "channel": "C001", "reaction": "thumbsup",
        })
        response = client.post("/reactions/add?account_name=test", json={
            "channel": "C001",
            "timestamp": "1677000001.000001",
            "name": "thumbsup",
        })
        assert response.status_code == 200
        assert response.json()["ok"]


class TestFileEndpoints:
    def test_upload_file(self, client: TestClient) -> None:
        app_state.integration.upload_file = AsyncMock(return_value=FileUploadResponse(
            ok=True, file_id="F001", file_url="https://files.slack.com/test",
        ))
        response = client.post("/files/upload?account_name=test", json={
            "channels": ["C001"],
            "filename": "test.txt",
            "content_base64": "SGVsbG8gV29ybGQ=",
            "title": "Test File",
        })
        assert response.status_code == 200
        assert response.json()["ok"]
        assert response.json()["file_id"] == "F001"
