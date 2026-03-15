"""Tests for WooCommerce order and product mapping logic."""

import pytest
from pinquark_common.schemas.ecommerce import OrderStatus
from src.woocommerce.mapper import (
    map_woo_order_to_order,
    map_woo_product_to_product,
    order_status_to_woo_status,
)
from src.woocommerce.schemas import (
    WooAddress,
    WooBilling,
    WooOrder,
    WooOrderLineItem,
    WooOrderStatus,
    WooProduct,
    WooProductAttribute,
    WooShippingLine,
)


def _make_woo_order(
    order_id: int = 123,
    status: WooOrderStatus = WooOrderStatus.PROCESSING,
    line_items: list | None = None,
) -> WooOrder:
    if line_items is None:
        line_items = [
            WooOrderLineItem(
                id=1,
                name="Test Product",
                product_id=42,
                quantity=2,
                sku="SKU-001",
                price=49.99,
                total="99.98",
            ),
        ]

    return WooOrder(
        id=order_id,
        number="123",
        status=status,
        currency="PLN",
        total="149.97",
        customer_id=10,
        customer_note="Please deliver in the morning",
        billing=WooBilling(
            first_name="Jan",
            last_name="Kowalski",
            company="Test Sp. z o.o.",
            address_1="ul. Testowa 1",
            address_2="m. 5",
            city="Warszawa",
            postcode="00-001",
            country="PL",
            email="jan@example.com",
            phone="500100200",
        ),
        shipping=WooAddress(
            first_name="Jan",
            last_name="Kowalski",
            company="Test Sp. z o.o.",
            address_1="ul. Testowa 1",
            address_2="m. 5",
            city="Warszawa",
            postcode="00-001",
            country="PL",
        ),
        payment_method="bacs",
        payment_method_title="Direct Bank Transfer",
        line_items=line_items,
        shipping_lines=[
            WooShippingLine(id=1, method_title="Kurier DPD", method_id="dpd"),
        ],
    )


class TestMapWooOrderToOrder:
    def test_maps_basic_fields(self):
        woo_order = _make_woo_order()
        order = map_woo_order_to_order(woo_order, "my-store")

        assert order.external_id == "123"
        assert order.account_name == "my-store"
        assert order.status == OrderStatus.PROCESSING
        assert order.total_amount == 149.97
        assert order.currency == "PLN"
        assert order.payment_type == "Direct Bank Transfer"

    def test_maps_buyer(self):
        woo_order = _make_woo_order()
        order = map_woo_order_to_order(woo_order, "store")

        assert order.buyer is not None
        assert order.buyer.external_id == "10"
        assert order.buyer.email == "jan@example.com"
        assert order.buyer.first_name == "Jan"
        assert order.buyer.last_name == "Kowalski"
        assert order.buyer.is_guest is False

    def test_guest_buyer(self):
        woo_order = _make_woo_order()
        woo_order.customer_id = 0
        order = map_woo_order_to_order(woo_order, "store")

        assert order.buyer is not None
        assert order.buyer.is_guest is True

    def test_maps_delivery_address(self):
        woo_order = _make_woo_order()
        order = map_woo_order_to_order(woo_order, "store")

        assert order.delivery_address is not None
        assert order.delivery_address.first_name == "Jan"
        assert order.delivery_address.city == "Warszawa"
        assert order.delivery_address.postal_code == "00-001"
        assert order.delivery_address.country_code == "PL"
        assert order.delivery_address.phone == "500100200"

    def test_maps_invoice_address(self):
        woo_order = _make_woo_order()
        order = map_woo_order_to_order(woo_order, "store")

        assert order.invoice_address is not None
        assert order.invoice_address.email == "jan@example.com"
        assert order.invoice_address.company_name == "Test Sp. z o.o."

    def test_maps_line_items(self):
        woo_order = _make_woo_order()
        order = map_woo_order_to_order(woo_order, "store")

        assert len(order.lines) == 1
        line = order.lines[0]
        assert line.external_id == "1"
        assert line.product_id == "42"
        assert line.sku == "SKU-001"
        assert line.name == "Test Product"
        assert line.quantity == 2.0
        assert line.unit_price == 49.99

    def test_maps_delivery_method(self):
        woo_order = _make_woo_order()
        order = map_woo_order_to_order(woo_order, "store")
        assert order.delivery_method == "Kurier DPD"

    def test_maps_customer_note(self):
        woo_order = _make_woo_order()
        order = map_woo_order_to_order(woo_order, "store")
        assert order.notes == "Please deliver in the morning"

    def test_maps_cancelled_status(self):
        woo_order = _make_woo_order(status=WooOrderStatus.CANCELLED)
        order = map_woo_order_to_order(woo_order, "store")
        assert order.status == OrderStatus.CANCELLED

    def test_maps_completed_to_delivered(self):
        woo_order = _make_woo_order(status=WooOrderStatus.COMPLETED)
        order = map_woo_order_to_order(woo_order, "store")
        assert order.status == OrderStatus.DELIVERED

    def test_maps_refunded_to_returned(self):
        woo_order = _make_woo_order(status=WooOrderStatus.REFUNDED)
        order = map_woo_order_to_order(woo_order, "store")
        assert order.status == OrderStatus.RETURNED

    def test_maps_pending_to_new(self):
        woo_order = _make_woo_order(status=WooOrderStatus.PENDING)
        order = map_woo_order_to_order(woo_order, "store")
        assert order.status == OrderStatus.NEW

    def test_stores_raw_data(self):
        woo_order = _make_woo_order()
        order = map_woo_order_to_order(woo_order, "store")
        assert "id" in order.raw_data
        assert order.raw_data["id"] == 123


