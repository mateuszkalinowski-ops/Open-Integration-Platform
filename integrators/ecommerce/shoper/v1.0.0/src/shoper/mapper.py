"""Maps Shoper API objects to Pinquark unified schemas and vice versa."""

import logging
from typing import Any

from pinquark_common.schemas.ecommerce import (
    Address,
    Buyer,
    Order,
    OrderLine,
    OrderStatus,
    Product,
)
from src.config import settings

logger = logging.getLogger(__name__)

SHOPER_STATUS_TO_ORDER: dict[str, OrderStatus] = {
    "1": OrderStatus.NEW,
    "2": OrderStatus.NEW,
    "3": OrderStatus.PROCESSING,
    "4": OrderStatus.PROCESSING,
    "5": OrderStatus.PROCESSING,
    "6": OrderStatus.READY_FOR_SHIPMENT,
    "7": OrderStatus.DELIVERED,
    "8": OrderStatus.CANCELLED,
    "9": OrderStatus.CANCELLED,
    "10": OrderStatus.CANCELLED,
    "12": OrderStatus.CANCELLED,
}

ORDER_STATUS_TO_SHOPER: dict[OrderStatus, str] = {
    OrderStatus.NEW: "2",
    OrderStatus.PROCESSING: "4",
    OrderStatus.READY_FOR_SHIPMENT: "6",
    OrderStatus.SHIPPED: "7",
    OrderStatus.DELIVERED: "7",
    OrderStatus.CANCELLED: "8",
}


def map_shoper_order_to_order(
    order_data: dict[str, Any],
    order_products: list[dict[str, Any]],
    account_name: str,
) -> Order:
    """Map a Shoper order to the unified Order schema."""
    order_id = order_data.get("order_id", 0)

    delivery_address = _map_address(order_data.get("delivery_address"))
    billing_address = _map_address(order_data.get("billing_address"))

    buyer = _map_buyer(order_data, delivery_address)

    lines = _map_order_lines(order_products)

    status_id = str(order_data.get("status_id", "2"))
    status = SHOPER_STATUS_TO_ORDER.get(status_id, OrderStatus.NEW)

    return Order(
        external_id=str(order_id),
        account_name=account_name,
        status=status,
        buyer=buyer,
        delivery_address=delivery_address,
        billing_address=billing_address,
        lines=lines,
        total_amount=float(order_data.get("sum", 0) or 0),
        currency="PLN",
        payment_type=str(order_data.get("payment_id", "")),
        delivery_method=str(order_data.get("shipping_id", "")),
        notes=order_data.get("notes", ""),
        updated_at=None,
        raw_data=order_data,
    )


def _map_address(addr_data: dict[str, Any] | None) -> Address | None:
    if not addr_data:
        return None
    return Address(
        first_name=addr_data.get("firstname", ""),
        last_name=addr_data.get("lastname", ""),
        company_name=addr_data.get("company", ""),
        street=addr_data.get("street1", ""),
        city=addr_data.get("city", ""),
        postal_code=addr_data.get("postcode", ""),
        country_code=addr_data.get("country_code", addr_data.get("country", "PL")),
        phone=addr_data.get("phone", ""),
    )


def _map_buyer(order_data: dict[str, Any], delivery_addr: Address | None) -> Buyer:
    user_id = order_data.get("user_id")

    first_name = delivery_addr.first_name if delivery_addr else ""
    last_name = delivery_addr.last_name if delivery_addr else ""
    company = delivery_addr.company_name if delivery_addr else ""

    return Buyer(
        external_id=str(user_id) if user_id else "",
        login="",
        email=order_data.get("email", ""),
        first_name=first_name,
        last_name=last_name,
        company_name=company,
        is_guest=user_id is None or user_id == 0,
    )


def _map_order_lines(order_products: list[dict[str, Any]]) -> list[OrderLine]:
    lines: list[OrderLine] = []
    for idx, product in enumerate(order_products):
        lines.append(OrderLine(
            external_id=str(product.get("id", idx)),
            offer_id=str(product.get("product_id", "")),
            product_id=str(product.get("product_id", "")),
            sku=product.get("code", ""),
            ean="",
            name=product.get("name", ""),
            quantity=float(product.get("quantity", 1) or 1),
            unit=product.get("unit", settings.default_unit),
            unit_price=float(product.get("price", 0) or 0),
            currency="PLN",
        ))
    return lines


def map_shoper_product_to_product(
    product_data: dict[str, Any],
    language_id: str = "pl_PL",
) -> Product:
    translations = product_data.get("translations", {})
    translation = translations.get(language_id, {})
    name = translation.get("name", "") if isinstance(translation, dict) else ""

    stock_data = product_data.get("stock") or {}

    return Product(
        external_id=str(product_data.get("product_id", "")),
        sku=product_data.get("code", ""),
        ean=product_data.get("ean", stock_data.get("ean", "")),
        name=name,
        price=float(stock_data.get("price", 0) or 0),
        stock_quantity=float(stock_data.get("stock", 0) or 0),
    )


def order_status_to_shoper(status: OrderStatus) -> str:
    result = ORDER_STATUS_TO_SHOPER.get(status)
    if result is None:
        raise ValueError(f"Cannot map OrderStatus.{status.value} to Shoper status_id")
    return result
