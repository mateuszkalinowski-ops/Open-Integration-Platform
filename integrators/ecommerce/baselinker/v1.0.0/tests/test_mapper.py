"""Tests for BaseLinker data mappers."""

from pinquark_common.schemas.ecommerce import OrderStatus
from src.baselinker.mapper import (
    find_bl_status_id,
    map_bl_order_to_order,
    map_bl_product_to_product,
    map_bl_status_to_order_status,
)


class TestStatusMapping:
    def test_maps_nowe_to_new(self, sample_bl_status_defs: dict[int, str]) -> None:
        assert map_bl_status_to_order_status(12345, sample_bl_status_defs) == OrderStatus.NEW

    def test_maps_w_realizacji_to_processing(self, sample_bl_status_defs: dict[int, str]) -> None:
        assert map_bl_status_to_order_status(12346, sample_bl_status_defs) == OrderStatus.PROCESSING

    def test_maps_gotowe_to_ready(self, sample_bl_status_defs: dict[int, str]) -> None:
        assert map_bl_status_to_order_status(12347, sample_bl_status_defs) == OrderStatus.READY_FOR_SHIPMENT

    def test_maps_wyslane_to_shipped(self, sample_bl_status_defs: dict[int, str]) -> None:
        assert map_bl_status_to_order_status(12348, sample_bl_status_defs) == OrderStatus.SHIPPED

    def test_maps_dostarczone_to_delivered(self, sample_bl_status_defs: dict[int, str]) -> None:
        assert map_bl_status_to_order_status(12349, sample_bl_status_defs) == OrderStatus.DELIVERED

    def test_maps_anulowane_to_cancelled(self, sample_bl_status_defs: dict[int, str]) -> None:
        assert map_bl_status_to_order_status(12350, sample_bl_status_defs) == OrderStatus.CANCELLED

    def test_maps_zwrot_to_returned(self, sample_bl_status_defs: dict[int, str]) -> None:
        assert map_bl_status_to_order_status(12351, sample_bl_status_defs) == OrderStatus.RETURNED

    def test_unknown_status_defaults_to_new(self) -> None:
        assert map_bl_status_to_order_status(99999, {}) == OrderStatus.NEW

    def test_unknown_name_defaults_to_processing(self) -> None:
        assert map_bl_status_to_order_status(1, {1: "Custom status"}) == OrderStatus.PROCESSING

    def test_find_bl_status_id_finds_match(self, sample_bl_status_defs: dict[int, str]) -> None:
        result = find_bl_status_id(OrderStatus.NEW, sample_bl_status_defs)
        assert result == 12345

    def test_find_bl_status_id_returns_none_for_no_match(self) -> None:
        result = find_bl_status_id(OrderStatus.NEW, {1: "Custom"})
        assert result is None


