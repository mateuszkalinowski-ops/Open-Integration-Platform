"""Maps Amazon SP-API objects to Pinquark unified schemas and vice versa.

Amazon order statuses: Pending, Unshipped, PartiallyShipped, Shipped, Canceled,
Unfulfillable, InvoiceUnconfirmed, PendingAvailability.
"""

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

_AMAZON_STATUS_MAP: dict[str, OrderStatus] = {
    "Pending": OrderStatus.NEW,
    "PendingAvailability": OrderStatus.NEW,
    "Unshipped": OrderStatus.PROCESSING,
    "PartiallyShipped": OrderStatus.PROCESSING,
    "Shipped": OrderStatus.SHIPPED,
    "Canceled": OrderStatus.CANCELLED,
    "Unfulfillable": OrderStatus.CANCELLED,
    "InvoiceUnconfirmed": OrderStatus.PROCESSING,
    "Delivered": OrderStatus.DELIVERED,
}

_UNIFIED_TO_AMAZON_STATUS: dict[OrderStatus, str] = {
    OrderStatus.NEW: "Unshipped",
    OrderStatus.PROCESSING: "Unshipped",
    OrderStatus.READY_FOR_SHIPMENT: "Unshipped",
    OrderStatus.SHIPPED: "Shipped",
    OrderStatus.DELIVERED: "Shipped",
    OrderStatus.CANCELLED: "Canceled",
    OrderStatus.RETURNED: "Canceled",
}


def map_amazon_status_to_order_status(amazon_status: str) -> OrderStatus:
    return _AMAZON_STATUS_MAP.get(amazon_status, OrderStatus.NEW)


def map_order_status_to_amazon(status: OrderStatus) -> str:
    return _UNIFIED_TO_AMAZON_STATUS.get(status, "Unshipped")


def map_amazon_order_to_order(
    order_data: dict[str, Any],
    order_items: list[dict[str, Any]],
    account_name: str,
) -> Order:
    """Map an Amazon order dict + order items to the unified Order schema."""
    lines = _map_order_items(order_items)

    shipping_address = _map_shipping_address(order_data.get("ShippingAddress"))
    buyer = _map_buyer(order_data)

    amazon_status = order_data.get("OrderStatus", "Pending")
    status = map_amazon_status_to_order_status(amazon_status)

    order_total = order_data.get("OrderTotal")
    total_amount = float(order_total.get("Amount", 0)) if order_total else sum(
        line.unit_price * line.quantity for line in lines
    )
    currency = order_total.get("CurrencyCode", "USD") if order_total else "USD"

    purchase_date = order_data.get("PurchaseDate")
    last_update = order_data.get("LastUpdateDate")

    return Order(
        external_id=order_data.get("AmazonOrderId", ""),
        account_name=account_name,
        status=status,
        buyer=buyer,
        delivery_address=shipping_address,
        invoice_address=None,
        lines=lines,
        total_amount=total_amount,
        currency=currency,
        payment_type=order_data.get("PaymentMethod", ""),
        delivery_method=order_data.get("ShipServiceLevel", ""),
        created_at=purchase_date,
        updated_at=last_update,
        notes="",
        raw_data=order_data,
    )


def _map_shipping_address(address_data: dict[str, Any] | None) -> Address | None:
    if not address_data:
        return None
    name = address_data.get("Name", "")
    parts = name.split(" ", 1)
    street_parts = [
        address_data.get("AddressLine1", ""),
        address_data.get("AddressLine2", ""),
        address_data.get("AddressLine3", ""),
    ]
    street = ", ".join(p for p in street_parts if p)
    return Address(
        first_name=parts[0] if parts else "",
        last_name=parts[1] if len(parts) > 1 else "",
        street=street,
        city=address_data.get("City", ""),
        postal_code=address_data.get("PostalCode", ""),
        country_code=address_data.get("CountryCode", "US"),
        phone=address_data.get("Phone", ""),
    )


def _map_buyer(order_data: dict[str, Any]) -> Buyer:
    buyer_info = order_data.get("BuyerInfo", {})
    email = buyer_info.get("BuyerEmail", "")
    name = buyer_info.get("BuyerName", "")
    parts = name.split(" ", 1) if name else []

    return Buyer(
        external_id=order_data.get("AmazonOrderId", ""),
        email=email,
        first_name=parts[0] if parts else "",
        last_name=parts[1] if len(parts) > 1 else "",
        is_guest=True,
    )


def _map_order_items(items: list[dict[str, Any]]) -> list[OrderLine]:
    lines: list[OrderLine] = []
    for item in items:
        item_price = item.get("ItemPrice")
        unit_price = 0.0
        currency = "USD"
        qty = int(item.get("QuantityOrdered", 1))
        if item_price:
            total_price = float(item_price.get("Amount", 0))
            currency = item_price.get("CurrencyCode", "USD")
            unit_price = total_price / qty if qty > 0 else total_price

        lines.append(OrderLine(
            external_id=item.get("OrderItemId", ""),
            offer_id=item.get("ASIN", ""),
            product_id=item.get("ASIN", ""),
            sku=item.get("SellerSKU", ""),
            name=item.get("Title", ""),
            quantity=float(qty),
            unit="szt.",
            unit_price=unit_price,
            currency=currency,
        ))
    return lines


def map_catalog_item_to_product(item_data: dict[str, Any]) -> Product:
    """Map an Amazon Catalog Item to the unified Product schema."""
    asin = item_data.get("asin", "")
    summaries = item_data.get("summaries", [])
    summary = summaries[0] if summaries else {}

    identifiers_groups = item_data.get("identifiers", [])
    ean = ""
    for group in identifiers_groups:
        for ident in group.get("identifiers", []):
            if ident.get("identifierType") in ("EAN", "GTIN"):
                ean = ident.get("identifier", "")
                break

    return Product(
        external_id=asin,
        sku="",
        ean=ean,
        name=summary.get("itemName", ""),
        description="",
        attributes={
            "brand": summary.get("brandName", ""),
            "manufacturer": summary.get("manufacturer", ""),
            "model_number": summary.get("modelNumber", ""),
        },
    )
