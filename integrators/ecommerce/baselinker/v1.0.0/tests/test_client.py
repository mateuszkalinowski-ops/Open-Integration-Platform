"""Tests for BaseLinker API client."""

import httpx
import pytest
import respx
from src.baselinker.client import BaseLinkerApiError, BaseLinkerClient
from src.config import BaseLinkerAccountConfig


@pytest.fixture
def account() -> BaseLinkerAccountConfig:
    return BaseLinkerAccountConfig(
        name="test",
        api_token="test-token-123",
        inventory_id=1,
        warehouse_id=1,
    )


@pytest.fixture
def client() -> BaseLinkerClient:
    return BaseLinkerClient()


class TestBaseLinkerClient:
    @respx.mock
    @pytest.mark.asyncio
    async def test_call_sends_correct_method(self, client: BaseLinkerClient, account: BaseLinkerAccountConfig) -> None:
        respx.post("https://api.baselinker.com/connector.php").mock(
            return_value=httpx.Response(200, json={"status": "SUCCESS", "orders": []})
        )

        result = await client.call("getOrders", account, {"date_from": 0})

        assert result["status"] == "SUCCESS"
        request = respx.calls.last.request
        assert request.headers["X-BLToken"] == "test-token-123"
        await client.close()

    @respx.mock
    @pytest.mark.asyncio
    async def test_call_raises_on_api_error(self, client: BaseLinkerClient, account: BaseLinkerAccountConfig) -> None:
        respx.post("https://api.baselinker.com/connector.php").mock(
            return_value=httpx.Response(
                200,
                json={
                    "status": "ERROR",
                    "error_code": "ERROR_INVALID_TOKEN",
                    "error_message": "Invalid API token",
                },
            )
        )

        with pytest.raises(BaseLinkerApiError) as exc_info:
            await client.call("getOrders", account)

        assert "Invalid API token" in str(exc_info.value)
        assert exc_info.value.error_code == "ERROR_INVALID_TOKEN"
        await client.close()

    @respx.mock
    @pytest.mark.asyncio
    async def test_get_orders_calls_correct_method(
        self,
        client: BaseLinkerClient,
        account: BaseLinkerAccountConfig,
    ) -> None:
        respx.post("https://api.baselinker.com/connector.php").mock(
            return_value=httpx.Response(200, json={"status": "SUCCESS", "orders": []})
        )

        result = await client.get_orders(account, date_confirmed_from=1708000000)
        assert result["status"] == "SUCCESS"
        await client.close()

    @respx.mock
    @pytest.mark.asyncio
    async def test_set_order_status(self, client: BaseLinkerClient, account: BaseLinkerAccountConfig) -> None:
        respx.post("https://api.baselinker.com/connector.php").mock(
            return_value=httpx.Response(200, json={"status": "SUCCESS"})
        )

        result = await client.set_order_status(account, 77001, 12346)
        assert result["status"] == "SUCCESS"
        await client.close()

    @respx.mock
    @pytest.mark.asyncio
    async def test_update_stock(self, client: BaseLinkerClient, account: BaseLinkerAccountConfig) -> None:
        respx.post("https://api.baselinker.com/connector.php").mock(
            return_value=httpx.Response(
                200,
                json={
                    "status": "SUCCESS",
                    "warnings": {},
                    "counter": 1,
                },
            )
        )

        result = await client.update_inventory_products_stock(
            account,
            1,
            {"5001": {"1": 100.0}},
        )
        assert result["status"] == "SUCCESS"
        await client.close()

    @respx.mock
    @pytest.mark.asyncio
    async def test_get_order_status_list(self, client: BaseLinkerClient, account: BaseLinkerAccountConfig) -> None:
        respx.post("https://api.baselinker.com/connector.php").mock(
            return_value=httpx.Response(
                200,
                json={
                    "status": "SUCCESS",
                    "statuses": [
                        {"id": 12345, "name": "Nowe", "name_for_customer": "New", "color": "#00FF00"},
                    ],
                },
            )
        )

        result = await client.get_order_status_list(account)
        assert len(result["statuses"]) == 1
        assert result["statuses"][0]["name"] == "Nowe"
        await client.close()

    @respx.mock
    @pytest.mark.asyncio
    async def test_create_package_manual(self, client: BaseLinkerClient, account: BaseLinkerAccountConfig) -> None:
        respx.post("https://api.baselinker.com/connector.php").mock(
            return_value=httpx.Response(200, json={"status": "SUCCESS", "order_id": 77001})
        )

        result = await client.create_package_manual(account, 77001, "inpost", "PK12345678")
        assert result["status"] == "SUCCESS"
        await client.close()
