"""Maps Shopify orders and products to pinquark unified schemas and vice versa."""

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
from src.shopify.schemas import (
    ShopifyAddress,
    ShopifyOrder,
    ShopifyOrderFulfillmentStatus,
    ShopifyProduct,
)

logger = logging.getLogger(__name__)


# --- Order status mapping ---
# Shopify uses a combination of financial_status + fulfillment_status + cancelled_at

def map_shopify_order_status(order: ShopifyOrder) -> OrderStatus:
    """Derive unified OrderStatus from Shopify order state."""
    if order.cancelled_at is not None:
        return OrderStatus.CANCELLED

    if order.closed_at is not None:
        if order.fulfillment_status == ShopifyOrderFulfillmentStatus.FULFILLED:
            return OrderStatus.DELIVERED
        return OrderStatus.SHIPPED

    match order.fulfillment_status:
        case ShopifyOrderFulfillmentStatus.FULFILLED:
            return OrderStatus.SHIPPED
        case ShopifyOrderFulfillmentStatus.PARTIAL:
            return OrderStatus.PROCESSING
        case _:
            return OrderStatus.NEW


ORDER_STATUS_TO_SHOPIFY_ACTION: dict[OrderStatus, str] = {
    OrderStatus.CANCELLED: "cancel",
    OrderStatus.SHIPPED: "fulfill",
    OrderStatus.DELIVERED: "close",
}


# --- Order mapping ---

def map_shopify_order_to_order(
    shopify_order: ShopifyOrder,
    account_name: str,
) -> Order:
    """Map a Shopify order to the unified Order schema."""
    delivery_address = _map_address(shopify_order.shipping_address)
    invoice_address = _map_address(shopify_order.billing_address)

    buyer = None
    if shopify_order.customer:
        c = shopify_order.customer
        buyer = Buyer(
            external_id=str(c.id),
            login=c.email,
            email=c.email,
            first_name=c.first_name,
            last_name=c.last_name,
            company_name=(c.default_address.company or "") if c.default_address else "",
            is_guest=False,
        )
    elif shopify_order.email:
        buyer = Buyer(
            external_id="guest",
            login=shopify_order.email,
            email=shopify_order.email,
            first_name=shopify_order.shipping_address.first_name if shopify_order.shipping_address else "",
            last_name=shopify_order.shipping_address.last_name if shopify_order.shipping_address else "",
            is_guest=True,
        )

    lines: list[OrderLine] = []
    for item in shopify_order.line_items:
        lines.append(OrderLine(
            external_id=str(item.id),
            offer_id=str(item.variant_id or ""),
            product_id=str(item.product_id or ""),
            sku=item.sku,
            ean="",
            name=item.name or item.title,
            quantity=float(item.quantity),
            unit="szt.",
            unit_price=float(item.price),
            currency=shopify_order.currency,
        ))

    delivery_method = ""
    if shopify_order.shipping_lines:
        delivery_method = shopify_order.shipping_lines[0].title

    notes = shopify_order.note or ""

    return Order(
        external_id=str(shopify_order.id),
        account_name=account_name,
        status=map_shopify_order_status(shopify_order),
        buyer=buyer,
        delivery_address=delivery_address,
        invoice_address=invoice_address,
        lines=lines,
        total_amount=float(shopify_order.total_price),
        currency=shopify_order.currency,
        payment_type=shopify_order.financial_status.value if shopify_order.financial_status else "",
        delivery_method=delivery_method,
        created_at=shopify_order.created_at,
        updated_at=shopify_order.updated_at,
        notes=notes,
        raw_data=shopify_order.model_dump(mode="json"),
    )


def _map_address(addr: ShopifyAddress | None) -> Address | None:
    if not addr:
        return None
    street = addr.address1 or ""
    if addr.address2:
        street = f"{street}, {addr.address2}"

    return Address(
        first_name=addr.first_name or "",
        last_name=addr.last_name or "",
        company_name=addr.company or "",
        street=street,
        city=addr.city or "",
        postal_code=addr.zip or "",
        country_code=addr.country_code or "",
        phone=addr.phone or "",
    )


# --- Product mapping ---

def map_shopify_product_to_product(product: ShopifyProduct) -> Product:
    """Map a Shopify product to the unified Product schema."""
    variant = product.variants[0] if product.variants else None
    return Product(
        external_id=str(product.id),
        sku=variant.sku if variant else "",
        ean=(variant.barcode or "") if variant else "",
        name=product.title,
        description=product.body_html or "",
        unit="szt.",
        price=float(variant.price) if variant else 0.0,
        currency="",
        stock_quantity=float(variant.inventory_quantity) if variant else 0.0,
        attributes={
            "vendor": product.vendor,
            "product_type": product.product_type,
            "tags": product.tags,
            "status": product.status,
            "handle": product.handle,
            "variants_count": len(product.variants),
        },
    )


def map_product_to_shopify(product: Product) -> dict[str, Any]:
    """Map a unified Product to Shopify product create/update payload."""
    payload: dict[str, Any] = {
        "title": product.name,
    }
    if product.description:
        payload["body_html"] = product.description

    vendor = product.attributes.get("vendor", "")
    if vendor:
        payload["vendor"] = vendor

    product_type = product.attributes.get("product_type", "")
    if product_type:
        payload["product_type"] = product_type

    tags = product.attributes.get("tags", "")
    if tags:
        payload["tags"] = tags

    variant: dict[str, Any] = {}
    if product.sku:
        variant["sku"] = product.sku
    if product.ean:
        variant["barcode"] = product.ean
    if product.price > 0:
        variant["price"] = str(product.price)
    if variant:
        payload["variants"] = [variant]

    return payload
