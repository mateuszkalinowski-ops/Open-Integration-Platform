"""Pydantic models for InsERT Nexo products (Asortyment)."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class ProductType(str, Enum):
    GOODS = "goods"
    SERVICE = "service"
    SET = "set"


class ProductUnitOfMeasure(BaseModel):
    symbol: str
    name: str = ""
    multiplier: float = 1.0
    is_primary: bool = False


class ProductPriceInfo(BaseModel):
    price_list_name: str = ""
    net_price: float = 0.0
    gross_price: float = 0.0
    currency: str = "PLN"
    vat_rate: str = "23%"


class ProductSupplier(BaseModel):
    contractor_symbol: str
    supplier_code: str = ""
    declared_price: float = 0.0
    currency: str = "PLN"
    is_primary: bool = False


class ProductCreate(BaseModel):
    product_type: ProductType = ProductType.GOODS
    name: str
    symbol: str = ""
    ean: str = ""
    pkwiu: str = ""
    cn_code: str = ""
    vat_rate: str = "23%"
    unit_of_measure: str = "szt"
    weight_kg: float | None = None
    description: str = ""
    group: str = ""
    prices: list[ProductPriceInfo] = Field(default_factory=list)
    suppliers: list[ProductSupplier] = Field(default_factory=list)
    additional_units: list[ProductUnitOfMeasure] = Field(default_factory=list)


class ProductUpdate(BaseModel):
    name: str | None = None
    ean: str | None = None
    pkwiu: str | None = None
    cn_code: str | None = None
    vat_rate: str | None = None
    weight_kg: float | None = None
    description: str | None = None
    group: str | None = None
    prices: list[ProductPriceInfo] | None = None
    suppliers: list[ProductSupplier] | None = None


class ProductResponse(BaseModel):
    id: int
    symbol: str
    product_type: ProductType
    name: str
    ean: str = ""
    pkwiu: str = ""
    cn_code: str = ""
    vat_rate: str = ""
    unit_of_measure: str = "szt"
    weight_kg: float | None = None
    description: str = ""
    group: str = ""
    prices: list[ProductPriceInfo] = Field(default_factory=list)
    suppliers: list[ProductSupplier] = Field(default_factory=list)
    units: list[ProductUnitOfMeasure] = Field(default_factory=list)
    created_at: datetime | None = None
    updated_at: datetime | None = None
