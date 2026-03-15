"""Tests for Shopify → unified schema mapper."""

from datetime import UTC, datetime

from pinquark_common.schemas.ecommerce import OrderStatus, Product
from src.shopify.mapper import (
    map_product_to_shopify,
    map_shopify_order_status,
    map_shopify_order_to_order,
    map_shopify_product_to_product,
)
from src.shopify.schemas import (
    ShopifyOrder,
    ShopifyOrderFulfillmentStatus,
    ShopifyProduct,
)


class TestMapShopifyOrderStatus:
    def test_new_order_unfulfilled(self, sample_shopify_order: ShopifyOrder):
        assert map_shopify_order_status(sample_shopify_order) == OrderStatus.NEW

    def test_cancelled_order(self, sample_shopify_order_cancelled: ShopifyOrder):
        assert map_shopify_order_status(sample_shopify_order_cancelled) == OrderStatus.CANCELLED

    def test_fulfilled_order(self, sample_shopify_order_fulfilled: ShopifyOrder):
        assert map_shopify_order_status(sample_shopify_order_fulfilled) == OrderStatus.SHIPPED

    def test_closed_and_fulfilled_order(self, sample_shopify_order_closed: ShopifyOrder):
        assert map_shopify_order_status(sample_shopify_order_closed) == OrderStatus.DELIVERED

    def test_partially_fulfilled_order(self, sample_shopify_order: ShopifyOrder):
        sample_shopify_order.fulfillment_status = ShopifyOrderFulfillmentStatus.PARTIAL
        assert map_shopify_order_status(sample_shopify_order) == OrderStatus.PROCESSING

    def test_closed_but_not_fulfilled(self, sample_shopify_order: ShopifyOrder):
        sample_shopify_order.closed_at = datetime(2026, 2, 22, tzinfo=UTC)
        sample_shopify_order.fulfillment_status = None
        assert map_shopify_order_status(sample_shopify_order) == OrderStatus.SHIPPED


class TestMapShopifyOrderToOrder:
    def test_maps_basic_fields(self, sample_shopify_order: ShopifyOrder):
        order = map_shopify_order_to_order(sample_shopify_order, "test-store")

        assert order.external_id == "1001"
        assert order.account_name == "test-store"
        assert order.status == OrderStatus.NEW
        assert order.total_amount == 199.99
        assert order.currency == "PLN"
        assert order.notes == "Please deliver to paczkomat"

    def test_maps_buyer(self, sample_shopify_order: ShopifyOrder):
        order = map_shopify_order_to_order(sample_shopify_order, "test-store")

        assert order.buyer is not None
        assert order.buyer.external_id == "5001"
        assert order.buyer.email == "jan.kowalski@example.com"
        assert order.buyer.first_name == "Jan"
        assert order.buyer.last_name == "Kowalski"
        assert order.buyer.is_guest is False

    def test_maps_delivery_address(self, sample_shopify_order: ShopifyOrder):
        order = map_shopify_order_to_order(sample_shopify_order, "test-store")

        assert order.delivery_address is not None
        assert order.delivery_address.first_name == "Jan"
        assert order.delivery_address.last_name == "Kowalski"
        assert order.delivery_address.company_name == "Firma ABC"
        assert order.delivery_address.street == "ul. Testowa 10, m. 5"
        assert order.delivery_address.city == "Warszawa"
        assert order.delivery_address.postal_code == "00-001"
        assert order.delivery_address.country_code == "PL"

    def test_maps_line_items(self, sample_shopify_order: ShopifyOrder):
        order = map_shopify_order_to_order(sample_shopify_order, "test-store")

        assert len(order.lines) == 2
        assert order.lines[0].sku == "SKU-A-001"
        assert order.lines[0].quantity == 2.0
        assert order.lines[0].unit_price == 49.99
        assert order.lines[0].product_id == "4001"
        assert order.lines[1].sku == "SKU-B-002"
        assert order.lines[1].quantity == 1.0

    def test_maps_delivery_method(self, sample_shopify_order: ShopifyOrder):
        order = map_shopify_order_to_order(sample_shopify_order, "test-store")
        assert order.delivery_method == "InPost Paczkomaty"

    def test_maps_timestamps(self, sample_shopify_order: ShopifyOrder):
        order = map_shopify_order_to_order(sample_shopify_order, "test-store")
        assert order.created_at == datetime(2026, 2, 20, 12, 0, 0, tzinfo=UTC)
        assert order.updated_at == datetime(2026, 2, 20, 14, 30, 0, tzinfo=UTC)

    def test_preserves_raw_data(self, sample_shopify_order: ShopifyOrder):
        order = map_shopify_order_to_order(sample_shopify_order, "test-store")
        assert order.raw_data is not None
        assert order.raw_data["id"] == 1001

    def test_guest_buyer_without_customer(self):
        order = ShopifyOrder(
            id=9999,
            name="#9999",
            email="guest@example.com",
            total_price="10.00",
            currency="PLN",
        )
        mapped = map_shopify_order_to_order(order, "test-store")
        assert mapped.buyer is not None
        assert mapped.buyer.is_guest is True
        assert mapped.buyer.email == "guest@example.com"

    def test_order_without_buyer(self):
        order = ShopifyOrder(
            id=8888,
            name="#8888",
            total_price="10.00",
            currency="PLN",
        )
        mapped = map_shopify_order_to_order(order, "test-store")
        assert mapped.buyer is None


class TestMapShopifyProductToProduct:
    def test_maps_basic_fields(self, sample_shopify_product: ShopifyProduct):
        product = map_shopify_product_to_product(sample_shopify_product)

        assert product.external_id == "4001"
        assert product.name == "Test Product A"
        assert product.description == "<p>Description of product A</p>"
        assert product.sku == "SKU-A-001"
        assert product.ean == "5901234567890"
        assert product.price == 49.99
        assert product.stock_quantity == 100.0

    def test_maps_attributes(self, sample_shopify_product: ShopifyProduct):
        product = map_shopify_product_to_product(sample_shopify_product)

        assert product.attributes["vendor"] == "TestVendor"
        assert product.attributes["product_type"] == "TestType"
        assert product.attributes["tags"] == "tag1, tag2"
        assert product.attributes["status"] == "active"
        assert product.attributes["variants_count"] == 1

    def test_product_without_variants(self):
        product = ShopifyProduct(
            id=5555,
            title="Empty Product",
            variants=[],
        )
        mapped = map_shopify_product_to_product(product)
        assert mapped.sku == ""
        assert mapped.ean == ""
        assert mapped.price == 0.0


class TestMapProductToShopify:
    def test_maps_basic_product(self):
        product = Product(
            external_id="0",
            name="New Product",
            sku="NEW-SKU",
            ean="1234567890123",
            price=29.99,
            description="<p>New description</p>",
            attributes={"vendor": "MyVendor", "product_type": "Widget", "tags": "new, hot"},
        )
        payload = map_product_to_shopify(product)

        assert payload["title"] == "New Product"
        assert payload["body_html"] == "<p>New description</p>"
        assert payload["vendor"] == "MyVendor"
        assert payload["product_type"] == "Widget"
        assert payload["tags"] == "new, hot"
        assert payload["variants"][0]["sku"] == "NEW-SKU"
        assert payload["variants"][0]["barcode"] == "1234567890123"
        assert payload["variants"][0]["price"] == "29.99"

    def test_minimal_product(self):
        product = Product(external_id="0", name="Minimal")
        payload = map_product_to_shopify(product)
        assert payload == {"title": "Minimal"}
