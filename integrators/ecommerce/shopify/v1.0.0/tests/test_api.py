"""Tests for Shopify integrator API routes."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient
from pinquark_common.schemas.common import SyncResult, SyncStatus
from pinquark_common.schemas.ecommerce import Order, OrdersPage, OrderStatus, Product
from src.api.dependencies import app_state
from src.config import ShopifyAccountConfig
from src.main import create_app


@pytest.fixture
def test_account() -> ShopifyAccountConfig:
    return ShopifyAccountConfig(
        name="test-store",
        shop_url="test-store.myshopify.com",
        access_token="shpat_test_123",
        api_version="2024-07",
        default_location_id="12345678",
    )


@pytest.fixture
def mock_state(test_account: ShopifyAccountConfig) -> None:
    app_state.auth_manager = MagicMock()
    app_state.auth_manager.is_authenticated.return_value = True
    app_state.auth_manager.get_status.return_value = MagicMock(
        account_name="test-store",
        authenticated=True,
        shop_url="test-store.myshopify.com",
        api_version="2024-07",
    )

    app_state.account_manager = MagicMock()
    app_state.account_manager.get_account.return_value = test_account
    app_state.account_manager.list_accounts.return_value = [test_account]

    app_state.integration = AsyncMock()
    app_state.health_checker = None


@pytest.fixture
def client(mock_state: None) -> TestClient:
    application = create_app()
    application.router.lifespan_context = None  # type: ignore[assignment]
    return TestClient(application, raise_server_exceptions=False)


class TestHealthEndpoints:
    def test_health_returns_ok(self, client: TestClient):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

    def test_readiness_returns_ok(self, client: TestClient):
        response = client.get("/readiness")
        assert response.status_code == 200


class TestAccountEndpoints:
    def test_list_accounts(self, client: TestClient):
        response = client.get("/accounts")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "test-store"

    def test_add_account(self, client: TestClient):
        response = client.post(
            "/accounts",
            json={
                "name": "new-store",
                "shop_url": "new-store.myshopify.com",
                "access_token": "shpat_new_123",
            },
        )
        assert response.status_code == 201
        assert response.json()["name"] == "new-store"

    def test_remove_account(self, client: TestClient):
        app_state.account_manager.remove_account.return_value = True
        response = client.delete("/accounts/test-store")
        assert response.status_code == 200
        assert response.json()["status"] == "removed"

    def test_remove_nonexistent_account(self, client: TestClient):
        app_state.account_manager.remove_account.return_value = False
        response = client.delete("/accounts/nonexistent")
        assert response.status_code == 404


class TestOrderEndpoints:
    def test_list_orders(self, client: TestClient):
        app_state.integration.fetch_orders.return_value = OrdersPage(
            orders=[
                Order(external_id="1001", account_name="test-store", status=OrderStatus.NEW),
            ],
            page=1,
            total=1,
            has_next=False,
        )
        response = client.get("/orders?account_name=test-store")
        assert response.status_code == 200
        data = response.json()
        assert len(data["orders"]) == 1
        assert data["orders"][0]["external_id"] == "1001"

    def test_get_order(self, client: TestClient):
        app_state.integration.get_order.return_value = Order(
            external_id="1001",
            account_name="test-store",
            status=OrderStatus.NEW,
        )
        response = client.get("/orders/1001?account_name=test-store")
        assert response.status_code == 200
        assert response.json()["external_id"] == "1001"

    def test_update_order_status(self, client: TestClient):
        app_state.integration.update_order_status.return_value = None
        response = client.put(
            "/orders/1001/status?account_name=test-store",
            json={
                "status": "SHIPPED",
                "tracking_number": "TRACK123",
                "tracking_company": "DHL",
            },
        )
        assert response.status_code == 200
        assert response.json()["status"] == "updated"

    def test_fulfill_order(self, client: TestClient):
        app_state.integration.update_order_status.return_value = None
        response = client.post(
            "/orders/1001/fulfill?account_name=test-store",
            json={
                "tracking_number": "TRACK456",
                "tracking_company": "InPost",
            },
        )
        assert response.status_code == 200
        assert response.json()["status"] == "fulfilled"

    def test_orders_require_auth(self, client: TestClient):
        app_state.auth_manager.is_authenticated.return_value = False
        response = client.get("/orders?account_name=test-store")
        assert response.status_code == 401


class TestStockEndpoints:
    def test_sync_stock(self, client: TestClient):
        app_state.integration.sync_stock.return_value = SyncResult(
            status=SyncStatus.SUCCESS,
            total=2,
            succeeded=2,
            failed=0,
        )
        response = client.post(
            "/stock/sync?account_name=test-store",
            json={
                "items": [
                    {"sku": "SKU-A", "quantity": 50, "product_id": "7001"},
                    {"sku": "SKU-B", "quantity": 30, "product_id": "7002"},
                ],
            },
        )
        assert response.status_code == 200
        assert response.json()["status"] == "SUCCESS"
        assert response.json()["succeeded"] == 2


class TestProductEndpoints:
    def test_get_product(self, client: TestClient):
        app_state.integration.get_product.return_value = Product(
            external_id="4001",
            name="Test Product",
            sku="SKU-A",
        )
        response = client.get("/products/4001?account_name=test-store")
        assert response.status_code == 200
        assert response.json()["external_id"] == "4001"

    def test_sync_products(self, client: TestClient):
        app_state.integration.sync_products.return_value = SyncResult(
            status=SyncStatus.SUCCESS,
            total=1,
            succeeded=1,
            failed=0,
        )
        response = client.post(
            "/products/sync?account_name=test-store",
            json={
                "products": [{"external_id": "0", "name": "New Product", "sku": "NEW-SKU"}],
            },
        )
        assert response.status_code == 200
        assert response.json()["status"] == "SUCCESS"
