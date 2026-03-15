"""Tests for IdoSell mapper functions."""

import pytest
from pinquark_common.schemas.ecommerce import OrderStatus
from src.idosell.mapper import (
    map_idosell_order_status,
    map_idosell_order_to_order,
    map_idosell_product_to_product,
    order_status_to_idosell,
)
from src.idosell.schemas import IdoSellOrder, IdoSellProduct


class TestOrderStatusMapping:
    def test_new_maps_to_new(self) -> None:
        assert map_idosell_order_status("new") == OrderStatus.NEW

    def test_payment_waiting_maps_to_new(self) -> None:
        assert map_idosell_order_status("payment_waiting") == OrderStatus.NEW

    def test_packed_maps_to_processing(self) -> None:
        assert map_idosell_order_status("packed") == OrderStatus.PROCESSING

    def test_ready_maps_to_ready_for_shipment(self) -> None:
        assert map_idosell_order_status("ready") == OrderStatus.READY_FOR_SHIPMENT

    def test_finished_maps_to_delivered(self) -> None:
        assert map_idosell_order_status("finished") == OrderStatus.DELIVERED

    def test_finished_ext_maps_to_delivered(self) -> None:
        assert map_idosell_order_status("finished_ext") == OrderStatus.DELIVERED

    def test_canceled_maps_to_cancelled(self) -> None:
        assert map_idosell_order_status("canceled") == OrderStatus.CANCELLED

    def test_returned_maps_to_returned(self) -> None:
        assert map_idosell_order_status("returned") == OrderStatus.RETURNED

    def test_unknown_status_defaults_to_new(self) -> None:
        assert map_idosell_order_status("some_unknown_status") == OrderStatus.NEW

    def test_all_statuses_covered(self) -> None:
        from src.idosell.schemas import IdoSellOrderStatus

        for status in IdoSellOrderStatus:
            result = map_idosell_order_status(status.value)
            assert isinstance(result, OrderStatus)


class TestReverseStatusMapping:
    def test_new_to_idosell(self) -> None:
        assert order_status_to_idosell(OrderStatus.NEW) == "new"

    def test_processing_to_packed(self) -> None:
        assert order_status_to_idosell(OrderStatus.PROCESSING) == "packed"

    def test_delivered_to_finished(self) -> None:
        assert order_status_to_idosell(OrderStatus.DELIVERED) == "finished"

    def test_cancelled_to_canceled(self) -> None:
        assert order_status_to_idosell(OrderStatus.CANCELLED) == "canceled"


class TestMapIdoSellOrderToOrder:
    def test_maps_basic_fields(self, sample_idosell_order: IdoSellOrder) -> None:
        order = map_idosell_order_to_order(sample_idosell_order, "test-shop")

        assert order.external_id == "ORD-001"
        assert order.account_name == "test-shop"
        assert order.status == OrderStatus.NEW

    def test_maps_buyer(self, sample_idosell_order: IdoSellOrder) -> None:
        order = map_idosell_order_to_order(sample_idosell_order, "test-shop")

        assert order.buyer is not None
        assert order.buyer.external_id == "500"
        assert order.buyer.email == "jan@example.com"
        assert order.buyer.login == "jan_kowalski"
        assert order.buyer.is_guest is False

    def test_maps_delivery_address(self, sample_idosell_order: IdoSellOrder) -> None:
        order = map_idosell_order_to_order(sample_idosell_order, "test-shop")

        assert order.delivery_address is not None
        assert order.delivery_address.first_name == "Jan"
        assert order.delivery_address.last_name == "Kowalski"
        assert order.delivery_address.city == "Kraków"
        assert order.delivery_address.postal_code == "00-002"

    def test_maps_billing_address(self, sample_idosell_order: IdoSellOrder) -> None:
        order = map_idosell_order_to_order(sample_idosell_order, "test-shop")

        assert order.invoice_address is not None
        assert order.invoice_address.company_name == "Firma ABC"
        assert order.invoice_address.city == "Warszawa"

    def test_maps_order_lines(self, sample_idosell_order: IdoSellOrder) -> None:
        order = map_idosell_order_to_order(sample_idosell_order, "test-shop")

        assert len(order.lines) == 1
        line = order.lines[0]
        assert line.sku == "POLO-001"
        assert line.name == "Koszulka Polo"
        assert line.quantity == 2.0
        assert line.unit_price == 49.99

    def test_maps_totals(self, sample_idosell_order: IdoSellOrder) -> None:
        order = map_idosell_order_to_order(sample_idosell_order, "test-shop")

        assert order.total_amount == pytest.approx(112.49, abs=0.01)
        assert order.currency == "PLN"

    def test_maps_dates(self, sample_idosell_order: IdoSellOrder) -> None:
        order = map_idosell_order_to_order(sample_idosell_order, "test-shop")

        assert order.created_at is not None
        assert order.updated_at is not None
        assert order.created_at.year == 2026

    def test_maps_notes(self, sample_idosell_order: IdoSellOrder) -> None:
        order = map_idosell_order_to_order(sample_idosell_order, "test-shop")
        assert order.notes == "Proszę o szybką wysyłkę"


class TestMapIdoSellProductToProduct:
    def test_maps_basic_fields(self, sample_idosell_product: IdoSellProduct) -> None:
        product = map_idosell_product_to_product(sample_idosell_product)

        assert product.external_id == "100"
        assert product.sku == "POLO-001"
        assert product.name == "Koszulka Polo"

    def test_maps_ean_from_sizes(self, sample_idosell_product: IdoSellProduct) -> None:
        product = map_idosell_product_to_product(sample_idosell_product)
        assert product.ean == "5901234567890"

    def test_maps_stock_quantity(self, sample_idosell_product: IdoSellProduct) -> None:
        product = map_idosell_product_to_product(sample_idosell_product)
        assert product.stock_quantity == 150.0

    def test_maps_price_and_currency(self, sample_idosell_product: IdoSellProduct) -> None:
        product = map_idosell_product_to_product(sample_idosell_product)
        assert product.price == 49.99
        assert product.currency == "PLN"

    def test_maps_unit(self, sample_idosell_product: IdoSellProduct) -> None:
        product = map_idosell_product_to_product(sample_idosell_product)
        assert product.unit == "szt."

    def test_prefers_polish_name(self, sample_idosell_product: IdoSellProduct) -> None:
        from src.idosell.schemas import IdoSellDescriptionLangData

        sample_idosell_product.productDescriptionsLangData = [
            IdoSellDescriptionLangData(langId="eng", productName="Polo Shirt"),
            IdoSellDescriptionLangData(langId="pol", productName="Koszulka Polo"),
        ]
        product = map_idosell_product_to_product(sample_idosell_product)
        assert product.name == "Koszulka Polo"
