"""Shopify Admin REST API Pydantic models.

Based on Shopify Admin API 2024-07 documentation for orders,
products, customers, fulfillments, and inventory.
"""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

# --- Enums ---


class ShopifyOrderFinancialStatus(str, Enum):
    PENDING = "pending"
    AUTHORIZED = "authorized"
    PARTIALLY_PAID = "partially_paid"
    PAID = "paid"
    PARTIALLY_REFUNDED = "partially_refunded"
    REFUNDED = "refunded"
    VOIDED = "voided"


class ShopifyOrderFulfillmentStatus(str, Enum):
    """Shopify order-level fulfillment status.

    Note: Shopify returns null (not "unfulfilled") for orders with no fulfillments.
    The ShopifyOrder model uses `ShopifyOrderFulfillmentStatus | None` to handle this.
    """

    FULFILLED = "fulfilled"
    PARTIAL = "partial"
    RESTOCKED = "restocked"


class ShopifyFulfillmentStatus(str, Enum):
    PENDING = "pending"
    OPEN = "open"
    SUCCESS = "success"
    CANCELLED = "cancelled"
    ERROR = "error"
    FAILURE = "failure"


class ShopifyOrderCancelReason(str, Enum):
    CUSTOMER = "customer"
    FRAUD = "fraud"
    INVENTORY = "inventory"
    DECLINED = "declined"
    OTHER = "other"


# --- Price / Money ---


class ShopifyPriceSet(BaseModel):
    shop_money: dict[str, str] | None = None
    presentment_money: dict[str, str] | None = None


# --- Address ---


class ShopifyAddress(BaseModel):
    first_name: str = ""
    last_name: str = ""
    company: str | None = None
    address1: str = ""
    address2: str | None = None
    city: str = ""
    province: str | None = None
    province_code: str | None = None
    country: str = ""
    country_code: str = ""
    zip: str = ""
    phone: str | None = None
    name: str = ""
    latitude: float | None = None
    longitude: float | None = None


# --- Customer ---


class ShopifyCustomer(BaseModel):
    id: int
    email: str = ""
    first_name: str = ""
    last_name: str = ""
    phone: str | None = None
    orders_count: int = 0
    total_spent: str = "0.00"
    verified_email: bool = False
    default_address: ShopifyAddress | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    tags: str = ""
    note: str | None = None


# --- Line Items ---


class ShopifyLineItem(BaseModel):
    id: int
    variant_id: int | None = None
    product_id: int | None = None
    title: str = ""
    variant_title: str | None = None
    sku: str = ""
    quantity: int = 1
    price: str = "0.00"
    total_discount: str = "0.00"
    fulfillable_quantity: int = 0
    fulfillment_status: str | None = None
    grams: int = 0
    name: str = ""
    vendor: str | None = None
    taxable: bool = True
    tax_lines: list[dict[str, Any]] = Field(default_factory=list)
    properties: list[dict[str, str]] = Field(default_factory=list)


# --- Fulfillment ---


class ShopifyFulfillmentLineItem(BaseModel):
    id: int
    fulfillment_order_id: int | None = None
    quantity: int = 1


class ShopifyFulfillment(BaseModel):
    id: int | None = None
    order_id: int | None = None
    status: ShopifyFulfillmentStatus = ShopifyFulfillmentStatus.PENDING
    tracking_company: str | None = None
    tracking_number: str | None = None
    tracking_numbers: list[str] = Field(default_factory=list)
    tracking_url: str | None = None
    tracking_urls: list[str] = Field(default_factory=list)
    created_at: datetime | None = None
    updated_at: datetime | None = None
    line_items: list[ShopifyLineItem] = Field(default_factory=list)


class ShopifyFulfillmentOrder(BaseModel):
    id: int
    order_id: int
    status: str = ""
    fulfill_at: datetime | None = None
    line_items: list[ShopifyFulfillmentLineItem] = Field(default_factory=list)


# --- Shipping Lines ---


