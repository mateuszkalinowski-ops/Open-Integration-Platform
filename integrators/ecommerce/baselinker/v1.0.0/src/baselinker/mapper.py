"""Maps BaseLinker API objects to Pinquark unified schemas and vice versa.

BaseLinker uses custom order statuses (per-account, fetched via getOrderStatusList).
Status mapping is done by status name keywords, not fixed IDs.
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

_STATUS_KEYWORD_MAP: list[tuple[list[str], OrderStatus]] = [
    (["nowe", "new", "niezatwierdzone"], OrderStatus.NEW),
    (["w realizacji", "kompletowanie", "processing", "przygotowanie", "pakowanie"], OrderStatus.PROCESSING),
    (["gotowe", "do wysylki", "ready", "spakowane"], OrderStatus.READY_FOR_SHIPMENT),
    (["wyslane", "shipped", "w drodze", "nadane"], OrderStatus.SHIPPED),
    (["dostarczone", "delivered", "odebrane", "zrealizowane"], OrderStatus.DELIVERED),
    (["anulowane", "cancelled", "canceled", "odrzucone"], OrderStatus.CANCELLED),
    (["zwrot", "return", "returned", "reklamacja"], OrderStatus.RETURNED),
]


def map_bl_status_to_order_status(
    status_id: int,
    status_defs: dict[int, str],
) -> OrderStatus:
    """Map BaseLinker status ID to unified OrderStatus using status name keywords."""
    name = status_defs.get(status_id, "").lower().strip()
    if not name:
        return OrderStatus.NEW

    for keywords, unified_status in _STATUS_KEYWORD_MAP:
        for kw in keywords:
            if kw in name:
                return unified_status

    return OrderStatus.PROCESSING


def find_bl_status_id(
    target: OrderStatus,
    status_defs: dict[int, str],
) -> int | None:
    """Find the best BaseLinker status ID for a given unified OrderStatus."""
    for status_id, _name in status_defs.items():
        mapped = map_bl_status_to_order_status(status_id, status_defs)
        if mapped == target:
            return status_id
    return None


def map_bl_order_to_order(
    order_data: dict[str, Any],
    account_name: str,
    status_defs: dict[int, str],
) -> Order:
    """Map a BaseLinker order dict to the unified Order schema."""
    products_raw = order_data.get("products", [])
    lines = _map_order_lines(products_raw)

    delivery_address = _map_delivery_address(order_data)
    invoice_address = _map_invoice_address(order_data)
    buyer = _map_buyer(order_data)

    status_id = order_data.get("order_status_id", 0)
    status = map_bl_status_to_order_status(status_id, status_defs)

    total = sum(line.unit_price * line.quantity for line in lines)
    total += order_data.get("delivery_price", 0.0)

    return Order(
        external_id=str(order_data.get("order_id", 0)),
        account_name=account_name,
        status=status,
        buyer=buyer,
        delivery_address=delivery_address,
        invoice_address=invoice_address,
        lines=lines,
        total_amount=total,
        currency=order_data.get("currency", "PLN"),
        payment_type=order_data.get("payment_method", ""),
        delivery_method=order_data.get("delivery_method", ""),
        notes=order_data.get("user_comments", ""),
        raw_data=order_data,
    )


def _map_delivery_address(data: dict[str, Any]) -> Address | None:
    fullname = data.get("delivery_fullname", "")
    parts = fullname.split(" ", 1)
    return Address(
        first_name=parts[0] if parts else "",
        last_name=parts[1] if len(parts) > 1 else "",
        company_name=data.get("delivery_company", ""),
        street=data.get("delivery_address", ""),
        city=data.get("delivery_city", ""),
        postal_code=data.get("delivery_postcode", ""),
        country_code=data.get("delivery_country_code", "PL"),
        phone=data.get("phone", ""),
        email=data.get("email", ""),
    )


def _map_invoice_address(data: dict[str, Any]) -> Address | None:
    if not data.get("invoice_fullname") and not data.get("invoice_company"):
        return None
    fullname = data.get("invoice_fullname", "")
    parts = fullname.split(" ", 1)
    return Address(
        first_name=parts[0] if parts else "",
        last_name=parts[1] if len(parts) > 1 else "",
        company_name=data.get("invoice_company", ""),
        street=data.get("invoice_address", ""),
        city=data.get("invoice_city", ""),
        postal_code=data.get("invoice_postcode", ""),
        country_code=data.get("invoice_country_code", "PL"),
    )


def _map_buyer(data: dict[str, Any]) -> Buyer:
    fullname = data.get("delivery_fullname", "")
    parts = fullname.split(" ", 1)
    return Buyer(
        external_id=data.get("user_login", "") or str(data.get("order_id", "")),
        login=data.get("user_login", ""),
        email=data.get("email", ""),
        first_name=parts[0] if parts else "",
        last_name=parts[1] if len(parts) > 1 else "",
        company_name=data.get("delivery_company", ""),
        is_guest=not bool(data.get("user_login")),
    )


def _map_order_lines(products: list[dict[str, Any]]) -> list[OrderLine]:
    lines: list[OrderLine] = []
    for p in products:
        lines.append(
            OrderLine(
                external_id=str(p.get("order_product_id", 0)),
                offer_id=str(p.get("product_id", "")),
                product_id=str(p.get("product_id", "")),
                sku=p.get("sku", ""),
                ean=p.get("ean", ""),
                name=p.get("name", ""),
                quantity=float(p.get("quantity", 1)),
                unit="szt.",
                unit_price=float(p.get("price_brutto", 0)),
                tax_rate=float(p.get("tax_rate", 0)) if p.get("tax_rate") else None,
                currency="PLN",
            )
        )
    return lines


def map_bl_product_to_product(
    product_id: str,
    data: dict[str, Any],
    warehouse_id: int = 0,
) -> Product:
    """Map BaseLinker inventory product data to unified Product schema."""
    prices = data.get("prices", {})
    price = next(iter(prices.values()), 0.0) if prices else 0.0

    stock_data = data.get("stock", {})
    stock_qty = 0.0
    if warehouse_id and str(warehouse_id) in stock_data:
        stock_qty = float(stock_data[str(warehouse_id)])
    elif stock_data:
        stock_qty = sum(float(v) for v in stock_data.values())

    text_fields = data.get("text_fields", {})
    name = text_fields.get("name", data.get("name", ""))
    description = text_fields.get("description", "")

    return Product(
        external_id=product_id,
        sku=data.get("sku", ""),
        ean=data.get("ean", ""),
        name=name,
        description=description,
        price=float(price),
        stock_quantity=stock_qty,
    )
