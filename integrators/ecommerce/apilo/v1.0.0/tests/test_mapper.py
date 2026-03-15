"""Tests for Apilo mapper functions."""

from pinquark_common.schemas.ecommerce import OrderStatus
from src.apilo.mapper import (
    map_apilo_order_to_order,
    map_apilo_product_to_product,
    map_apilo_status_to_order_status,
    map_order_status_to_apilo,
)


class TestStatusMapping:
    def test_nowy_maps_to_new(self) -> None:
        assert map_apilo_status_to_order_status(7, "Nowy") == OrderStatus.NEW

    def test_w_realizacji_maps_to_processing(self) -> None:
        assert map_apilo_status_to_order_status(9, "W realizacji") == OrderStatus.PROCESSING

    def test_wysłane_maps_to_shipped(self) -> None:
        assert map_apilo_status_to_order_status(11, "Wysłane") == OrderStatus.SHIPPED

    def test_dostarczone_maps_to_delivered(self) -> None:
        assert map_apilo_status_to_order_status(12, "Dostarczone") == OrderStatus.DELIVERED

    def test_anulowane_maps_to_cancelled(self) -> None:
        assert map_apilo_status_to_order_status(13, "Anulowane") == OrderStatus.CANCELLED

    def test_zwrot_maps_to_returned(self) -> None:
        assert map_apilo_status_to_order_status(14, "Zwrot") == OrderStatus.RETURNED

    def test_do_wysylki_maps_to_ready(self) -> None:
        assert map_apilo_status_to_order_status(10, "Do wysyłki") == OrderStatus.READY_FOR_SHIPMENT

    def test_unknown_status_maps_to_new(self) -> None:
        assert map_apilo_status_to_order_status(999, "Unknown status XYZ") == OrderStatus.NEW

    def test_english_status_names(self) -> None:
        assert map_apilo_status_to_order_status(1, "New") == OrderStatus.NEW
        assert map_apilo_status_to_order_status(2, "Shipped") == OrderStatus.SHIPPED
        assert map_apilo_status_to_order_status(3, "Cancelled") == OrderStatus.CANCELLED

    def test_reverse_mapping_new(self, sample_apilo_status_map: list) -> None:
        result = map_order_status_to_apilo(OrderStatus.NEW, sample_apilo_status_map)
        assert result == 7

    def test_reverse_mapping_processing(self, sample_apilo_status_map: list) -> None:
        result = map_order_status_to_apilo(OrderStatus.PROCESSING, sample_apilo_status_map)
        assert result == 9

    def test_reverse_mapping_shipped(self, sample_apilo_status_map: list) -> None:
        result = map_order_status_to_apilo(OrderStatus.SHIPPED, sample_apilo_status_map)
        assert result == 11

    def test_reverse_mapping_cancelled(self, sample_apilo_status_map: list) -> None:
        result = map_order_status_to_apilo(OrderStatus.CANCELLED, sample_apilo_status_map)
        assert result == 13

    def test_reverse_mapping_no_map(self) -> None:
        result = map_order_status_to_apilo(OrderStatus.NEW, None)
        assert result is None


class TestOrderMapping:
    def test_maps_order_basic_fields(self, sample_apilo_order: dict) -> None:
        order = map_apilo_order_to_order(sample_apilo_order, "test-account")

        assert order.external_id == "AL231100017"
        assert order.account_name == "test-account"
        assert order.currency == "PLN"
        assert order.total_amount == 1259.98

    def test_maps_order_lines(self, sample_apilo_order: dict) -> None:
        order = map_apilo_order_to_order(sample_apilo_order, "test")

        assert len(order.lines) == 2
        assert order.lines[0].sku == "P44/3-T1.2"
        assert order.lines[0].name == "Samsung Galaxy S20 Plus Black 128GB 5G"
        assert order.lines[0].quantity == 2.0
        assert order.lines[0].unit_price == 2799.99
        assert order.lines[0].ean == "400638133393"
        assert order.lines[0].tax_rate == 23.0

    def test_maps_shipping_line(self, sample_apilo_order: dict) -> None:
        order = map_apilo_order_to_order(sample_apilo_order, "test")

        assert order.lines[1].sku == "ship-pp"
        assert order.lines[1].name == "Wysyłka - Poczta Polska - Pocztex"
        assert order.lines[1].quantity == 1.0
        assert order.lines[1].unit_price == 10.0

    def test_maps_delivery_address(self, sample_apilo_order: dict) -> None:
        order = map_apilo_order_to_order(sample_apilo_order, "test")

        assert order.delivery_address is not None
        assert order.delivery_address.first_name == "Jan"
        assert order.delivery_address.last_name == "Kowalski"
        assert order.delivery_address.city == "Kraków"
        assert order.delivery_address.postal_code == "31-154"
        assert order.delivery_address.country_code == "PL"
        assert order.delivery_address.street == "Testowa"
        assert order.delivery_address.building_number == "4b/12"

    def test_maps_invoice_address(self, sample_apilo_order: dict) -> None:
        order = map_apilo_order_to_order(sample_apilo_order, "test")

        assert order.invoice_address is not None
        assert order.invoice_address.company_name == "Apilo Sp. z o.o."

    def test_maps_buyer(self, sample_apilo_order: dict) -> None:
        order = map_apilo_order_to_order(sample_apilo_order, "test")

        assert order.buyer is not None
        assert order.buyer.email == "jan.kowalski@apilo.com"
        assert order.buyer.first_name == "Jan"
        assert order.buyer.last_name == "Kowalski"
        assert order.buyer.login == "user123"
        assert order.buyer.company_name == "Apilo Sp. z o.o."
        assert order.buyer.is_guest is False

    def test_maps_notes(self, sample_apilo_order: dict) -> None:
        order = map_apilo_order_to_order(sample_apilo_order, "test")
        assert "Prosze o dostawe" in order.notes

    def test_empty_items_list(self, sample_apilo_order: dict) -> None:
        sample_apilo_order["orderItems"] = []
        order = map_apilo_order_to_order(sample_apilo_order, "test")
        assert len(order.lines) == 0

    def test_missing_address(self) -> None:
        order_data = {
            "id": "AL999900001",
            "status": 7,
            "originalCurrency": "PLN",
            "originalAmountTotalWithTax": 100.0,
            "orderItems": [],
        }
        order = map_apilo_order_to_order(order_data, "test")
        assert order.delivery_address is None
        assert order.buyer is not None
        assert order.buyer.external_id == "AL999900001"


class TestProductMapping:
    def test_maps_product(self, sample_apilo_product: dict) -> None:
        product = map_apilo_product_to_product(sample_apilo_product)

        assert product.external_id == "1234"
        assert product.sku == "HG-331/P"
        assert product.ean == "4006381333931"
        assert product.name == "Samsung Galaxy S20 Plus Black 128GB"
        assert product.price == 123.0
        assert product.stock_quantity == 15.0
        assert product.unit == "Szt."
        assert product.attributes["weight"] == 1.12
        assert product.attributes["tax"] == "23.00"

    def test_maps_product_no_name_uses_group_name(self) -> None:
        data = {
            "id": 999,
            "name": "",
            "groupName": "Group Product Name",
            "sku": "SKU1",
            "quantity": 0,
            "priceWithTax": 0,
        }
        product = map_apilo_product_to_product(data)
        assert product.name == "Group Product Name"

    def test_maps_product_default_unit(self) -> None:
        data = {"id": 888, "sku": "SKU2", "unit": None, "quantity": 5, "priceWithTax": 10}
        product = map_apilo_product_to_product(data)
        assert product.unit == "szt."
