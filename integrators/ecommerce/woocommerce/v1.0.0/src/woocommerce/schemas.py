"""WooCommerce REST API v3 Pydantic models.

Based on WooCommerce REST API documentation and the reference Java implementation.
"""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

# --- Enums ---


class WooOrderStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    ON_HOLD = "on-hold"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"
    FAILED = "failed"
    TRASH = "trash"


class WooProductType(str, Enum):
    SIMPLE = "simple"
    GROUPED = "grouped"
    EXTERNAL = "external"
    VARIABLE = "variable"


class WooProductStatus(str, Enum):
    DRAFT = "draft"
    PENDING = "pending"
    PRIVATE = "private"
    PUBLISH = "publish"


# --- Common ---


class WooMetaData(BaseModel):
    id: int | None = None
    key: str = ""
    value: Any = None


class WooAddress(BaseModel):
    first_name: str = Field(default="", alias="first_name")
    last_name: str = Field(default="", alias="last_name")
    company: str = ""
    address_1: str = Field(default="", alias="address_1")
    address_2: str = Field(default="", alias="address_2")
    city: str = ""
    state: str = ""
    postcode: str = ""
    country: str = ""

    model_config = {"populate_by_name": True}


class WooBilling(WooAddress):
    email: str = ""
    phone: str = ""


# --- Order models ---


class WooOrderLineItem(BaseModel):
    id: int | None = None
    name: str = ""
    product_id: int | None = Field(default=None, alias="product_id")
    variation_id: int | None = Field(default=None, alias="variation_id")
    quantity: float = 1.0
    tax_class: str = Field(default="", alias="tax_class")
    subtotal: str = "0"
    subtotal_tax: str = Field(default="0", alias="subtotal_tax")
    total: str = "0"
    total_tax: str = Field(default="0", alias="total_tax")
    sku: str = ""
    price: float = 0.0
    meta_data: list[WooMetaData] = Field(default_factory=list, alias="meta_data")

    model_config = {"populate_by_name": True}


class WooShippingLine(BaseModel):
    id: int | None = None
    method_title: str = Field(default="", alias="method_title")
    method_id: str = Field(default="", alias="method_id")
    total: str = "0"
    total_tax: str = Field(default="0", alias="total_tax")
    meta_data: list[WooMetaData] = Field(default_factory=list, alias="meta_data")

    model_config = {"populate_by_name": True}


class WooOrder(BaseModel):
    id: int
    number: str = ""
    order_key: str = Field(default="", alias="order_key")
    status: WooOrderStatus = WooOrderStatus.PENDING
    currency: str = "PLN"
    total: str = "0"
    total_tax: str = Field(default="0", alias="total_tax")
    customer_id: int = Field(default=0, alias="customer_id")
    customer_note: str = Field(default="", alias="customer_note")
    billing: WooBilling | None = None
    shipping: WooAddress | None = None
    payment_method: str = Field(default="", alias="payment_method")
    payment_method_title: str = Field(default="", alias="payment_method_title")
    date_created: datetime | None = Field(default=None, alias="date_created")
    date_modified: datetime | None = Field(default=None, alias="date_modified")
    line_items: list[WooOrderLineItem] = Field(default_factory=list, alias="line_items")
    shipping_lines: list[WooShippingLine] = Field(default_factory=list, alias="shipping_lines")
    meta_data: list[WooMetaData] = Field(default_factory=list, alias="meta_data")

    model_config = {"populate_by_name": True}


# --- Product models ---


class WooProductImage(BaseModel):
    id: int | None = None
    src: str = ""
    name: str = ""
    alt: str = ""


class WooProductCategory(BaseModel):
    id: int | None = None
    name: str = ""
    slug: str = ""


class WooProductAttribute(BaseModel):
    id: int | None = None
    name: str = ""
    position: int = 0
    visible: bool = True
    variation: bool = False
    options: list[str] = Field(default_factory=list)


class WooProductDimensions(BaseModel):
    length: str = ""
    width: str = ""
    height: str = ""


class WooProduct(BaseModel):
    id: int | None = None
    name: str = ""
    slug: str = ""
    sku: str = ""
    type: WooProductType = WooProductType.SIMPLE
    status: WooProductStatus = WooProductStatus.PUBLISH
    description: str = ""
    short_description: str = Field(default="", alias="short_description")
    regular_price: str = Field(default="", alias="regular_price")
    sale_price: str = Field(default="", alias="sale_price")
    price: str = ""
    manage_stock: bool = Field(default=False, alias="manage_stock")
    stock_quantity: int | None = Field(default=None, alias="stock_quantity")
    stock_status: str = Field(default="instock", alias="stock_status")
    weight: str = ""
    dimensions: WooProductDimensions | None = None
    categories: list[WooProductCategory] = Field(default_factory=list)
    images: list[WooProductImage] = Field(default_factory=list)
    attributes: list[WooProductAttribute] = Field(default_factory=list)
    meta_data: list[WooMetaData] = Field(default_factory=list, alias="meta_data")
    date_created: datetime | None = Field(default=None, alias="date_created")
    date_modified: datetime | None = Field(default=None, alias="date_modified")

    model_config = {"populate_by_name": True}


# --- Customer models ---


class WooCustomer(BaseModel):
    id: int | None = None
    email: str = ""
    first_name: str = Field(default="", alias="first_name")
    last_name: str = Field(default="", alias="last_name")
    role: str = ""
    username: str = ""
    billing: WooBilling | None = None
    shipping: WooAddress | None = None
    is_paying_customer: bool = Field(default=False, alias="is_paying_customer")
    date_created: datetime | None = Field(default=None, alias="date_created")
    date_modified: datetime | None = Field(default=None, alias="date_modified")

    model_config = {"populate_by_name": True}


# --- Auth status ---


class AuthStatusResponse(BaseModel):
    account_name: str
    authenticated: bool
    store_url: str = ""
    api_version: str = ""
