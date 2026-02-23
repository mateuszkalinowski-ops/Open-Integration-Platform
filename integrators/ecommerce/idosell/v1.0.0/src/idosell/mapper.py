"""Maps IdoSell API objects to Pinquark unified schemas and vice versa."""

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
from src.idosell.schemas import (
    IdoSellBillingAddress,
    IdoSellDeliveryAddress,
    IdoSellOrder,
    IdoSellOrderStatus,
    IdoSellProduct,
)

logger = logging.getLogger(__name__)

POLISH_LANG_IDS = {"pol", "pl"}

# ---------------------------------------------------------------------------
# Order status mapping (ported from Java IdoOrderMapper)
# ---------------------------------------------------------------------------

IDOSELL_STATUS_TO_ORDER: dict[str, OrderStatus] = {
    IdoSellOrderStatus.NEW.value: OrderStatus.NEW,
    IdoSellOrderStatus.PAYMENT_WAITING.value: OrderStatus.NEW,
    IdoSellOrderStatus.DELIVERY_WAITING.value: OrderStatus.PROCESSING,
    IdoSellOrderStatus.ON_ORDER.value: OrderStatus.PROCESSING,
    IdoSellOrderStatus.PACKED.value: OrderStatus.PROCESSING,
    IdoSellOrderStatus.PACKED_FULFILLMENT.value: OrderStatus.PROCESSING,
    IdoSellOrderStatus.WAIT_FOR_PACKAGING.value: OrderStatus.PROCESSING,
    IdoSellOrderStatus.SUSPENDED.value: OrderStatus.PROCESSING,
    IdoSellOrderStatus.BLOCKED.value: OrderStatus.PROCESSING,
    IdoSellOrderStatus.PACKED_READY.value: OrderStatus.READY_FOR_SHIPMENT,
    IdoSellOrderStatus.READY.value: OrderStatus.READY_FOR_SHIPMENT,
    IdoSellOrderStatus.WAIT_FOR_DISPATCH.value: OrderStatus.READY_FOR_SHIPMENT,
    IdoSellOrderStatus.HANDLED.value: OrderStatus.SHIPPED,
    IdoSellOrderStatus.WAIT_FOR_RECEIVE.value: OrderStatus.SHIPPED,
    IdoSellOrderStatus.FINISHED.value: OrderStatus.DELIVERED,
    IdoSellOrderStatus.FINISHED_EXT.value: OrderStatus.DELIVERED,
    IdoSellOrderStatus.RETURNED.value: OrderStatus.RETURNED,
    IdoSellOrderStatus.COMPLAINED.value: OrderStatus.RETURNED,
    IdoSellOrderStatus.CANCELED.value: OrderStatus.CANCELLED,
    IdoSellOrderStatus.ALL_CANCELED.value: OrderStatus.CANCELLED,
    IdoSellOrderStatus.FALSE.value: OrderStatus.CANCELLED,
    IdoSellOrderStatus.LOST.value: OrderStatus.CANCELLED,
    IdoSellOrderStatus.MISSING.value: OrderStatus.CANCELLED,
    IdoSellOrderStatus.JOINED.value: OrderStatus.CANCELLED,
}

ORDER_STATUS_TO_IDOSELL: dict[OrderStatus, str] = {
    OrderStatus.NEW: "new",
    OrderStatus.PROCESSING: "packed",
    OrderStatus.READY_FOR_SHIPMENT: "ready",
    OrderStatus.SHIPPED: "handled",
    OrderStatus.DELIVERED: "finished",
    OrderStatus.CANCELLED: "canceled",
    OrderStatus.RETURNED: "returned",
}


def map_idosell_order_status(status_str: str) -> OrderStatus:
    return IDOSELL_STATUS_TO_ORDER.get(status_str, OrderStatus.NEW)


