"""Orlen Paczka-specific request/response schemas."""

from pydantic import BaseModel, Field


class OrlenPaczkaCredentials(BaseModel):
    partner_id: str
    partner_key: str


class OrlenPaczkaExtras(BaseModel):
    return_pack: bool = False
    cod_description: str = ""
    insurance: float | None = None
    custom_attributes: dict = Field(default_factory=dict)


class Parcel(BaseModel):
    parcel_type: str = "A"
    quantity: int = 1
    weight: float = 0
    width: int = 0
    height: int = 0
    length: int = 0


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


class CreateOrderCommand(BaseModel):
    shipper: ShipmentParty = Field(default_factory=ShipmentParty)
    receiver: ShipmentParty = Field(default_factory=ShipmentParty)
    parcels: list[Parcel] = Field(default_factory=list)
    content: str = ""
    cod: bool = False
    cod_value: float = 0
    extras: dict = Field(default_factory=dict)


class CreateOrderRequest(BaseModel):
    credentials: OrlenPaczkaCredentials
    command: CreateOrderCommand


class LabelRequest(BaseModel):
    waybill_numbers: list[str]
    credentials: OrlenPaczkaCredentials


class StatusRequest(BaseModel):
    credentials: OrlenPaczkaCredentials
    order_id: str


class DeleteRequest(BaseModel):
    credentials: OrlenPaczkaCredentials
    order_id: str


class PointsRequest(BaseModel):
    credentials: OrlenPaczkaCredentials


class CreateOrderResponse(BaseModel):
    id: str
    waybill_number: str
    shipper: dict = Field(default_factory=dict)
    receiver: dict = Field(default_factory=dict)
    order_status: str = "CREATED"


class Tracking(BaseModel):
    tracking_number: str
    tracking_url: str
