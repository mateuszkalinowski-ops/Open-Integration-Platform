from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class OrderStatus(str, Enum):
    NEW = "NEW"
    PROCESSING = "PROCESSING"
    READY_FOR_SHIPMENT = "READY_FOR_SHIPMENT"
    SHIPPED = "SHIPPED"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"
    RETURNED = "RETURNED"


class Address(BaseModel):
    first_name: str = ""
    last_name: str = ""
    company_name: str = ""
    street: str = ""
    building_number: str = ""
    apartment_number: str = ""
    city: str = ""
    postal_code: str = ""
    country_code: str = "PL"
    phone: str = ""
    email: str = ""


class Buyer(BaseModel):
    external_id: str
    login: str = ""
    email: str = ""
    first_name: str = ""
    last_name: str = ""
    company_name: str = ""
    is_guest: bool = False
    address: Address | None = None


class OrderLine(BaseModel):
    external_id: str
    offer_id: str = ""
    product_id: str = ""
    sku: str = ""
    ean: str = ""
    name: str = ""
    quantity: float = 1.0
    unit: str = "szt."
    unit_price: float = 0.0
    currency: str = "PLN"
    tax_rate: float | None = None


class Order(BaseModel):
    external_id: str
    account_name: str = ""
    status: OrderStatus = OrderStatus.NEW
    buyer: Buyer | None = None
    delivery_address: Address | None = None
    invoice_address: Address | None = None
    lines: list[OrderLine] = Field(default_factory=list)
    total_amount: float = 0.0
    currency: str = "PLN"
    payment_type: str = ""
    delivery_method: str = ""
    created_at: datetime | None = None
    updated_at: datetime | None = None
    notes: str = ""
    raw_data: dict[str, Any] = Field(default_factory=dict)


class OrdersPage(BaseModel):
    orders: list[Order]
    page: int = 1
    total: int = 0
    has_next: bool = False


class StockItem(BaseModel):
    sku: str
    ean: str = ""
    product_id: str = ""
    quantity: float
    warehouse_id: str = ""


class Product(BaseModel):
    external_id: str
    sku: str = ""
    ean: str = ""
    name: str = ""
    description: str = ""
    unit: str = "szt."
    price: float = 0.0
    currency: str = "PLN"
    stock_quantity: float = 0.0
    attributes: dict[str, Any] = Field(default_factory=dict)


class PriceUpdate(BaseModel):
    product_id: str
    price: float
    currency: str = "PLN"
