"""Tests for Amazon integrator API routes."""

import pytest

from fastapi.testclient import TestClient

from src.api.dependencies import app_state
from src.config import AmazonAccountConfig
from src.main import create_app
from src.services.account_manager import AccountManager


@pytest.fixture
def test_app():
    application = create_app()

    account_manager = AccountManager()
    account_manager.add_account(AmazonAccountConfig(
        name="test",
        client_id="amzn1.test-client",
        client_secret="test-secret",
        refresh_token="Atzr|test-token",
        marketplace_id="A1PA6795UKMFR9",
        region="eu",
    ))
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
        assert data[0]["region"] == "eu"

    def test_add_account(self, client: TestClient) -> None:
        response = client.post("/accounts", json={
            "name": "new-seller",
            "client_id": "amzn1.new-client",
            "client_secret": "new-secret",
            "refresh_token": "Atzr|new-token",
            "marketplace_id": "ATVPDKIKX0DER",
            "region": "na",
        })
        assert response.status_code == 201
        assert response.json()["name"] == "new-seller"

    def test_remove_account(self, client: TestClient) -> None:
        client.post("/accounts", json={
            "name": "to-remove",
            "client_id": "amzn1.temp",
            "client_secret": "temp",
            "refresh_token": "Atzr|temp",
            "marketplace_id": "A1PA6795UKMFR9",
        })
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


class TestProductEndpoints:
    def test_get_product_unknown_account(self, client: TestClient) -> None:
        response = client.get("/products/B0EXAMPLE01?account_name=nonexistent")
        assert response.status_code == 404


class TestStockEndpoints:
    def test_sync_stock_unknown_account(self, client: TestClient) -> None:
        response = client.post(
            "/stock/sync?account_name=nonexistent",
            json={"items": [{"sku": "TEST", "quantity": 10}]},
        )
        assert response.status_code == 404


class TestReportEndpoints:
    def test_create_report_unknown_account(self, client: TestClient) -> None:
        response = client.post(
            "/reports?account_name=nonexistent",
            json={"report_type": "GET_FLAT_FILE_OPEN_LISTINGS_DATA"},
        )
        assert response.status_code == 404

    def test_get_report_unknown_account(self, client: TestClient) -> None:
        response = client.get("/reports/12345?account_name=nonexistent")
        assert response.status_code == 404


class TestFeedEndpoints:
    def test_get_feed_unknown_account(self, client: TestClient) -> None:
        response = client.get("/feeds/12345?account_name=nonexistent")
        assert response.status_code == 404
