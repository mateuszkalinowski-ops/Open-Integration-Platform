"""Tests for KSeF FastAPI routes."""

import pytest
from fastapi.testclient import TestClient
from src.api.dependencies import app_state
from src.main import create_app
from src.services.account_manager import AccountManager


@pytest.fixture
def account_manager() -> AccountManager:
    mgr = AccountManager()
    mgr.add_account(
        {
            "name": "test-account",
            "nip": "1234567890",
            "ksef_token": "test-token",
            "environment": "test",
        }
    )
    return mgr


@pytest.fixture
def client(account_manager: AccountManager) -> TestClient:
    app = create_app()
    app_state.account_manager = account_manager
    app_state.health_checker = None
    return TestClient(app, raise_server_exceptions=False)


class TestHealthEndpoint:
    def test_health_returns_ok(self, client: TestClient) -> None:
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_readiness_returns_ok(self, client: TestClient) -> None:
        response = client.get("/readiness")
        assert response.status_code == 200


class TestAccountsEndpoint:
    def test_list_accounts(self, client: TestClient) -> None:
        response = client.get("/accounts")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "test-account"
        assert "****" in data[0]["nip"]

    def test_create_account(self, client: TestClient) -> None:
        response = client.post(
            "/accounts",
            json={
                "name": "new-account",
                "nip": "9876543210",
                "ksef_token": "new-token",
                "environment": "demo",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "new-account"
        assert data["environment"] == "demo"

    def test_delete_account(self, client: TestClient) -> None:
        response = client.delete("/accounts/test-account")
        assert response.status_code == 200

    def test_list_accounts_after_create(self, client: TestClient) -> None:
        client.post(
            "/accounts",
            json={
                "name": "second",
                "nip": "5555555555",
                "environment": "production",
            },
        )
        response = client.get("/accounts")
        assert response.status_code == 200
        names = [a["name"] for a in response.json()]
        assert "second" in names

    def test_update_account_replaces_credentials(self, client: TestClient, account_manager: AccountManager) -> None:
        response = client.put(
            "/accounts/test-account",
            json={"name": "ignored", "nip": "5273148508", "ksef_token": "new-token", "environment": "production"},
        )
        assert response.status_code == 200
        assert response.json()["name"] == "test-account"
        account = account_manager.get_account("test-account")
        assert account.nip == "5273148508"
        assert account.ksef_token == "new-token"
        assert account.environment.value == "production"

    def test_update_account_creates_missing_account(self, client: TestClient, account_manager: AccountManager) -> None:
        response = client.put(
            "/accounts/meritus",
            json={"name": "meritus", "nip": "5273148508", "ksef_token": "t", "environment": "demo"},
        )
        assert response.status_code == 200
        assert account_manager.get_account("meritus").nip == "5273148508"

    def test_whitespace_is_stripped_from_nip_and_token(
        self, client: TestClient, account_manager: AccountManager
    ) -> None:
        response = client.post(
            "/accounts",
            json={
                "name": "spaces",
                "nip": " 527 314 8508\n",
                "ksef_token": "  tok|nip-5273148508|abc \n",
                "environment": "demo",
            },
        )
        assert response.status_code == 201
        account = account_manager.get_account("spaces")
        assert account.nip == "5273148508"
        assert account.ksef_token == "tok|nip-5273148508|abc"


class TestAuthEndpoint:
    def test_auth_with_unknown_account_returns_404(self, client: TestClient) -> None:
        response = client.post(
            "/auth/token",
            json={
                "account_name": "nonexistent",
            },
        )
        assert response.status_code == 404


class TestInvoiceEndpoints:
    def test_send_invoice_missing_data_returns_400(self, client: TestClient) -> None:
        response = client.post(
            "/invoices",
            json={
                "account_name": "test-account",
                "reference_number": "test-ref",
            },
        )
        assert response.status_code == 400

    def test_get_invoice_unknown_account_returns_404(self, client: TestClient) -> None:
        response = client.get("/invoices/some-ref?account_name=nonexistent")
        assert response.status_code == 404

    def test_get_invoice_pdf_unknown_account_returns_404(self, client: TestClient) -> None:
        response = client.get("/invoices/some-ref/pdf?account_name=nonexistent")
        assert response.status_code == 404


class TestSessionEndpoints:
    def test_close_session_unknown_account_returns_404(self, client: TestClient) -> None:
        response = client.post("/sessions/test-ref/close?account_name=nonexistent")
        assert response.status_code == 404

    def test_get_session_status_unknown_account_returns_404(self, client: TestClient) -> None:
        response = client.get("/sessions/test-ref?account_name=nonexistent")
        assert response.status_code == 404
