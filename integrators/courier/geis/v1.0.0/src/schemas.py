"""Geis-specific request/response schemas."""

from pydantic import BaseModel, Field


class GeisCredentials(BaseModel):
    customer_code: str
    password: str
    default_language: str = "PL"


class GeisExtras(BaseModel):
    geis_export: bool = True
    book_courier: bool = False
    insurance: bool = False
    insurance_value: float = 0
    insurance_curr: str = "PLN"
    pickup_date: str = ""
    pickup_time_from: str = ""
    pickup_time_to: str = ""


class Parcel(BaseModel):
    parcel_type: str = "KS"
    quantity: int = 1
    weight: float = 0
    width: int = 0
    height: int = 0
    length: int = 0


class Payment(BaseModel):
    account_id: str = ""
    payment_method: str = ""
    payer_type: str = ""


class ShipmentParty(BaseModel):
    first_name: str = ""
    last_name: str = ""
    company_name: str = ""
    email: str = ""
    phone: str = ""
    street: str = ""
    building_number: str = ""
    city: str = ""
    postal_code: str = ""
    country_code: str = "PL"
    contact_person: str = ""


class CreateOrderCommand(BaseModel):
    shipper: ShipmentParty = Field(default_factory=ShipmentParty)
    receiver: ShipmentParty = Field(default_factory=ShipmentParty)
    parcels: list[Parcel] = Field(default_factory=list)
    content: str = ""
    shipment_date: str = ""
    cod: bool = False
    cod_value: float = 0
    cod_curr: str = "PLN"
    payment: Payment = Field(default_factory=Payment)
    extras: dict = Field(default_factory=dict)


class CreateOrderRequest(BaseModel):
    credentials: GeisCredentials
    command: CreateOrderCommand


class LabelRequest(BaseModel):
    waybill_numbers: list[str]
    credentials: GeisCredentials


class StatusRequest(BaseModel):
    credentials: GeisCredentials
    waybill_number: str


class DeleteRequest(BaseModel):
    credentials: GeisCredentials
    waybill_number: str


class OrderDetailRequest(BaseModel):
    credentials: GeisCredentials
    waybill_number: str


class CreateOrderResponse(BaseModel):
    id: str
    waybill_number: str
    shipper: dict = Field(default_factory=dict)
    receiver: dict = Field(default_factory=dict)
    order_status: str = "CREATED"