class TestOrderMapper:
    def test_maps_order_basic_fields(
        self,
        sample_bl_order: dict,
        sample_bl_status_defs: dict[int, str],
    ) -> None:
        order = map_bl_order_to_order(sample_bl_order, "test", sample_bl_status_defs)

        assert order.external_id == "77001"
        assert order.account_name == "test"
        assert order.status == OrderStatus.NEW
        assert order.currency == "PLN"
        assert order.notes == "Prosze o szybka wysylke"
        assert order.delivery_method == "InPost Paczkomaty"

    def test_maps_total_includes_delivery(
        self,
        sample_bl_order: dict,
        sample_bl_status_defs: dict[int, str],
    ) -> None:
        order = map_bl_order_to_order(sample_bl_order, "test", sample_bl_status_defs)
        expected = 89.99 * 2 + 29.99 * 1 + 12.99
        assert abs(order.total_amount - expected) < 0.01

    def test_maps_delivery_address(
        self,
        sample_bl_order: dict,
        sample_bl_status_defs: dict[int, str],
    ) -> None:
        order = map_bl_order_to_order(sample_bl_order, "test", sample_bl_status_defs)

        assert order.delivery_address is not None
        assert order.delivery_address.first_name == "Jan"
        assert order.delivery_address.last_name == "Kowalski"
        assert order.delivery_address.city == "Warszawa"
        assert order.delivery_address.postal_code == "00-001"
        assert order.delivery_address.country_code == "PL"

    def test_maps_invoice_address(
        self,
        sample_bl_order: dict,
        sample_bl_status_defs: dict[int, str],
    ) -> None:
        order = map_bl_order_to_order(sample_bl_order, "test", sample_bl_status_defs)

        assert order.invoice_address is not None
        assert order.invoice_address.company_name == "Firma Sp. z o.o."
        assert order.invoice_address.city == "Warszawa"

    def test_maps_buyer(
        self,
        sample_bl_order: dict,
        sample_bl_status_defs: dict[int, str],
    ) -> None:
        order = map_bl_order_to_order(sample_bl_order, "test", sample_bl_status_defs)

        assert order.buyer is not None
        assert order.buyer.login == "jan.kowalski"
        assert order.buyer.email == "jan.kowalski@example.com"
        assert order.buyer.first_name == "Jan"
        assert not order.buyer.is_guest

    def test_maps_order_lines(
        self,
        sample_bl_order: dict,
        sample_bl_status_defs: dict[int, str],
    ) -> None:
        order = map_bl_order_to_order(sample_bl_order, "test", sample_bl_status_defs)

        assert len(order.lines) == 2
        line = order.lines[0]
        assert line.name == "Koszulka polo niebieska"
        assert line.sku == "POLO-BLU-001"
        assert line.ean == "5901234123457"
        assert line.quantity == 2.0
        assert line.unit_price == 89.99

    def test_maps_empty_products(self, sample_bl_status_defs: dict[int, str]) -> None:
        order_data = {"order_id": 1, "order_status_id": 12345, "products": []}
        order = map_bl_order_to_order(order_data, "test", sample_bl_status_defs)
        assert len(order.lines) == 0

    def test_guest_buyer_when_no_login(self, sample_bl_status_defs: dict[int, str]) -> None:
        order_data = {
            "order_id": 2,
            "order_status_id": 12345,
            "user_login": "",
            "email": "guest@example.com",
            "delivery_fullname": "Anna Nowak",
            "products": [],
        }
        order = map_bl_order_to_order(order_data, "test", sample_bl_status_defs)
        assert order.buyer.is_guest


class TestProductMapper:
    def test_maps_product_basic_fields(self, sample_bl_product: dict) -> None:
        product = map_bl_product_to_product("5001", sample_bl_product, warehouse_id=1)

        assert product.external_id == "5001"
        assert product.sku == "POLO-BLU-001"
        assert product.ean == "5901234123457"
        assert product.name == "Koszulka polo niebieska"
        assert product.description == "Elegancka koszulka polo w kolorze niebieskim"

    def test_maps_product_price(self, sample_bl_product: dict) -> None:
        product = map_bl_product_to_product("5001", sample_bl_product)
        assert product.price == 89.99

    def test_maps_product_stock_for_specific_warehouse(self, sample_bl_product: dict) -> None:
        product = map_bl_product_to_product("5001", sample_bl_product, warehouse_id=1)
        assert product.stock_quantity == 150.0

    def test_maps_product_total_stock_when_no_warehouse(self, sample_bl_product: dict) -> None:
        product = map_bl_product_to_product("5001", sample_bl_product, warehouse_id=0)
        assert product.stock_quantity == 200.0

    def test_maps_product_without_stock_data(self) -> None:
        data = {"sku": "TEST", "name": "Test", "prices": {}, "stock": {}, "text_fields": {"name": "Test"}}
        product = map_bl_product_to_product("1", data)
        assert product.price == 0.0
        assert product.stock_quantity == 0.0