class TestOrderStatusToWooStatus:
    @pytest.mark.parametrize(
        "order_status,expected",
        [
            (OrderStatus.NEW, WooOrderStatus.PENDING),
            (OrderStatus.PROCESSING, WooOrderStatus.PROCESSING),
            (OrderStatus.READY_FOR_SHIPMENT, WooOrderStatus.PROCESSING),
            (OrderStatus.SHIPPED, WooOrderStatus.COMPLETED),
            (OrderStatus.DELIVERED, WooOrderStatus.COMPLETED),
            (OrderStatus.CANCELLED, WooOrderStatus.CANCELLED),
            (OrderStatus.RETURNED, WooOrderStatus.REFUNDED),
        ],
    )
    def test_status_mapping(self, order_status, expected):
        assert order_status_to_woo_status(order_status) == expected


class TestMapWooProductToProduct:
    def test_maps_basic_product(self):
        woo_product = WooProduct(
            id=42,
            name="Test Widget",
            sku="WIDGET-001",
            regular_price="29.99",
            description="A test widget",
            manage_stock=True,
            stock_quantity=100,
        )
        product = map_woo_product_to_product(woo_product)

        assert product.external_id == "42"
        assert product.sku == "WIDGET-001"
        assert product.name == "Test Widget"
        assert product.price == 29.99
        assert product.stock_quantity == 100.0
        assert product.description == "A test widget"

    def test_maps_product_with_attributes(self):
        woo_product = WooProduct(
            id=43,
            name="T-Shirt",
            sku="TSHIRT-001",
            regular_price="59.00",
            attributes=[
                WooProductAttribute(name="Color", options=["Red", "Blue"]),
                WooProductAttribute(name="Size", options=["S", "M", "L"]),
            ],
        )
        product = map_woo_product_to_product(woo_product)

        assert "Color" in product.attributes
        assert product.attributes["Color"] == ["Red", "Blue"]
        assert product.attributes["Size"] == ["S", "M", "L"]

    def test_maps_product_no_price(self):
        woo_product = WooProduct(id=44, name="Free Item", sku="FREE-001")
        product = map_woo_product_to_product(woo_product)
        assert product.price == 0.0

    def test_maps_product_sale_price_fallback(self):
        woo_product = WooProduct(
            id=45,
            name="Sale Item",
            sku="SALE-001",
            regular_price="",
            price="19.99",
        )
        product = map_woo_product_to_product(woo_product)
        assert product.price == 19.99

    def test_maps_product_no_stock(self):
        woo_product = WooProduct(
            id=46,
            name="No Stock",
            sku="NS-001",
            manage_stock=False,
            stock_quantity=None,
        )
        product = map_woo_product_to_product(woo_product)
        assert product.stock_quantity == 0.0
