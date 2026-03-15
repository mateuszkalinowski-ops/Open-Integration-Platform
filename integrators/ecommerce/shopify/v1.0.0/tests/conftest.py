"""Test fixtures for Shopify integrator tests."""

from datetime import UTC, datetime
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from src.config import ShopifyAccountConfig
from src.shopify.schemas import (
    ShopifyAddress,
    ShopifyCustomer,
    ShopifyLineItem,
    ShopifyOrder,
    ShopifyOrderFinancialStatus,
    ShopifyOrderFulfillmentStatus,
    ShopifyProduct,
    ShopifyProductVariant,
    ShopifyShippingLine,
)


@pytest.fixture
def sample_account() -> ShopifyAccountConfig:
    return ShopifyAccountConfig(
        name="test-store",
        shop_url="test-store.myshopify.com",
        access_token="shpat_test_token_12345",
        api_version="2024-07",
        default_location_id="12345678",
        default_carrier="TestCarrier",
    )


@pytest.fixture
def sample_shopify_order() -> ShopifyOrder:
    return ShopifyOrder(
        id=1001,
        name="#1001",
        order_number=1001,
        email="jan.kowalski@example.com",
        financial_status=ShopifyOrderFinancialStatus.PAID,
        fulfillment_status=None,
        currency="PLN",
        total_price="199.99",
        subtotal_price="179.99",
        total_tax="0.00",
        total_discounts="0.00",
        customer=ShopifyCustomer(
            id=5001,
            email="jan.kowalski@example.com",
            first_name="Jan",
            last_name="Kowalski",
            phone="+48123456789",
        ),
        shipping_address=ShopifyAddress(
            first_name="Jan",
            last_name="Kowalski",
            company="Firma ABC",
            address1="ul. Testowa 10",
            address2="m. 5",
            city="Warszawa",
            province="mazowieckie",
            country="Poland",
            country_code="PL",
            zip="00-001",
            phone="+48123456789",
        ),
        billing_address=ShopifyAddress(
            first_name="Jan",
            last_name="Kowalski",
            address1="ul. Testowa 10",
            city="Warszawa",
            country="Poland",
            country_code="PL",
            zip="00-001",
        ),
        line_items=[
            ShopifyLineItem(
                id=2001,
                variant_id=3001,
                product_id=4001,
                title="Test Product A",
                sku="SKU-A-001",
                quantity=2,
                price="49.99",
                name="Test Product A",
            ),
            ShopifyLineItem(
                id=2002,
                variant_id=3002,
                product_id=4002,
                title="Test Product B",
                sku="SKU-B-002",
                quantity=1,
                price="100.01",
                name="Test Product B",
            ),
        ],
        shipping_lines=[
            ShopifyShippingLine(
                id=6001,
                title="InPost Paczkomaty",
                price="9.99",
            ),
        ],
        note="Please deliver to paczkomat",
        created_at=datetime(2026, 2, 20, 12, 0, 0, tzinfo=UTC),
        updated_at=datetime(2026, 2, 20, 14, 30, 0, tzinfo=UTC),
    )


@pytest.fixture
def sample_shopify_order_cancelled(sample_shopify_order: ShopifyOrder) -> ShopifyOrder:
    order = sample_shopify_order.model_copy()
    order.cancelled_at = datetime(2026, 2, 21, 10, 0, 0, tzinfo=UTC)
    return order


@pytest.fixture
def sample_shopify_order_fulfilled(sample_shopify_order: ShopifyOrder) -> ShopifyOrder:
    order = sample_shopify_order.model_copy()
    order.fulfillment_status = ShopifyOrderFulfillmentStatus.FULFILLED
    return order


@pytest.fixture
def sample_shopify_order_closed(sample_shopify_order: ShopifyOrder) -> ShopifyOrder:
    order = sample_shopify_order.model_copy()
    order.closed_at = datetime(2026, 2, 22, 8, 0, 0, tzinfo=UTC)
    order.fulfillment_status = ShopifyOrderFulfillmentStatus.FULFILLED
    return order


@pytest.fixture
def sample_shopify_product() -> ShopifyProduct:
    return ShopifyProduct(
        id=4001,
        title="Test Product A",
        body_html="<p>Description of product A</p>",
        vendor="TestVendor",
        product_type="TestType",
        handle="test-product-a",
        status="active",
        tags="tag1, tag2",
        variants=[
            ShopifyProductVariant(
                id=3001,
                product_id=4001,
                title="Default",
                sku="SKU-A-001",
                barcode="5901234567890",
                price="49.99",
                weight=0.5,
                weight_unit="kg",
                inventory_item_id=7001,
                inventory_quantity=100,
            ),
        ],
    )


@pytest.fixture
def sample_shopify_order_raw(sample_shopify_order: ShopifyOrder) -> dict[str, Any]:
    return {"orders": [sample_shopify_order.model_dump(mode="json")]}


@pytest.fixture
def mock_client() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def mock_account_manager(sample_account: ShopifyAccountConfig) -> MagicMock:
    manager = MagicMock()
    manager.get_account.return_value = sample_account
    manager.list_accounts.return_value = [sample_account]
    return manager
