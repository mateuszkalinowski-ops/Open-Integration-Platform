"""Tests for BaseLinker integrator API routes."""

import pytest
from fastapi.testclient import TestClient
from src.api.dependencies import app_state
from src.config import BaseLinkerAccountConfig
from src.main import create_app
from src.services.account_manager import AccountManager


@pytest.fixture
def test_app():
    application = create_app()

    account_manager = AccountManager()
    account_manager.add_account(
        BaseLinkerAccountConfig(
            name="test",
            api_token="test-token",
            inventory_id=1,
            warehouse_id=1,
        )
    )
    app_state.account_manager = account_manager

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
        response = client.post(
            "/accounts",
            json={
                "name": "new-account",
                "api_token": "new-token-abc",
                "inventory_id": 2,
                "warehouse_id": 3,
            },
        )
        assert response.status_code == 201
        assert response.json()["name"] == "new-account"

    def test_remove_account(self, client: TestClient) -> None:
        client.post(
            "/accounts",
            json={
                "name": "to-remove",
                "api_token": "temp-token",
            },
        )
        response = client.delete("/accounts/to-remove")
        assert response.status_code == 200

    def test_remove_nonexistent_account(self, client: TestClient) -> None:
        response = client.delete("/accounts/nonexistent")
        assert response.status_code == 404


class TestOrderEndpoints:
    def test_get_orders_unknown_account(self, client: TestClient) -> None:
        response = client.get("/orders?account_name=nonexistent")
        assert response.status_code == 404

    def test_get_order_unknown_account(self, client: TestClient) -> None:
        response = client.get("/orders/123?account_name=nonexistent")
        assert response.status_code == 404


class TestParcelEndpoints:
    def test_create_parcel_unknown_account(self, client: TestClient) -> None:
        response = client.post(
            "/parcels?account_name=nonexistent",
            json={"order_id": 1, "courier_code": "inpost", "package_number": "PK123"},
        )
        assert response.status_code == 404
