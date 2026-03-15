"""Tests for Apilo integrator API routes."""

import pytest
from fastapi.testclient import TestClient
from src.api.dependencies import app_state
from src.config import ApiloAccountConfig
from src.main import create_app
from src.services.account_manager import AccountManager


@pytest.fixture
def test_app():
    application = create_app()

    account_manager = AccountManager()
    account_manager.add_account(
        ApiloAccountConfig(
            name="test",
            client_id="test-client-id",
            client_secret="test-secret",
            authorization_code="test-code",
            base_url="https://test.apilo.com",
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
        assert data[0]["base_url"] == "https://test.apilo.com"

    def test_add_account(self, client: TestClient) -> None:
        response = client.post(
            "/accounts",
            json={
                "name": "new-account",
                "client_id": "new-client-id",
                "client_secret": "new-secret",
                "authorization_code": "new-code",
                "base_url": "https://new.apilo.com",
            },
        )
        assert response.status_code == 201
        assert response.json()["name"] == "new-account"

    def test_remove_account(self, client: TestClient) -> None:
        client.post(
            "/accounts",
            json={
                "name": "to-remove",
                "client_id": "temp-id",
                "client_secret": "temp-secret",
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
        response = client.get("/orders/AL231100017?account_name=nonexistent")
        assert response.status_code == 404


class TestProductEndpoints:
    def test_get_product_unknown_account(self, client: TestClient) -> None:
        response = client.get("/products/1234?account_name=nonexistent")
        assert response.status_code == 404

    def test_list_products_unknown_account(self, client: TestClient) -> None:
        response = client.get("/products?account_name=nonexistent")
        assert response.status_code == 404


class TestStockEndpoints:
    def test_sync_stock_unknown_account(self, client: TestClient) -> None:
        response = client.post(
            "/stock/sync?account_name=nonexistent",
            json={"items": [{"sku": "TEST", "quantity": 10}]},
        )
        assert response.status_code == 404


class TestShipmentEndpoints:
    def test_get_shipment_unknown_account(self, client: TestClient) -> None:
        response = client.get("/shipments/123?account_name=nonexistent")
        assert response.status_code == 404


class TestMapsEndpoint:
    def test_get_maps_unknown_account(self, client: TestClient) -> None:
        response = client.get("/maps?account_name=nonexistent")
        assert response.status_code == 404