class ShopifyShippingLine(BaseModel):
    id: int | None = None
    title: str = ""
    price: str = "0.00"
    code: str | None = None
    source: str | None = None


# --- Note Attributes ---


class ShopifyNoteAttribute(BaseModel):
    name: str
    value: str


# --- Order ---


class ShopifyOrder(BaseModel):
    id: int
    name: str = ""
    order_number: int | None = None
    email: str = ""
    phone: str | None = None
    financial_status: ShopifyOrderFinancialStatus = ShopifyOrderFinancialStatus.PENDING
    fulfillment_status: ShopifyOrderFulfillmentStatus | None = None
    cancel_reason: ShopifyOrderCancelReason | None = None
    cancelled_at: datetime | None = None
    closed_at: datetime | None = None
    currency: str = "USD"
    total_price: str = "0.00"
    subtotal_price: str = "0.00"
    total_tax: str = "0.00"
    total_discounts: str = "0.00"
    total_shipping_price_set: ShopifyPriceSet | None = None
    customer: ShopifyCustomer | None = None
    billing_address: ShopifyAddress | None = None
    shipping_address: ShopifyAddress | None = None
    line_items: list[ShopifyLineItem] = Field(default_factory=list)
    fulfillments: list[ShopifyFulfillment] = Field(default_factory=list)
    shipping_lines: list[ShopifyShippingLine] = Field(default_factory=list)
    note: str | None = None
    note_attributes: list[ShopifyNoteAttribute] = Field(default_factory=list)
    tags: str = ""
    created_at: datetime | None = None
    updated_at: datetime | None = None
    processed_at: datetime | None = None


class ShopifyOrdersResponse(BaseModel):
    orders: list[ShopifyOrder] = Field(default_factory=list)


class ShopifyOrderResponse(BaseModel):
    order: ShopifyOrder


# --- Product ---


class ShopifyProductImage(BaseModel):
    id: int | None = None
    product_id: int | None = None
    src: str = ""
    alt: str | None = None
    position: int = 1


class ShopifyProductVariant(BaseModel):
    id: int | None = None
    product_id: int | None = None
    title: str = ""
    sku: str = ""
    barcode: str | None = None
    price: str = "0.00"
    compare_at_price: str | None = None
    weight: float = 0.0
    weight_unit: str = "kg"
    inventory_item_id: int | None = None
    inventory_quantity: int = 0
    inventory_management: str | None = None
    fulfillment_service: str = "manual"
    option1: str | None = None
    option2: str | None = None
    option3: str | None = None
    taxable: bool = True
    created_at: datetime | None = None
    updated_at: datetime | None = None


class ShopifyProduct(BaseModel):
    id: int | None = None
    title: str = ""
    body_html: str | None = None
    vendor: str = ""
    product_type: str = ""
    handle: str = ""
    status: str = "active"
    tags: str = ""
    variants: list[ShopifyProductVariant] = Field(default_factory=list)
    images: list[ShopifyProductImage] = Field(default_factory=list)
    created_at: datetime | None = None
    updated_at: datetime | None = None


class ShopifyProductsResponse(BaseModel):
    products: list[ShopifyProduct] = Field(default_factory=list)


class ShopifyProductResponse(BaseModel):
    product: ShopifyProduct


# --- Inventory ---


class ShopifyInventoryLevel(BaseModel):
    inventory_item_id: int
    location_id: int
    available: int | None = None
    updated_at: datetime | None = None


class ShopifyInventoryLevelsResponse(BaseModel):
    inventory_levels: list[ShopifyInventoryLevel] = Field(default_factory=list)


# --- Fulfillment Orders (for fulfillment creation) ---


class ShopifyFulfillmentOrdersResponse(BaseModel):
    fulfillment_orders: list[ShopifyFulfillmentOrder] = Field(default_factory=list)


# --- Auth Status ---


class AuthStatusResponse(BaseModel):
    account_name: str
    authenticated: bool
    shop_url: str = ""
    api_version: str = ""
