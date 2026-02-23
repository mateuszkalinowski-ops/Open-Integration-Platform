"""Paxy-specific request/response schemas."""

from pydantic import BaseModel, Field


class PaxyCredentials(BaseModel):
    api_key: str
    api_token: str


class Parcel(BaseModel):
    weight: float = 0
    length: float = 0
    width: float = 0
    height: float = 0
    quantity: int = 1
    parcel_type: str = "PACKAGE"


class Address(BaseModel):
    first_name: str = ""
    last_name: str = ""
    company_name: str = ""
    street: str = ""
    building_number: str = ""
    city: str = ""
    postal_code: str = ""
    country_code: str = "PL"
    email: str = ""
    phone: str = ""
    contact_person: str = ""


class CreateOrderCommand(BaseModel):
    service_name: str = ""
    shipment_date: str = ""
    content: str = ""
    cod: bool = False
    cod_value: float = 0
    parcels: list[Parcel] = Field(default_factory=list)
    shipper: Address = Field(default_factory=Address)
    receiver: Address = Field(default_factory=Address)
    extras: dict = Field(default_factory=dict)
    doc_id: str = ""


class CreateShipmentRequest(BaseModel):
    credentials: PaxyCredentials
    command: CreateOrderCommand


class LabelRequest(BaseModel):
    credentials: PaxyCredentials
    waybill_numbers: list[str]


class DeleteRequest(BaseModel):
    credentials: PaxyCredentials
    waybill_number: str


class StatusRequest(BaseModel):
    credentials: PaxyCredentials
    waybill_number: str
