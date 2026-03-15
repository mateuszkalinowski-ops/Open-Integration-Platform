"""Tests for Amazon SP-API mapper functions."""

from pinquark_common.schemas.ecommerce import OrderStatus
from src.amazon.mapper import (
    map_amazon_order_to_order,
    map_amazon_status_to_order_status,
    map_catalog_item_to_product,
    map_order_status_to_amazon,
)


class TestStatusMapping:
    def test_pending_maps_to_new(self) -> None:
        assert map_amazon_status_to_order_status("Pending") == OrderStatus.NEW

    def test_unshipped_maps_to_processing(self) -> None:
        assert map_amazon_status_to_order_status("Unshipped") == OrderStatus.PROCESSING

    def test_partially_shipped_maps_to_processing(self) -> None:
        assert map_amazon_status_to_order_status("PartiallyShipped") == OrderStatus.PROCESSING

    def test_shipped_maps_to_shipped(self) -> None:
        assert map_amazon_status_to_order_status("Shipped") == OrderStatus.SHIPPED

    def test_canceled_maps_to_cancelled(self) -> None:
        assert map_amazon_status_to_order_status("Canceled") == OrderStatus.CANCELLED

    def test_unknown_status_maps_to_new(self) -> None:
        assert map_amazon_status_to_order_status("SomeNewStatus") == OrderStatus.NEW

    def test_reverse_mapping_shipped(self) -> None:
        assert map_order_status_to_amazon(OrderStatus.SHIPPED) == "Shipped"

    def test_reverse_mapping_cancelled(self) -> None:
        assert map_order_status_to_amazon(OrderStatus.CANCELLED) == "Canceled"


class TestOrderMapping:
    def test_maps_order_basic_fields(self, sample_amazon_order: dict, sample_amazon_order_items: list) -> None:
        order = map_amazon_order_to_order(sample_amazon_order, sample_amazon_order_items, "test-account")

        assert order.external_id == "114-1234567-8901234"
        assert order.account_name == "test-account"
        assert order.status == OrderStatus.PROCESSING
        assert order.currency == "EUR"
        assert order.total_amount == 59.98

    def test_maps_order_lines(self, sample_amazon_order: dict, sample_amazon_order_items: list) -> None:
        order = map_amazon_order_to_order(sample_amazon_order, sample_amazon_order_items, "test")

        assert len(order.lines) == 2
        assert order.lines[0].sku == "SKU-TSHIRT-BLU-L"
        assert order.lines[0].name == "Blue T-Shirt Large"
        assert order.lines[0].quantity == 1.0
        assert order.lines[0].unit_price == 29.99
        assert order.lines[1].offer_id == "B0EXAMPLE02"

    def test_maps_shipping_address(self, sample_amazon_order: dict, sample_amazon_order_items: list) -> None:
        order = map_amazon_order_to_order(sample_amazon_order, sample_amazon_order_items, "test")

        assert order.delivery_address is not None
        assert order.delivery_address.first_name == "Max"
        assert order.delivery_address.last_name == "Mustermann"
        assert order.delivery_address.city == "Berlin"
        assert order.delivery_address.postal_code == "10115"
        assert order.delivery_address.country_code == "DE"

    def test_maps_buyer(self, sample_amazon_order: dict, sample_amazon_order_items: list) -> None:
        order = map_amazon_order_to_order(sample_amazon_order, sample_amazon_order_items, "test")

        assert order.buyer is not None
        assert order.buyer.email == "buyer123@marketplace.amazon.de"
        assert order.buyer.first_name == "Max"
        assert order.buyer.last_name == "Mustermann"

    def test_empty_items_list(self, sample_amazon_order: dict) -> None:
        order = map_amazon_order_to_order(sample_amazon_order, [], "test")
        assert len(order.lines) == 0

    def test_missing_shipping_address(self, sample_amazon_order_items: list) -> None:
        order_data = {
            "AmazonOrderId": "999-0000000-0000000",
            "OrderStatus": "Pending",
            "OrderTotal": {"CurrencyCode": "USD", "Amount": "10.00"},
            "BuyerInfo": {},
        }
        order = map_amazon_order_to_order(order_data, sample_amazon_order_items, "test")
        assert order.delivery_address is None


class TestCatalogMapping:
    def test_maps_catalog_item(self, sample_amazon_catalog_item: dict) -> None:
        product = map_catalog_item_to_product(sample_amazon_catalog_item)

        assert product.external_id == "B0EXAMPLE01"
        assert product.name == "Blue T-Shirt Large"
        assert product.ean == "4012345678901"
        assert product.attributes["brand"] == "ExampleBrand"
        assert product.attributes["manufacturer"] == "ExampleManufacturer"

    def test_maps_catalog_item_no_identifiers(self) -> None:
        item = {"asin": "B0TEST", "summaries": [{"itemName": "Test"}], "identifiers": []}
        product = map_catalog_item_to_product(item)
        assert product.external_id == "B0TEST"
        assert product.ean == ""
