"""Pydantic models for InsERT Nexo stock levels."""

from datetime import datetime

from pydantic import BaseModel, Field


class StockLevel(BaseModel):
    product_symbol: str
    product_name: str = ""
    warehouse_symbol: str = ""
    warehouse_name: str = ""
    quantity_available: float = 0.0
    quantity_reserved: float = 0.0
    quantity_ordered: float = 0.0
    quantity_total: float = 0.0
    unit: str = "szt"
    last_updated: datetime | None = None


class WarehouseStock(BaseModel):
    warehouse_symbol: str
    warehouse_name: str = ""
    items: list[StockLevel] = Field(default_factory=list)
    total_products: int = 0
    as_of: datetime | None = None


class StockQuery(BaseModel):
    warehouse_symbol: str | None = None
    product_symbols: list[str] | None = None
    only_available: bool = False
    page: int = 1
    page_size: int = 100
