"""Schenker-specific request/response schemas."""

from pydantic import BaseModel, Field


class SchenkerCredentials(BaseModel):
    login: str
    password: str
    credentials_id: str = ""
    login_ext: str = ""


class ShipmentParty(BaseModel):
    first_name: str = ""
    last_name: str = ""
    street: str = ""
    building_number: str = ""
    city: str = ""
    postal_code: str = ""
    country_code: str = "PL"
    email: str = ""
    phone: str = ""
    contact_person: str = ""
    tax_number: str = ""
    client_id: str | None = None


class Parcel(BaseModel):
    weight: float = 0
    length: float = 0
    width: float = 0
    height: float = 0
    quantity: int = 1
    parcel_type: str = "PACKAGE"


class Payment(BaseModel):
    payer_type: str = "SHIPPER"
    payment_method: str = "BANK_TRANSFER"
    account_id: str = ""


class CreateShipmentRequest(BaseModel):
    credentials: SchenkerCredentials
    shipper: ShipmentParty = Field(default_factory=ShipmentParty)
    receiver: ShipmentParty = Field(default_factory=ShipmentParty)
    parcels: list[Parcel] = Field(default_factory=list)
    payment: Payment = Field(default_factory=Payment)
    content: str = ""
    service_name: str = "SYSTEM"
    cod: bool = False
    cod_value: float = 0
    extras: dict = Field(default_factory=dict)


class LabelRequest(BaseModel):
    credentials: SchenkerCredentials
    waybill_numbers: list[str] = Field(default_factory=list)


class DeleteOrderRequest(BaseModel):
    credentials: SchenkerCredentials
    waybill_number: str
