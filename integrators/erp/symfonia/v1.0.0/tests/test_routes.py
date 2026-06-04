"""Tests for API routes."""

from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient
from src.api.dependencies import app_state
from src.services.symfonia_client import SymfoniaClient


@pytest.fixture
def mock_symfonia_client():
    client = AsyncMock(spec=SymfoniaClient)
    return client


@pytest.fixture
def test_client(mock_symfonia_client):
    from src.main import app

    with TestClient(app, raise_server_exceptions=False) as client:
        app_state.symfonia_client = mock_symfonia_client
        yield client
    app_state.symfonia_client = None


class TestHealthEndpoints:
    def test_health_returns_healthy(self, test_client):
        app_state.health_checker = None
        resp = test_client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "healthy"


class TestContractorEndpoints:
    def test_list_contractors_returns_paginated(self, test_client, mock_symfonia_client):
        mock_symfonia_client.list_contractors = AsyncMock(
            return_value=[{"Code": "K001"}, {"Code": "K002"}, {"Code": "K003"}]
        )

        resp = test_client.get("/api/v1/contractors?page=1&page_size=2")

        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 3
        assert len(data["items"]) == 2
        assert data["page"] == 1

    def test_get_contractor_by_code(self, test_client, mock_symfonia_client):
        mock_symfonia_client.get_contractor_by_code = AsyncMock(return_value={"Code": "K001", "Name": "Test"})

        resp = test_client.get("/api/v1/contractors/K001")

        assert resp.status_code == 200
        assert resp.json()["Code"] == "K001"

    def test_get_contractor_by_numeric_id(self, test_client, mock_symfonia_client):
        mock_symfonia_client.get_contractor_by_id = AsyncMock(return_value={"Id": 1, "Code": "K001"})

        resp = test_client.get("/api/v1/contractors/1")

        assert resp.status_code == 200
        mock_symfonia_client.get_contractor_by_id.assert_called_once_with(1)

    def test_create_contractor(self, test_client, mock_symfonia_client):
        mock_symfonia_client.create_contractor = AsyncMock(return_value={"Id": 10, "Code": "NEW01"})

        resp = test_client.post("/api/v1/contractors", json={"code": "NEW01", "name": "New Contractor"})

        assert resp.status_code == 200
        mock_symfonia_client.create_contractor.assert_called_once()


class TestProductEndpoints:
    def test_list_products(self, test_client, mock_symfonia_client):
        mock_symfonia_client.list_products = AsyncMock(return_value=[{"Code": "P001"}])

        resp = test_client.get("/api/v1/products")

        assert resp.status_code == 200
        assert resp.json()["total"] == 1


class TestInventoryEndpoints:
    def test_inventory_all(self, test_client, mock_symfonia_client):
        mock_symfonia_client.get_inventory_all = AsyncMock(
            return_value=[{"ProductCode": "P001", "QuantityAvailable": 100}]
        )

        resp = test_client.get("/api/v1/inventory")

        assert resp.status_code == 200
        assert resp.json()["total_products"] == 1

    def test_inventory_by_product(self, test_client, mock_symfonia_client):
        mock_symfonia_client.get_inventory_by_product_code = AsyncMock(
            return_value=[{"WarehouseCode": "MAG1", "QuantityAvailable": 50}]
        )

        resp = test_client.get("/api/v1/inventory/P001")

        assert resp.status_code == 200

    def test_inventory_by_warehouse_code(self, test_client, mock_symfonia_client):
        mock_symfonia_client.get_inventory_by_warehouse_code = AsyncMock(return_value=[])

        resp = test_client.get("/api/v1/inventory?warehouse_code=MAG1")

        assert resp.status_code == 200
        mock_symfonia_client.get_inventory_by_warehouse_code.assert_called_once_with("MAG1")


class TestSalesEndpoints:
    def test_list_sales(self, test_client, mock_symfonia_client):
        mock_symfonia_client.list_sales = AsyncMock(return_value=[])

        resp = test_client.get("/api/v1/sales")

        assert resp.status_code == 200

    def test_filter_sales(self, test_client, mock_symfonia_client):
        mock_symfonia_client.filter_sales = AsyncMock(return_value=[{"Number": "FVS/001"}])

        resp = test_client.get("/api/v1/sales/filter?date_from=2024-01-01&date_to=2024-12-31")

        assert resp.status_code == 200
        assert resp.json()["total"] == 1


class TestOrderEndpoints:
    def test_list_orders(self, test_client, mock_symfonia_client):
        mock_symfonia_client.list_orders = AsyncMock(return_value=[])

        resp = test_client.get("/api/v1/orders")

        assert resp.status_code == 200
