"""Tests for Allegro order mapping logic."""

import pytest

from pinquark_common.schemas.ecommerce import OrderStatus
from src.allegro.mapper import (
    map_checkout_to_order,
    order_status_to_fulfillment,
    extract_ean_from_parameters,
)
from src.allegro.schemas import (
    AllegroCheckoutForm,
    AllegroBuyer,
    AllegroDelivery,
    AllegroDeliveryAddress,
    AllegroLineItem,
    AllegroOfferRef,
    AllegroPrice,
    AllegroSummary,
    AllegroPayment,
    CheckoutFormStatus,
    FulfillmentStatus,
)


def _make_checkout(
    checkout_id: str = "checkout-123",
    status: CheckoutFormStatus = CheckoutFormStatus.READY_FOR_PROCESSING,
    buyer_id: str = "buyer-1",
    line_items: list | None = None,
) -> AllegroCheckoutForm:
    if line_items is None:
        line_items = [
            AllegroLineItem(
                id="line-1",
                offer=AllegroOfferRef(id="offer-1", name="Test Product"),
                quantity=2,
                price=AllegroPrice(amount="49.99", currency="PLN"),
            ),
        ]

    return AllegroCheckoutForm(
        id=checkout_id,
        status=status,
        buyer=AllegroBuyer(
            id=buyer_id,
            email="buyer@example.com",
            login="buyer123",
            firstName="Jan",
            lastName="Kowalski",
            guest=False,
        ),
        delivery=AllegroDelivery(
            address=AllegroDeliveryAddress(
                firstName="Jan",
                lastName="Kowalski",
                street="ul. Testowa 1",
                city="Warszawa",
                zipCode="00-001",
                countryCode="PL",
                phoneNumber="500100200",
            ),
        ),
        payment=AllegroPayment(type="ONLINE"),
        lineItems=line_items,
        summary=AllegroSummary(totalToPay=AllegroPrice(amount="99.98", currency="PLN")),
    )


class TestMapCheckoutToOrder:
    def test_maps_basic_fields(self):
        checkout = _make_checkout()
        order = map_checkout_to_order(checkout, "my-account")

        assert order.external_id == "checkout-123"
        assert order.account_name == "my-account"
        assert order.status == OrderStatus.NEW
        assert order.total_amount == 99.98
        assert order.currency == "PLN"
        assert order.payment_type == "ONLINE"

    def test_maps_buyer(self):
        checkout = _make_checkout()
        order = map_checkout_to_order(checkout, "acc")

        assert order.buyer is not None
        assert order.buyer.external_id == "buyer-1"
        assert order.buyer.email == "buyer@example.com"
        assert order.buyer.first_name == "Jan"
        assert order.buyer.last_name == "Kowalski"
        assert order.buyer.is_guest is False

    def test_maps_delivery_address(self):
        checkout = _make_checkout()
        order = map_checkout_to_order(checkout, "acc")

        assert order.delivery_address is not None
        assert order.delivery_address.first_name == "Jan"
        assert order.delivery_address.city == "Warszawa"
        assert order.delivery_address.postal_code == "00-001"
        assert order.delivery_address.country_code == "PL"
        assert order.delivery_address.phone == "500100200"

    def test_maps_line_items(self):
        checkout = _make_checkout()
        order = map_checkout_to_order(checkout, "acc")

        assert len(order.lines) == 1
        line = order.lines[0]
        assert line.external_id == "line-1"
        assert line.offer_id == "offer-1"
        assert line.name == "Test Product"
        assert line.quantity == 2.0
        assert line.unit_price == 49.99

    def test_maps_cancelled_status(self):
        checkout = _make_checkout(status=CheckoutFormStatus.CANCELLED)
        order = map_checkout_to_order(checkout, "acc")
        assert order.status == OrderStatus.CANCELLED

    def test_maps_with_product_details(self):
        checkout = _make_checkout()
        details = {"offer-1": {"ean": "5901234123457", "sku": "SKU-001", "name": "Detailed Name", "product_id": "prod-1"}}
        order = map_checkout_to_order(checkout, "acc", details)

        line = order.lines[0]
        assert line.ean == "5901234123457"
        assert line.sku == "SKU-001"
        assert line.product_id == "prod-1"

    def test_stores_raw_data(self):
        checkout = _make_checkout()
        order = map_checkout_to_order(checkout, "acc")
        assert "id" in order.raw_data
        assert order.raw_data["id"] == "checkout-123"


class TestOrderStatusToFulfillment:
    @pytest.mark.parametrize(
        "order_status,expected",
        [
            (OrderStatus.NEW, FulfillmentStatus.NEW),
            (OrderStatus.PROCESSING, FulfillmentStatus.PROCESSING),
            (OrderStatus.READY_FOR_SHIPMENT, FulfillmentStatus.READY_FOR_SHIPMENT),
            (OrderStatus.SHIPPED, FulfillmentStatus.SENT),
            (OrderStatus.DELIVERED, FulfillmentStatus.PICKED_UP),
            (OrderStatus.CANCELLED, FulfillmentStatus.CANCELLED),
        ],
    )
    def test_status_mapping(self, order_status, expected):
        assert order_status_to_fulfillment(order_status) == expected

    def test_unmapped_status_raises(self):
        with pytest.raises(ValueError, match="Cannot map"):
            order_status_to_fulfillment(OrderStatus.RETURNED)


class TestExtractEan:
    def test_extracts_ean_from_values(self):
        params = [{"id": "225693", "name": "EAN", "values": ["5901234123457"]}]
        assert extract_ean_from_parameters(params) == "5901234123457"

    def test_extracts_ean_from_values_labels(self):
        params = [{"id": "225693", "name": "EAN", "values": [], "valuesLabels": ["5901234123457"]}]
        assert extract_ean_from_parameters(params) == "5901234123457"

    def test_returns_empty_when_no_ean(self):
        params = [{"id": "999", "name": "Color", "values": ["Red"]}]
        assert extract_ean_from_parameters(params) == ""

    def test_returns_empty_for_empty_list(self):
        assert extract_ean_from_parameters([]) == ""
