"""Tests for Shoper integrator API routes."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient

from src.api.dependencies import app_state
from src.config import ShoperAccountConfig
from src.main import create_app
from src.services.account_manager import AccountManager
from src.shoper.auth import ShoperAuthManager


@pytest.fixture
def test_app():
    application = create_app()

    account_manager = AccountManager()
    account_manager.add_account(ShoperAccountConfig(
        name="test",
        shop_url="https://test.shoparena.pl",
        login="admin",
        password="pass",
    ))
    app_state.account_manager = account_manager
    app_state.auth_manager = ShoperAuthManager()

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
            "name": "new-shop",
            "shop_url": "https://new.shoparena.pl",
            "login": "admin",
            "password": "secret",
        })
        assert response.status_code == 201
        assert response.json()["name"] == "new-shop"

    def test_remove_account(self, client: TestClient) -> None:
        client.post("/accounts", json={
            "name": "to-remove",
            "shop_url": "https://remove.shoparena.pl",
            "login": "admin",
            "password": "secret",
        })
        response = client.delete("/accounts/to-remove")
        assert response.status_code == 200

    def test_remove_nonexistent_account(self, client: TestClient) -> None:
        response = client.delete("/accounts/nonexistent")
        assert response.status_code == 404


class TestAuthEndpoints:
    def test_auth_status_unauthenticated(self, client: TestClient) -> None:
        response = client.get("/auth/test/status")
        assert response.status_code == 200
        data = response.json()
        assert data["account_name"] == "test"
        assert not data["authenticated"]

    def test_all_auth_statuses(self, client: TestClient) -> None:
        response = client.get("/auth/status")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1


class TestOrderEndpoints:
    def test_get_orders_unknown_account(self, client: TestClient) -> None:
        response = client.get("/orders?account_name=nonexistent")
        assert response.status_code == 404


class TestParcelEndpoints:
    def test_create_parcel_unknown_account(self, client: TestClient) -> None:
        response = client.post(
            "/parcels?account_name=nonexistent",
            json={"order_id": 1},
        )
        assert response.status_code == 404
