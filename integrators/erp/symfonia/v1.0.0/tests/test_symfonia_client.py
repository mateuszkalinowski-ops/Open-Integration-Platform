"""Tests for the Symfonia WebAPI HTTP client."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from src.services.symfonia_client import SymfoniaApiError, SymfoniaClient


@pytest.fixture
def mock_client():
    client = SymfoniaClient(
        base_url="http://localhost:8080",
        application_guid="TEST-GUID",
        device_name="test",
    )
    return client


class TestSymfoniaApiError:
    def test_error_contains_status_and_message(self):
        err = SymfoniaApiError(400, "Bad request", details={"field": "code"})
        assert err.status_code == 400
        assert "Bad request" in str(err)
        assert err.details == {"field": "code"}


class TestSymfoniaClient:
    @pytest.mark.asyncio
    async def test_list_contractors_calls_correct_endpoint(self, mock_client: SymfoniaClient):
        mock_client._request = AsyncMock(return_value=[{"Code": "K001", "Name": "Test"}])

        result = await mock_client.list_contractors()

        mock_client._request.assert_called_once_with("GET", "/api/Contractors", params=None)
        assert len(result) == 1
        assert result[0]["Code"] == "K001"

    @pytest.mark.asyncio
    async def test_get_contractor_by_id(self, mock_client: SymfoniaClient):
        mock_client._request = AsyncMock(return_value={"Id": 1, "Code": "K001"})

        result = await mock_client.get_contractor_by_id(1)

        mock_client._request.assert_called_once_with("GET", "/api/Contractors", params={"id": 1})
        assert result["Id"] == 1

    @pytest.mark.asyncio
    async def test_get_contractor_by_code(self, mock_client: SymfoniaClient):
        mock_client._request = AsyncMock(return_value={"Code": "ABC"})

        result = await mock_client.get_contractor_by_code("ABC")

        mock_client._request.assert_called_once_with("GET", "/api/Contractors", params={"code": "ABC"})

    @pytest.mark.asyncio
    async def test_create_contractor(self, mock_client: SymfoniaClient):
        mock_client._request = AsyncMock(return_value={"Id": 2, "Code": "NEW"})

        result = await mock_client.create_contractor({"Code": "NEW", "Name": "New Contractor"})

        mock_client._request.assert_called_once_with(
            "POST", "/api/Contractors/Create", json_body={"Code": "NEW", "Name": "New Contractor"}
        )

    @pytest.mark.asyncio
    async def test_update_contractor(self, mock_client: SymfoniaClient):
        mock_client._request = AsyncMock(return_value={"Id": 1})

        await mock_client.update_contractor({"Id": 1, "Name": "Updated"})

        mock_client._request.assert_called_once_with(
            "PUT", "/api/Contractors/Update", json_body={"Id": 1, "Name": "Updated"}
        )

    @pytest.mark.asyncio
    async def test_list_products(self, mock_client: SymfoniaClient):
        mock_client._request = AsyncMock(return_value=[{"Code": "P001"}])

        result = await mock_client.list_products()

        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_get_inventory_all(self, mock_client: SymfoniaClient):
        mock_client._request = AsyncMock(return_value=[{"ProductCode": "P001", "QuantityAvailable": 10}])

        result = await mock_client.get_inventory_all()

        mock_client._request.assert_called_once_with("GET", "/api/InventoryStates", params=None)

    @pytest.mark.asyncio
    async def test_get_inventory_by_warehouse_code(self, mock_client: SymfoniaClient):
        mock_client._request = AsyncMock(return_value=[])

        await mock_client.get_inventory_by_warehouse_code("MAG1")

        mock_client._request.assert_called_once_with("GET", "/api/InventoryStates/ByWarehouse", params={"code": "MAG1"})

    @pytest.mark.asyncio
    async def test_filter_sales(self, mock_client: SymfoniaClient):
        mock_client._request = AsyncMock(return_value=[])

        await mock_client.filter_sales("2024-01-01", "2024-12-31", buyer_code="K001")

        mock_client._request.assert_called_once_with(
            "GET",
            "/api/Sales/Filter",
            params={"dateFrom": "2024-01-01", "dateTo": "2024-12-31", "buyerCode": "K001"},
        )

    @pytest.mark.asyncio
    async def test_filter_orders_with_recipient(self, mock_client: SymfoniaClient):
        mock_client._request = AsyncMock(return_value=[])

        await mock_client.filter_orders("2024-01-01", "2024-06-30", recipient_code="K002")

        mock_client._request.assert_called_once_with(
            "GET",
            "/api/Orders/Filter",
            params={"dateFrom": "2024-01-01", "dateTo": "2024-06-30", "recipientCode": "K002"},
        )

    @pytest.mark.asyncio
    async def test_sync_contractors(self, mock_client: SymfoniaClient):
        mock_client._request = AsyncMock(return_value=[{"Code": "K001", "IsDeleted": False}])

        result = await mock_client.sync_contractors("2024-01-01")

        mock_client._request.assert_called_once_with(
            "GET", "/api/Contractors/IncrementalSync", params={"dateFrom": "2024-01-01"}
        )

    @pytest.mark.asyncio
    async def test_inventory_changes(self, mock_client: SymfoniaClient):
        mock_client._request = AsyncMock(return_value=[])

        await mock_client.get_inventory_changes()

        mock_client._request.assert_called_once_with("GET", "/api/InventoryStates/Changes", params=None)

    @pytest.mark.asyncio
    async def test_ping(self, mock_client: SymfoniaClient):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"modules": ["Handel"]}
        mock_resp.raise_for_status = MagicMock()

        mock_client._session._client = AsyncMock()
        mock_client._session._client.get = AsyncMock(return_value=mock_resp)

        result = await mock_client.ping()

        assert result == {"modules": ["Handel"]}
