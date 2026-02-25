"""Pydantic models for InsERT Nexo contractors (Podmioty)."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class ContractorType(str, Enum):
    COMPANY = "company"
    PERSON = "person"


class ContractorAddress(BaseModel):
    address_type: str = "main"
    street: str = ""
    house_number: str = ""
    apartment_number: str = ""
    postal_code: str = ""
    city: str = ""
    country: str = "PL"
    is_default: bool = True


class ContractorContact(BaseModel):
    contact_type: str
    value: str
    is_primary: bool = False


class ContractorCreate(BaseModel):
    contractor_type: ContractorType = ContractorType.COMPANY
    short_name: str
    full_name: str = ""
    nip: str = ""
    regon: str = ""
    pesel: str = ""
    first_name: str = ""
    last_name: str = ""
    addresses: list[ContractorAddress] = Field(default_factory=list)
    contacts: list[ContractorContact] = Field(default_factory=list)
    group: str = ""
    notes: str = ""
    payment_deadline_days: int | None = None
    credit_limit: float | None = None
    discount_percent: float | None = None


class ContractorUpdate(BaseModel):
    short_name: str | None = None
    full_name: str | None = None
    nip: str | None = None
    regon: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    addresses: list[ContractorAddress] | None = None
    contacts: list[ContractorContact] | None = None
    group: str | None = None
    notes: str | None = None
    payment_deadline_days: int | None = None
    credit_limit: float | None = None
    discount_percent: float | None = None


class ContractorResponse(BaseModel):
    id: int
    symbol: str
    contractor_type: ContractorType
    short_name: str
    full_name: str = ""
    nip: str = ""
    regon: str = ""
    pesel: str = ""
    first_name: str = ""
    last_name: str = ""
    addresses: list[ContractorAddress] = Field(default_factory=list)
    contacts: list[ContractorContact] = Field(default_factory=list)
    group: str = ""
    payment_deadline_days: int | None = None
    credit_limit: float | None = None
    discount_percent: float | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
