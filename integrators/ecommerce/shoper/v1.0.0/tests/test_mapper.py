"""Tests for Shoper data mappers."""

import pytest
from pinquark_common.schemas.ecommerce import OrderStatus
from src.shoper.mapper import (
    ORDER_STATUS_TO_SHOPER,
    SHOPER_STATUS_TO_ORDER,
    map_shoper_order_to_order,
    map_shoper_product_to_product,
    order_status_to_shoper,
)


class TestOrderMapper:
    def test_maps_order_basic_fields(
        self,
        sample_shoper_order: dict,
        sample_order_products: list[dict],
    ) -> None:
        order = map_shoper_order_to_order(sample_shoper_order, sample_order_products, "test")

        assert order.external_id == "12345"
        assert order.account_name == "test"
        assert order.status == OrderStatus.NEW
        assert order.total_amount == 199.99
        assert order.notes == "Prosze o szybka wysylke"

    def test_maps_delivery_address(
        self,
        sample_shoper_order: dict,
        sample_order_products: list[dict],
    ) -> None:
        order = map_shoper_order_to_order(sample_shoper_order, sample_order_products, "test")

        assert order.delivery_address is not None
        assert order.delivery_address.first_name == "Jan"
        assert order.delivery_address.last_name == "Kowalski"
        assert order.delivery_address.city == "Warszawa"
        assert order.delivery_address.postal_code == "00-001"
        assert order.delivery_address.country_code == "PL"

    def test_maps_buyer(
        self,
        sample_shoper_order: dict,
        sample_order_products: list[dict],
    ) -> None:
        order = map_shoper_order_to_order(sample_shoper_order, sample_order_products, "test")

        assert order.buyer is not None
        assert order.buyer.external_id == "100"
        assert order.buyer.email == "jan.kowalski@example.com"
        assert order.buyer.first_name == "Jan"

    def test_maps_order_lines(
        self,
        sample_shoper_order: dict,
        sample_order_products: list[dict],
    ) -> None:
        order = map_shoper_order_to_order(sample_shoper_order, sample_order_products, "test")

        assert len(order.lines) == 1
        line = order.lines[0]
        assert line.name == "Koszulka polo"
        assert line.sku == "POLO-001"
        assert line.quantity == 2.0
        assert line.unit_price == 99.99

    def test_maps_empty_products(self, sample_shoper_order: dict) -> None:
        order = map_shoper_order_to_order(sample_shoper_order, [], "test")
        assert len(order.lines) == 0

    def test_maps_all_statuses(self) -> None:
        for status_id, expected in SHOPER_STATUS_TO_ORDER.items():
            order_data = {"order_id": 1, "status_id": status_id}
            order = map_shoper_order_to_order(order_data, [], "test")
            assert order.status == expected, f"Failed for status_id={status_id}"


class TestProductMapper:
    def test_maps_product_basic_fields(self, sample_shoper_product: dict) -> None:
        product = map_shoper_product_to_product(sample_shoper_product, "pl_PL")

        assert product.external_id == "500"
        assert product.sku == "POLO-001"
        assert product.ean == "5901234123457"
        assert product.name == "Koszulka polo"

    def test_maps_product_with_stock_data(self, sample_shoper_product: dict) -> None:
        product = map_shoper_product_to_product(sample_shoper_product, "pl_PL")

        assert product.price == 99.99
        assert product.stock_quantity == 150.0

    def test_maps_product_without_translations(self) -> None:
        product_data = {"product_id": 1, "code": "TEST", "ean": "123", "translations": {}}
        product = map_shoper_product_to_product(product_data, "pl_PL")
        assert product.name == ""

    def test_maps_product_without_stock(self) -> None:
        product_data = {"product_id": 1, "code": "TEST", "translations": {"pl_PL": {"name": "Test"}}}
        product = map_shoper_product_to_product(product_data, "pl_PL")
        assert product.price == 0.0
        assert product.stock_quantity == 0.0


class TestStatusMapping:
    def test_order_status_to_shoper_all_values(self) -> None:
        for status, expected_id in ORDER_STATUS_TO_SHOPER.items():
            result = order_status_to_shoper(status)
            assert result == expected_id

    def test_order_status_to_shoper_raises_for_unknown(self) -> None:
        with pytest.raises(ValueError, match="Cannot map"):
            order_status_to_shoper(OrderStatus.RETURNED)
