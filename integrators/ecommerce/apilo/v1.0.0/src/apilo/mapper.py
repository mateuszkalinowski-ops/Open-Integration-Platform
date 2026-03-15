"""Maps Apilo API objects to Pinquark unified schemas and vice versa.

Apilo order statuses are integer IDs. Common defaults:
7=Nowy, 8=Niepotwierdzone, 9=W realizacji, etc.
Actual IDs depend on the account configuration (GET /orders/status/map/).
"""

import contextlib
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

logger = logging.getLogger(__name__)

_APILO_STATUS_NAME_MAP: dict[str, OrderStatus] = {
    "nowy": OrderStatus.NEW,
    "new": OrderStatus.NEW,
    "niepotwierdzone": OrderStatus.NEW,
    "unconfirmed": OrderStatus.NEW,
    "w realizacji": OrderStatus.PROCESSING,
    "in progress": OrderStatus.PROCESSING,
    "processing": OrderStatus.PROCESSING,
    "do wysyłki": OrderStatus.READY_FOR_SHIPMENT,
    "ready to ship": OrderStatus.READY_FOR_SHIPMENT,
    "wysłane": OrderStatus.SHIPPED,
    "shipped": OrderStatus.SHIPPED,
    "dostarczone": OrderStatus.DELIVERED,
    "delivered": OrderStatus.DELIVERED,
    "anulowane": OrderStatus.CANCELLED,
    "cancelled": OrderStatus.CANCELLED,
    "canceled": OrderStatus.CANCELLED,
    "zwrot": OrderStatus.RETURNED,
    "returned": OrderStatus.RETURNED,
}


def map_apilo_status_to_order_status(status_id: int, status_name: str = "") -> OrderStatus:
    """Map Apilo status to unified OrderStatus.

    Uses status name heuristics since Apilo status IDs are configurable per account.
    """
    name_lower = status_name.lower().strip()
    if name_lower in _APILO_STATUS_NAME_MAP:
        return _APILO_STATUS_NAME_MAP[name_lower]

    for keyword, unified_status in _APILO_STATUS_NAME_MAP.items():
        if keyword in name_lower:
            return unified_status

    return OrderStatus.NEW


def map_order_status_to_apilo(status: OrderStatus, status_map: list[dict[str, Any]] | None = None) -> int | None:
    """Map unified OrderStatus back to Apilo status ID using the account's status map."""
    if not status_map:
        return None

    target_keywords: dict[OrderStatus, list[str]] = {
        OrderStatus.NEW: ["nowy", "new"],
        OrderStatus.PROCESSING: ["realizacji", "processing", "progress"],
        OrderStatus.READY_FOR_SHIPMENT: ["wysyłki", "ready", "ship"],
        OrderStatus.SHIPPED: ["wysłane", "shipped", "sent"],
        OrderStatus.DELIVERED: ["dostarczone", "delivered"],
        OrderStatus.CANCELLED: ["anulowane", "cancelled", "canceled"],
        OrderStatus.RETURNED: ["zwrot", "returned", "return"],
    }

    keywords = target_keywords.get(status, [])
    for status_entry in status_map:
        entry_name = status_entry.get("name", "").lower()
        for kw in keywords:
            if kw in entry_name:
                return int(status_entry["id"])

    return None


