"""Pydantic models for InsERT Nexo orders (Zamówienia)."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class OrderType(str, Enum):
    FROM_CUSTOMER = "from_customer"
    TO_SUPPLIER = "to_supplier"


class OrderStatus(str, Enum):
    NEW = "new"
    IN_PROGRESS = "in_progress"
    PARTIALLY_REALIZED = "partially_realized"
    REALIZED = "realized"
    CANCELLED = "cancelled"


class OrderPosition(BaseModel):
    product_id: int | None = None
    product_symbol: str
    product_name: str = ""
    quantity: float = 1.0
    unit: str = "szt"
    net_price: float = 0.0
    gross_price: float = 0.0
    vat_rate: str = "23%"
    discount_percent: float = 0.0
    realized_quantity: float = 0.0


class OrderCreate(BaseModel):
    order_type: OrderType = OrderType.FROM_CUSTOMER
    contractor_symbol: str
    positions: list[OrderPosition] = Field(default_factory=list)
    expected_date: datetime | None = None
    notes: str = ""
    external_number: str = ""
    warehouse_symbol: str = ""


class OrderUpdate(BaseModel):
    status: OrderStatus | None = None
    expected_date: datetime | None = None
    notes: str | None = None
    external_number: str | None = None
    positions: list[OrderPosition] | None = None


class OrderResponse(BaseModel):
    id: int
    order_type: OrderType
    number: str
    status: OrderStatus = OrderStatus.NEW
    contractor_symbol: str = ""
    contractor_name: str = ""
    positions: list[OrderPosition] = Field(default_factory=list)
    net_total: float = 0.0
    gross_total: float = 0.0
    currency: str = "PLN"
    expected_date: datetime | None = None
    notes: str = ""
    external_number: str = ""
    warehouse_symbol: str = ""
    realization_percent: float = 0.0
    created_at: datetime | None = None
    updated_at: datetime | None = None
