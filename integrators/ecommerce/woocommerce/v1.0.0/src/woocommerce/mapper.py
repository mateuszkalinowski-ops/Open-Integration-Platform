"""Maps WooCommerce orders/products to pinquark unified schemas and vice versa."""

import contextlib
import logging

from pinquark_common.schemas.ecommerce import (
    Address,
    Buyer,
    Order,
    OrderLine,
    OrderStatus,
    Product,
)

from src.woocommerce.schemas import WooOrder, WooOrderStatus, WooProduct

logger = logging.getLogger(__name__)

WOO_STATUS_TO_ORDER_STATUS: dict[WooOrderStatus, OrderStatus] = {
    WooOrderStatus.PENDING: OrderStatus.NEW,
    WooOrderStatus.PROCESSING: OrderStatus.PROCESSING,
    WooOrderStatus.ON_HOLD: OrderStatus.PROCESSING,
    WooOrderStatus.COMPLETED: OrderStatus.DELIVERED,
    WooOrderStatus.CANCELLED: OrderStatus.CANCELLED,
    WooOrderStatus.REFUNDED: OrderStatus.RETURNED,
    WooOrderStatus.FAILED: OrderStatus.CANCELLED,
    WooOrderStatus.TRASH: OrderStatus.CANCELLED,
}

ORDER_STATUS_TO_WOO: dict[OrderStatus, WooOrderStatus] = {
    OrderStatus.NEW: WooOrderStatus.PENDING,
    OrderStatus.PROCESSING: WooOrderStatus.PROCESSING,
    OrderStatus.READY_FOR_SHIPMENT: WooOrderStatus.PROCESSING,
    OrderStatus.SHIPPED: WooOrderStatus.COMPLETED,
    OrderStatus.DELIVERED: WooOrderStatus.COMPLETED,
    OrderStatus.CANCELLED: WooOrderStatus.CANCELLED,
    OrderStatus.RETURNED: WooOrderStatus.REFUNDED,
}


def map_woo_order_to_order(woo_order: WooOrder, account_name: str) -> Order:
    """Map a WooCommerce order to the unified Order schema."""
    delivery_address = None
    if woo_order.shipping:
        s = woo_order.shipping
        delivery_address = Address(
            first_name=s.first_name,
            last_name=s.last_name,
            company_name=s.company,
            street=s.address_1,
            building_number="",
            apartment_number=s.address_2,
            city=s.city,
            postal_code=s.postcode,
            country_code=s.country,
        )

    invoice_address = None
    buyer = None
    if woo_order.billing:
        b = woo_order.billing
        invoice_address = Address(
            first_name=b.first_name,
            last_name=b.last_name,
            company_name=b.company,
            street=b.address_1,
            building_number="",
            apartment_number=b.address_2,
            city=b.city,
            postal_code=b.postcode,
            country_code=b.country,
            phone=b.phone,
            email=b.email,
        )
        buyer = Buyer(
            external_id=str(woo_order.customer_id) if woo_order.customer_id else "0",
            email=b.email,
            first_name=b.first_name,
            last_name=b.last_name,
            company_name=b.company,
            is_guest=woo_order.customer_id == 0,
        )

    if delivery_address and woo_order.billing:
        delivery_address.phone = woo_order.billing.phone

    lines: list[OrderLine] = []
    for item in woo_order.line_items:
        lines.append(
            OrderLine(
                external_id=str(item.id) if item.id else "",
                offer_id=str(item.product_id) if item.product_id else "",
                product_id=str(item.product_id) if item.product_id else "",
                sku=item.sku,
                name=item.name,
                quantity=item.quantity,
                unit="szt.",
                unit_price=item.price,
                currency=woo_order.currency,
            )
        )

    delivery_method = ""
    if woo_order.shipping_lines:
        delivery_method = woo_order.shipping_lines[0].method_title

    return Order(
        external_id=str(woo_order.id),
        account_name=account_name,
        status=WOO_STATUS_TO_ORDER_STATUS.get(woo_order.status, OrderStatus.NEW),
        buyer=buyer,
        delivery_address=delivery_address,
        invoice_address=invoice_address,
        lines=lines,
        total_amount=float(woo_order.total),
        currency=woo_order.currency,
        payment_type=woo_order.payment_method_title or woo_order.payment_method,
        delivery_method=delivery_method,
        notes=woo_order.customer_note,
        created_at=woo_order.date_created,
        updated_at=woo_order.date_modified,
        raw_data=woo_order.model_dump(mode="json"),
    )


def order_status_to_woo_status(status: OrderStatus) -> WooOrderStatus:
    """Convert a unified OrderStatus to a WooCommerce order status string."""
    result = ORDER_STATUS_TO_WOO.get(status)
    if result is None:
        raise ValueError(f"Cannot map OrderStatus.{status.value} to WooCommerce status")
    return result


def map_woo_product_to_product(woo_product: WooProduct) -> Product:
    """Map a WooCommerce product to the unified Product schema."""
    price = 0.0
    if woo_product.regular_price:
        with contextlib.suppress(ValueError):
            price = float(woo_product.regular_price)
    elif woo_product.price:
        with contextlib.suppress(ValueError):
            price = float(woo_product.price)

    attrs: dict[str, list[str]] = {}
    for attr in woo_product.attributes:
        attrs[attr.name] = attr.options

    return Product(
        external_id=str(woo_product.id) if woo_product.id else "",
        sku=woo_product.sku,
        name=woo_product.name,
        description=woo_product.description,
        unit="szt.",
        price=price,
        stock_quantity=float(woo_product.stock_quantity) if woo_product.stock_quantity is not None else 0.0,
        attributes=attrs,
    )
