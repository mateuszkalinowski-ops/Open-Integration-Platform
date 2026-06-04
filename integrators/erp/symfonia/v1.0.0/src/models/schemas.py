"""Pydantic schemas for the Symfonia ERP WebAPI connector."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

# --- Contractor ---


class ContractorAddress(BaseModel):
    street: str | None = None
    city: str | None = None
    postal_code: str | None = None
    country: str | None = None


class Contractor(BaseModel):
    id: int | None = None
    code: str | None = Field(None, alias="Code")
    name: str | None = Field(None, alias="Name")
    short_name: str | None = Field(None, alias="ShortName")
    nip: str | None = Field(None, alias="Nip")
    regon: str | None = Field(None, alias="Regon")
    pesel: str | None = Field(None, alias="Pesel")
    street: str | None = Field(None, alias="Street")
    city: str | None = Field(None, alias="City")
    postal_code: str | None = Field(None, alias="PostalCode")
    country: str | None = Field(None, alias="Country")
    phone: str | None = Field(None, alias="Phone")
    email: str | None = Field(None, alias="Email")
    www: str | None = Field(None, alias="Www")
    is_active: bool | None = Field(None, alias="IsActive")
    is_deleted: bool | None = Field(None, alias="IsDeleted")

    model_config = {"populate_by_name": True}


class ContractorCreate(BaseModel):
    code: str
    name: str
    short_name: str | None = None
    nip: str | None = None
    regon: str | None = None
    pesel: str | None = None
    street: str | None = None
    city: str | None = None
    postal_code: str | None = None
    country: str | None = None
    phone: str | None = None
    email: str | None = None

    def to_symfonia_payload(self) -> dict:
        payload: dict = {"Code": self.code, "Name": self.name}
        if self.short_name:
            payload["ShortName"] = self.short_name
        if self.nip:
            payload["Nip"] = self.nip
        if self.regon:
            payload["Regon"] = self.regon
        if self.pesel:
            payload["Pesel"] = self.pesel
        if self.street:
            payload["Street"] = self.street
        if self.city:
            payload["City"] = self.city
        if self.postal_code:
            payload["PostalCode"] = self.postal_code
        if self.country:
            payload["Country"] = self.country
        if self.phone:
            payload["Phone"] = self.phone
        if self.email:
            payload["Email"] = self.email
        return payload


class ContractorUpdate(BaseModel):
    id: int | None = None
    code: str | None = None
    name: str | None = None
    short_name: str | None = None
    nip: str | None = None
    regon: str | None = None
    pesel: str | None = None
    street: str | None = None
    city: str | None = None
    postal_code: str | None = None
    country: str | None = None
    phone: str | None = None
    email: str | None = None

    def to_symfonia_payload(self) -> dict:
        payload: dict = {}
        if self.id is not None:
            payload["Id"] = self.id
        if self.code is not None:
            payload["Code"] = self.code
        if self.name is not None:
            payload["Name"] = self.name
        if self.short_name is not None:
            payload["ShortName"] = self.short_name
        if self.nip is not None:
            payload["Nip"] = self.nip
        if self.regon is not None:
            payload["Regon"] = self.regon
        if self.pesel is not None:
            payload["Pesel"] = self.pesel
        if self.street is not None:
            payload["Street"] = self.street
        if self.city is not None:
            payload["City"] = self.city
        if self.postal_code is not None:
            payload["PostalCode"] = self.postal_code
        if self.country is not None:
            payload["Country"] = self.country
        if self.phone is not None:
            payload["Phone"] = self.phone
        if self.email is not None:
            payload["Email"] = self.email
        return payload


# --- Product ---


class Product(BaseModel):
    id: int | None = None
    code: str | None = Field(None, alias="Code")
    name: str | None = Field(None, alias="Name")
    ean: str | None = Field(None, alias="EAN")
    vat_rate: str | None = Field(None, alias="VatRate")
    unit: str | None = Field(None, alias="BaseUnitOfMeasure")
    weight: float | None = Field(None, alias="Weight")
    description: str | None = Field(None, alias="Description")
    group: str | None = Field(None, alias="Group")
    is_active: bool | None = Field(None, alias="IsActive")
    is_deleted: bool | None = Field(None, alias="IsDeleted")

    model_config = {"populate_by_name": True}


class ProductCreate(BaseModel):
    code: str
    name: str
    ean: str | None = None
    vat_rate: str | None = None
    unit: str | None = None
    weight: float | None = None
    description: str | None = None
    group: str | None = None

    def to_symfonia_payload(self) -> dict:
        payload: dict = {"Code": self.code, "Name": self.name}
        if self.ean:
            payload["EAN"] = self.ean
        if self.vat_rate:
            payload["VatRate"] = self.vat_rate
        if self.unit:
            payload["BaseUnitOfMeasure"] = self.unit
        if self.weight is not None:
            payload["Weight"] = self.weight
        if self.description:
            payload["Description"] = self.description
        if self.group:
            payload["Group"] = self.group
        return payload


class ProductUpdate(BaseModel):
    id: int | None = None
    code: str | None = None
    name: str | None = None
    ean: str | None = None
    vat_rate: str | None = None
    unit: str | None = None
    weight: float | None = None
    description: str | None = None

    def to_symfonia_payload(self) -> dict:
        payload: dict = {}
        if self.id is not None:
            payload["Id"] = self.id
        if self.code is not None:
            payload["Code"] = self.code
        if self.name is not None:
            payload["Name"] = self.name
        if self.ean is not None:
            payload["EAN"] = self.ean
        if self.vat_rate is not None:
            payload["VatRate"] = self.vat_rate
        if self.unit is not None:
            payload["BaseUnitOfMeasure"] = self.unit
        if self.weight is not None:
            payload["Weight"] = self.weight
        if self.description is not None:
            payload["Description"] = self.description
        return payload


# --- Inventory ---


class InventoryState(BaseModel):
    product_id: int | None = None
    product_code: str | None = None
    product_name: str | None = None
    warehouse_id: int | None = None
    warehouse_code: str | None = None
    warehouse_name: str | None = None
    quantity_available: float = 0.0
    quantity_reserved: float = 0.0
    quantity_total: float = 0.0
    unit: str | None = None


# --- Documents ---


class DocumentPosition(BaseModel):
    product_id: int | None = None
    product_code: str | None = None
    product_name: str | None = None
    quantity: float = 0.0
    unit: str | None = None
    net_price: float = 0.0
    gross_price: float = 0.0
    vat_rate: str | None = None
    discount_percent: float = 0.0
    net_value: float = 0.0
    gross_value: float = 0.0


class SalesDocument(BaseModel):
    id: int | None = None
    number: str | None = None
    document_type: str | None = None
    status: str | None = None
    buyer_id: int | None = None
    buyer_code: str | None = None
    buyer_name: str | None = None
    buyer_nip: str | None = None
    recipient_id: int | None = None
    recipient_code: str | None = None
    recipient_name: str | None = None
    positions: list[DocumentPosition] = Field(default_factory=list)
    net_total: float = 0.0
    gross_total: float = 0.0
    vat_total: float = 0.0
    currency: str = "PLN"
    issue_date: str | None = None
    sale_date: str | None = None


class PurchaseDocument(BaseModel):
    id: int | None = None
    number: str | None = None
    document_type: str | None = None
    status: str | None = None
    supplier_id: int | None = None
    supplier_code: str | None = None
    supplier_name: str | None = None
    positions: list[DocumentPosition] = Field(default_factory=list)
    net_total: float = 0.0
    gross_total: float = 0.0
    vat_total: float = 0.0
    currency: str = "PLN"
    issue_date: str | None = None


# --- Orders ---


class Order(BaseModel):
    id: int | None = None
    number: str | None = None
    status: str | None = None
    contractor_id: int | None = None
    contractor_code: str | None = None
    contractor_name: str | None = None
    positions: list[DocumentPosition] = Field(default_factory=list)
    net_total: float = 0.0
    gross_total: float = 0.0
    currency: str = "PLN"
    issue_date: str | None = None
    expected_date: str | None = None


# --- Paginated response ---


class PaginatedResponse(BaseModel):
    items: list = Field(default_factory=list)
    total: int = 0
    page: int = 1
    page_size: int = 50


# --- Filter request ---


class FilterRequest(BaseModel):
    query: str
    mode: str = "hmf"


class DateRangeFilter(BaseModel):
    date_from: str
    date_to: str
    buyer_code: str | None = None
    buyer_id: str | None = None
    supplier_code: str | None = None
    supplier_id: str | None = None
    recipient_code: str | None = None


# --- Sync state ---


class SyncState(BaseModel):
    entity_type: str
    last_sync: datetime | None = None
    last_sync_date_param: str | None = None