def map_apilo_order_to_order(
    order_data: dict[str, Any],
    account_name: str,
    status_name: str = "",
) -> Order:
    """Map an Apilo order dict to the unified Order schema."""
    items = order_data.get("orderItems", [])
    lines = _map_order_items(items)

    customer_address = _map_address(order_data.get("addressCustomer"))
    delivery_address = _map_address(order_data.get("addressDelivery"))
    invoice_address = _map_address(order_data.get("addressInvoice"))
    buyer = _map_buyer(order_data)

    status_id = order_data.get("status", 0)
    status = map_apilo_status_to_order_status(status_id, status_name)

    total_amount = 0.0
    raw_total = order_data.get("originalAmountTotalWithTax")
    if raw_total is not None:
        try:
            total_amount = float(raw_total)
        except (ValueError, TypeError):
            total_amount = sum(line.unit_price * line.quantity for line in lines)

    currency = order_data.get("originalCurrency", "PLN")

    payment_type_id = order_data.get("paymentType", 0)
    _payment_status = order_data.get("paymentStatus", 0)

    notes_list = order_data.get("orderNotes", [])
    notes = "; ".join(n.get("comment", "") for n in notes_list if n.get("comment"))

    return Order(
        external_id=order_data.get("id", ""),
        account_name=account_name,
        status=status,
        buyer=buyer,
        delivery_address=delivery_address or customer_address,
        invoice_address=invoice_address,
        lines=lines,
        total_amount=total_amount,
        currency=currency,
        payment_type=str(payment_type_id),
        delivery_method=str(order_data.get("carrierId", "")),
        created_at=order_data.get("createdAt") or order_data.get("orderedAt"),
        updated_at=order_data.get("updatedAt"),
        notes=notes,
        raw_data=order_data,
    )


def map_apilo_product_to_product(product_data: dict[str, Any]) -> Product:
    """Map an Apilo product dict to the unified Product schema."""
    price_with_tax = 0.0
    with contextlib.suppress(ValueError, TypeError):
        price_with_tax = float(product_data.get("priceWithTax", 0))

    return Product(
        external_id=str(product_data.get("id", "")),
        sku=product_data.get("sku", ""),
        ean=product_data.get("ean", ""),
        name=product_data.get("name", "") or product_data.get("groupName", ""),
        description=product_data.get("description", ""),
        unit=product_data.get("unit", "szt.") or "szt.",
        price=price_with_tax,
        currency="PLN",
        stock_quantity=float(product_data.get("quantity", 0)),
        attributes={
            "original_code": product_data.get("originalCode", ""),
            "weight": product_data.get("weight"),
            "tax": product_data.get("tax", ""),
            "status": product_data.get("status", 1),
        },
    )


def _map_address(address_data: dict[str, Any] | None) -> Address | None:
    if not address_data:
        return None

    name = address_data.get("name", "")
    parts = name.split(" ", 1)

    street = address_data.get("streetName", "")
    street_number = address_data.get("streetNumber", "")

    return Address(
        first_name=parts[0] if parts else "",
        last_name=parts[1] if len(parts) > 1 else "",
        company_name=address_data.get("companyName", ""),
        street=street,
        building_number=street_number,
        city=address_data.get("city", ""),
        postal_code=address_data.get("zipCode", ""),
        country_code=address_data.get("country", "PL"),
        phone=address_data.get("phone", ""),
        email=address_data.get("email", ""),
    )


def _map_buyer(order_data: dict[str, Any]) -> Buyer:
    customer = order_data.get("addressCustomer") or {}
    name = customer.get("name", "")
    parts = name.split(" ", 1) if name else []

    return Buyer(
        external_id=order_data.get("id", ""),
        login=order_data.get("customerLogin", ""),
        email=customer.get("email", ""),
        first_name=parts[0] if parts else "",
        last_name=parts[1] if len(parts) > 1 else "",
        company_name=customer.get("companyName", ""),
        is_guest=not order_data.get("customerLogin"),
    )


def _map_order_items(items: list[dict[str, Any]]) -> list[OrderLine]:
    lines: list[OrderLine] = []
    for item in items:
        unit_price = 0.0
        with contextlib.suppress(ValueError, TypeError):
            unit_price = float(item.get("originalPriceWithTax", 0))

        tax_rate: float | None = None
        tax_str = item.get("tax")
        if tax_str is not None:
            with contextlib.suppress(ValueError, TypeError):
                tax_rate = float(tax_str)

        lines.append(
            OrderLine(
                external_id=str(item.get("id", "")),
                offer_id=str(item.get("idExternal", "")),
                product_id=str(item.get("productId", "")),
                sku=item.get("sku", "") or "",
                ean=item.get("ean", "") or "",
                name=item.get("originalName", ""),
                quantity=float(item.get("quantity", 1)),
                unit=item.get("unit", "szt.") or "szt.",
                unit_price=unit_price,
                currency="PLN",
                tax_rate=tax_rate,
            )
        )
    return lines