def map_idosell_order_to_order(ido_order: IdoSellOrder, account_name: str) -> Order:
    """Map an IdoSell order to the unified Order schema."""
    details = ido_order.order
    client = ido_order.client

    status = OrderStatus.NEW
    if details and details.orderStatus:
        status = map_idosell_order_status(details.orderStatus.orderStatus)

    delivery_address = _map_delivery_address(client.clientDeliveryAddress if client else None)
    billing_address = _map_billing_address(client.clientBillingAddress if client else None)
    buyer = _map_buyer(client, delivery_address)
    lines = _map_order_lines(details.productsResults if details else [])

    currency = "PLN"
    total_amount = 0.0
    payment_type = ""
    delivery_method = ""
    notes = ""
    created_at = None
    updated_at = None

    if details:
        notes = details.orderNote or details.clientNoteToOrder or ""
        if details.payments:
            payment_type = details.payments.orderPaymentType
            if details.payments.orderBaseCurrency:
                currency = details.payments.orderBaseCurrency.billingCurrency or "PLN"
                total_amount = details.payments.orderBaseCurrency.orderProductsCost + \
                    details.payments.orderBaseCurrency.orderDeliveryCost
        if details.dispatch:
            delivery_method = details.dispatch.courierName
        created_at_str = details.orderAddDate
        updated_at_str = details.orderChangeDate
        if created_at_str:
            try:
                from datetime import datetime
                created_at = datetime.strptime(created_at_str, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                pass
        if updated_at_str:
            try:
                from datetime import datetime
                updated_at = datetime.strptime(updated_at_str, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                pass

    return Order(
        external_id=ido_order.orderId or str(ido_order.orderSerialNumber or ""),
        account_name=account_name,
        status=status,
        buyer=buyer,
        delivery_address=delivery_address,
        invoice_address=billing_address,
        lines=lines,
        total_amount=total_amount,
        currency=currency,
        payment_type=payment_type,
        delivery_method=delivery_method,
        created_at=created_at,
        updated_at=updated_at,
        notes=notes,
        raw_data=ido_order.model_dump(mode="json"),
    )


def _map_delivery_address(addr: IdoSellDeliveryAddress | None) -> Address | None:
    if not addr:
        return None
    return Address(
        first_name=addr.clientDeliveryAddressFirstName,
        last_name=addr.clientDeliveryAddressLastName,
        company_name=addr.clientDeliveryAddressFirm,
        street=addr.clientDeliveryAddressStreet,
        city=addr.clientDeliveryAddressCity,
        postal_code=addr.clientDeliveryAddressZipCode,
        country_code=addr.clientDeliveryAddressCountry or "PL",
        phone=addr.clientDeliveryAddressPhone1,
    )


def _map_billing_address(addr: IdoSellBillingAddress | None) -> Address | None:
    if not addr:
        return None
    return Address(
        first_name=addr.clientFirstName,
        last_name=addr.clientLastName,
        company_name=addr.clientFirm,
        street=addr.clientStreet,
        city=addr.clientCity,
        postal_code=addr.clientZipCode,
        country_code=addr.clientCountryName or "PL",
        phone=addr.clientPhone1,
    )


def _map_buyer(client: Any | None, delivery_addr: Address | None) -> Buyer:
    if not client or not client.clientAccount:
        return Buyer(
            external_id="",
            is_guest=True,
            first_name=delivery_addr.first_name if delivery_addr else "",
            last_name=delivery_addr.last_name if delivery_addr else "",
        )

    account = client.clientAccount
    return Buyer(
        external_id=str(account.clientId) if account.clientId else "",
        login=account.clientLogin,
        email=account.clientEmail,
        first_name=delivery_addr.first_name if delivery_addr else "",
        last_name=delivery_addr.last_name if delivery_addr else "",
        company_name=delivery_addr.company_name if delivery_addr else "",
        is_guest=False,
    )


def _map_order_lines(products: list[Any]) -> list[OrderLine]:
    lines: list[OrderLine] = []
    for idx, product in enumerate(products):
        lines.append(OrderLine(
            external_id=str(product.productId or idx),
            product_id=str(product.productId or ""),
            sku=product.productCode,
            name=product.productName,
            quantity=product.productQuantity,
            unit_price=product.productOrderPrice,
        ))
    return lines


def map_idosell_product_to_product(ido_product: IdoSellProduct) -> Product:
    """Map an IdoSell product to the unified Product schema."""
    name = ""
    description = ""
    for desc in ido_product.productDescriptionsLangData:
        if desc.langId.lower() in POLISH_LANG_IDS:
            name = desc.productName
            description = desc.productDescription
            break
    if not name and ido_product.productDescriptionsLangData:
        name = ido_product.productDescriptionsLangData[0].productName
        description = ido_product.productDescriptionsLangData[0].productDescription

    ean = ""
    if ido_product.productSizesAttributes:
        ean = ido_product.productSizesAttributes[0].productSizeCodeExternal

    stock_quantity = 0.0
    if ido_product.productStocksData:
        for sq in ido_product.productStocksData.productStocksQuantities:
            for sd in sq.productSizesData:
                stock_quantity += sd.productSizeQuantity

    unit = "szt."
    if ido_product.productUnit:
        unit = ido_product.productUnit.unitName or unit

    return Product(
        external_id=str(ido_product.productId or ""),
        sku=ido_product.productDisplayedCode,
        ean=ean,
        name=name,
        description=description,
        unit=unit,
        price=ido_product.productPosPrice,
        currency=ido_product.currencyId or "PLN",
        stock_quantity=stock_quantity,
    )


def order_status_to_idosell(status: OrderStatus) -> str:
    result = ORDER_STATUS_TO_IDOSELL.get(status)
    if result is None:
        raise ValueError(f"Cannot map OrderStatus.{status.value} to IdoSell status")
    return result
