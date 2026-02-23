"""Tests for IdoSell FastAPI routes."""

import pytest
from httpx import ASGITransport, AsyncClient

from pinquark_common.schemas.ecommerce import Order, OrdersPage, OrderStatus, Product
from src.main import create_app


@pytest.fixture
def app(mock_app_state):  # type: ignore[no-untyped-def]
    return create_app()


@pytest.fixture
async def client(app):  # type: ignore[no-untyped-def]
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


class TestHealthEndpoints:
    async def test_health_returns_ok(self, client: AsyncClient) -> None:
        response = await client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"


class TestAccountEndpoints:
    async def test_list_accounts(self, client: AsyncClient) -> None:
        response = await client.get("/accounts")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "test-shop"

    async def test_add_account(self, client: AsyncClient) -> None:
        response = await client.post("/accounts", json={
            "name": "new-shop",
            "shop_url": "https://new.idosell.com",
            "api_key": "key123",
        })
        assert response.status_code == 201
        assert response.json()["status"] == "created"


class TestOrderEndpoints:
    async def test_list_orders(self, client: AsyncClient, mock_integration) -> None:  # type: ignore[no-untyped-def]
        mock_integration.fetch_orders.return_value = OrdersPage(
            orders=[],
            page=1,
            total=0,
            has_next=False,
        )
        response = await client.get("/orders?account_name=test-shop")
        assert response.status_code == 200
        assert response.json()["total"] == 0

    async def test_get_order(self, client: AsyncClient, mock_integration) -> None:  # type: ignore[no-untyped-def]
        mock_integration.get_order.return_value = Order(
            external_id="ORD-001",
            account_name="test-shop",
            status=OrderStatus.NEW,
        )
        response = await client.get("/orders/ORD-001?account_name=test-shop")
        assert response.status_code == 200
        assert response.json()["external_id"] == "ORD-001"

    async def test_update_status(self, client: AsyncClient, mock_integration) -> None:  # type: ignore[no-untyped-def]
        mock_integration.update_order_status.return_value = None
        response = await client.put(
            "/orders/12345/status?account_name=test-shop",
            json={"status": "SHIPPED"},
        )
        assert response.status_code == 200
        assert response.json()["status"] == "updated"


class TestStockEndpoints:
    async def test_sync_stock(self, client: AsyncClient, mock_integration) -> None:  # type: ignore[no-untyped-def]
        from pinquark_common.schemas.common import SyncResult, SyncStatus
        mock_integration.sync_stock.return_value = SyncResult(
            status=SyncStatus.SUCCESS,
            total=1,
            succeeded=1,
            failed=0,
        )
        response = await client.post(
            "/stock/sync?account_name=test-shop",
            json={"items": [{"sku": "POLO-001", "quantity": 100}]},
        )
        assert response.status_code == 200
        assert response.json()["status"] == "success"


class TestProductEndpoints:
    async def test_get_product(self, client: AsyncClient, mock_integration) -> None:  # type: ignore[no-untyped-def]
        mock_integration.get_product.return_value = Product(
            external_id="100",
            sku="POLO-001",
            name="Koszulka Polo",
        )
        response = await client.get("/products/100?account_name=test-shop")
        assert response.status_code == 200
        assert response.json()["sku"] == "POLO-001"


class TestParcelEndpoints:
    async def test_create_parcel(self, client: AsyncClient, mock_integration) -> None:  # type: ignore[no-untyped-def]
        mock_integration.create_parcel.return_value = {"status": "created"}
        response = await client.post(
            "/parcels?account_name=test-shop",
            json={
                "order_serial_number": 12345,
                "courier_id": 1,
                "tracking_numbers": ["TRACK001"],
            },
        )
        assert response.status_code == 201
