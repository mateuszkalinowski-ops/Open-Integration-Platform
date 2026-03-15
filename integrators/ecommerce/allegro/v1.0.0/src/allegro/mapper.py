"""Maps Allegro checkout forms to pinquark unified Order schema and vice versa."""

import logging
from typing import Any

from pinquark_common.schemas.ecommerce import (
    Address,
    Buyer,
    Order,
    OrderLine,
    OrderStatus,
)

from src.allegro.schemas import (
    AllegroCheckoutForm,
    CheckoutFormStatus,
    FulfillmentStatus,
)

logger = logging.getLogger(__name__)

ALLEGRO_STATUS_TO_ORDER_STATUS: dict[CheckoutFormStatus, OrderStatus] = {
    CheckoutFormStatus.READY_FOR_PROCESSING: OrderStatus.NEW,
    CheckoutFormStatus.CANCELLED: OrderStatus.CANCELLED,
    CheckoutFormStatus.BOUGHT: OrderStatus.NEW,
    CheckoutFormStatus.FILLED_IN: OrderStatus.NEW,
}

ORDER_STATUS_TO_FULFILLMENT: dict[OrderStatus, FulfillmentStatus] = {
    OrderStatus.NEW: FulfillmentStatus.NEW,
    OrderStatus.PROCESSING: FulfillmentStatus.PROCESSING,
    OrderStatus.READY_FOR_SHIPMENT: FulfillmentStatus.READY_FOR_SHIPMENT,
    OrderStatus.SHIPPED: FulfillmentStatus.SENT,
    OrderStatus.DELIVERED: FulfillmentStatus.PICKED_UP,
    OrderStatus.CANCELLED: FulfillmentStatus.CANCELLED,
}

EAN_PARAMETER_ID = "225693"


def map_checkout_to_order(
    checkout: AllegroCheckoutForm,
    account_name: str,
    product_details: dict[str, dict[str, Any]] | None = None,
) -> Order:
    """Map an Allegro checkout form to a unified Order."""
    product_details = product_details or {}

    delivery_address = None
    if checkout.delivery and checkout.delivery.address:
        addr = checkout.delivery.address
        delivery_address = Address(
            first_name=addr.first_name,
            last_name=addr.last_name,
            company_name=addr.company_name,
            street=addr.street,
            city=addr.city,
            postal_code=addr.zip_code,
            country_code=addr.country_code,
            phone=addr.phone_number,
        )

    buyer = None
    if checkout.buyer:
        b = checkout.buyer
        buyer = Buyer(
            external_id=b.id,
            login=b.login,
            email=b.email,
            first_name=b.first_name,
            last_name=b.last_name,
            company_name=b.company_name or "",
            is_guest=b.guest,
        )

    lines: list[OrderLine] = []
    for item in checkout.line_items:
        details = product_details.get(item.offer.id, {})
        lines.append(
            OrderLine(
                external_id=item.id,
                offer_id=item.offer.id,
                product_id=details.get("product_id", ""),
                sku=details.get("sku", item.offer.id),
                ean=details.get("ean", ""),
                name=item.offer.name or details.get("name", ""),
                quantity=float(item.quantity),
                unit="szt.",
                unit_price=float(item.price.amount) if item.price else 0.0,
                currency=item.price.currency if item.price else "PLN",
            )
        )

    total = 0.0
    currency = "PLN"
    if checkout.summary and checkout.summary.total_to_pay:
        total = float(checkout.summary.total_to_pay.amount)
        currency = checkout.summary.total_to_pay.currency

    return Order(
        external_id=checkout.id,
        account_name=account_name,
        status=ALLEGRO_STATUS_TO_ORDER_STATUS.get(checkout.status, OrderStatus.NEW),
        buyer=buyer,
        delivery_address=delivery_address,
        lines=lines,
        total_amount=total,
        currency=currency,
        payment_type=checkout.payment.type if checkout.payment else "",
        delivery_method=(
            checkout.delivery.method.get("name", "") if checkout.delivery and checkout.delivery.method else ""
        ),
        updated_at=checkout.updated_at,
        raw_data=checkout.model_dump(mode="json"),
    )


def order_status_to_fulfillment(status: OrderStatus) -> FulfillmentStatus:
    result = ORDER_STATUS_TO_FULFILLMENT.get(status)
    if result is None:
        raise ValueError(f"Cannot map OrderStatus.{status.value} to Allegro FulfillmentStatus")
    return result


def extract_ean_from_parameters(parameters: list[dict[str, Any]]) -> str:
    """Extract EAN (GTIN) from Allegro offer/product parameters."""
    for param in parameters:
        if param.get("id") == EAN_PARAMETER_ID:
            values = param.get("values", [])
            if values:
                return values[0]
            labels = param.get("valuesLabels", [])
            if labels:
                return labels[0]
    return ""
