"""Tests for Email Client integrator API routes."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient
from src.api.dependencies import app_state
from src.config import EmailAccountConfig
from src.email_client.integration import EmailIntegration
from src.email_client.schemas import (
    AuthStatusResponse,
    ConnectionStatus,
    EmailsPage,
    FolderInfo,
    SendEmailResponse,
)
from src.main import create_app
from src.services.account_manager import AccountManager


@pytest.fixture
def test_app():
    application = create_app()

    account_manager = AccountManager()
    account_manager.add_account(
        EmailAccountConfig(
            name="test",
            email_address="test@example.com",
            password="pass",
            imap_host="imap.example.com",
            smtp_host="smtp.example.com",
        )
    )
    app_state.account_manager = account_manager

    integration = MagicMock(spec=EmailIntegration)
    integration.get_auth_status.return_value = AuthStatusResponse(
        account_name="test",
        imap_connected=False,
        smtp_connected=False,
    )
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
        assert data[0]["email_address"] == "test@example.com"

    def test_add_account(self, client: TestClient) -> None:
        response = client.post(
            "/accounts",
            json={
                "name": "new-account",
                "email_address": "new@example.com",
                "password": "secret",
                "imap_host": "imap.example.com",
                "smtp_host": "smtp.example.com",
            },
        )
        assert response.status_code == 201
        assert response.json()["name"] == "new-account"

    def test_remove_account(self, client: TestClient) -> None:
        client.post(
            "/accounts",
            json={
                "name": "to-remove",
                "email_address": "remove@example.com",
                "password": "secret",
                "imap_host": "imap.example.com",
                "smtp_host": "smtp.example.com",
            },
        )
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
        assert not data["imap_connected"]

    def test_all_auth_statuses(self, client: TestClient) -> None:
        response = client.get("/auth/status")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1


class TestEmailEndpoints:
    def test_list_emails_unknown_account(self, client: TestClient) -> None:
        response = client.get("/emails?account_name=nonexistent")
        assert response.status_code == 404

    def test_list_emails(self, client: TestClient) -> None:
        app_state.integration.fetch_emails = AsyncMock(
            return_value=EmailsPage(
                emails=[],
                total=0,
                page=1,
                page_size=50,
                folder="INBOX",
            )
        )
        response = client.get("/emails?account_name=test")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["folder"] == "INBOX"

    def test_get_email_not_found(self, client: TestClient) -> None:
        app_state.integration.get_email = AsyncMock(return_value=None)
        response = client.get("/emails/123?account_name=test")
        assert response.status_code == 404

    def test_send_email(self, client: TestClient) -> None:
        app_state.integration.send_email = AsyncMock(
            return_value=SendEmailResponse(
                status="sent",
                message_id="<test@example.com>",
                account_name="test",
            )
        )
        response = client.post(
            "/emails/send?account_name=test",
            json={
                "to": ["recipient@example.com"],
                "subject": "Test",
                "body_text": "Hello",
            },
        )
        assert response.status_code == 200
        assert response.json()["status"] == "sent"

    def test_mark_as_read(self, client: TestClient) -> None:
        app_state.integration.mark_as_read = AsyncMock(return_value=True)
        response = client.put("/emails/123/read?account_name=test")
        assert response.status_code == 200
        assert response.json()["status"] == "marked_read"

    def test_mark_as_read_failure(self, client: TestClient) -> None:
        app_state.integration.mark_as_read = AsyncMock(return_value=False)
        response = client.put("/emails/123/read?account_name=test")
        assert response.status_code == 500

    def test_delete_email(self, client: TestClient) -> None:
        app_state.integration.delete_email = AsyncMock(return_value=True)
        response = client.delete("/emails/123?account_name=test")
        assert response.status_code == 200
        assert response.json()["status"] == "deleted"

    def test_delete_email_failure(self, client: TestClient) -> None:
        app_state.integration.delete_email = AsyncMock(return_value=False)
        response = client.delete("/emails/123?account_name=test")
        assert response.status_code == 500


class TestFolderEndpoints:
    def test_list_folders(self, client: TestClient) -> None:
        app_state.integration.list_folders = AsyncMock(
            return_value=[
                FolderInfo(name="INBOX", delimiter="/"),
                FolderInfo(name="Sent", delimiter="/"),
            ]
        )
        response = client.get("/folders?account_name=test")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["name"] == "INBOX"

    def test_list_folders_unknown_account(self, client: TestClient) -> None:
        response = client.get("/folders?account_name=nonexistent")
        assert response.status_code == 404


class TestConnectionEndpoint:
    def test_connection_status(self, client: TestClient) -> None:
        app_state.integration.get_connection_status = AsyncMock(
            return_value=ConnectionStatus(
                account_name="test",
                imap_connected=True,
                smtp_connected=True,
            ),
        )
        response = client.get("/connection/test/status")
        assert response.status_code == 200
        data = response.json()
        assert data["imap_connected"]
        assert data["smtp_connected"]

    def test_connection_status_unknown_account(self, client: TestClient) -> None:
        response = client.get("/connection/nonexistent/status")
        assert response.status_code == 404
