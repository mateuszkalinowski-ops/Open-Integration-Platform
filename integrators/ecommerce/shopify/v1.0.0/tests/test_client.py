"""Tests for Shopify HTTP client."""

from unittest.mock import AsyncMock

import pytest
from src.config import ShopifyAccountConfig
from src.shopify.client import ShopifyClient


@pytest.fixture
def account() -> ShopifyAccountConfig:
    return ShopifyAccountConfig(
        name="test-store",
        shop_url="test-store.myshopify.com",
        access_token="shpat_test_token",
        api_version="2024-07",
    )


class TestShopifyClient:
    def test_build_base_url(self, account: ShopifyAccountConfig):
        url = ShopifyClient._build_base_url(account)
        assert url == "https://test-store.myshopify.com/admin/api/2024-07/"

    def test_build_base_url_with_https_prefix(self):
        account = ShopifyAccountConfig(
            name="test",
            shop_url="https://my-store.myshopify.com",
            access_token="token",
        )
        url = ShopifyClient._build_base_url(account)
        assert url == "https://my-store.myshopify.com/admin/api/2024-07/"

    def test_build_base_url_strips_trailing_slash(self):
        account = ShopifyAccountConfig(
            name="test",
            shop_url="my-store.myshopify.com/",
            access_token="token",
        )
        url = ShopifyClient._build_base_url(account)
        assert url == "https://my-store.myshopify.com/admin/api/2024-07/"

    @pytest.mark.asyncio
    async def test_close_clears_clients(self):
        client = ShopifyClient()
        mock_http = AsyncMock()
        client._clients["https://test.myshopify.com"] = mock_http

        await client.close()

        mock_http.aclose.assert_called_once()
        assert len(client._clients) == 0
