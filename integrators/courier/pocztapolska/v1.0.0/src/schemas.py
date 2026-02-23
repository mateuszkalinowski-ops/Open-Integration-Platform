"""Poczta Polska-specific request/response schemas."""

from pydantic import BaseModel, Field


class PocztaPolskaCredentials(BaseModel):
    login: str
    password: str


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
    transfer_title: str = ""


class PocztaPolskaExtras(BaseModel):
    dispatch_office: str = ""
    not_clear_envelope: bool = False
    not_send_envelope: bool = False
    book_courier: bool = False
    pickup_time_from: str = ""
    rod: bool = False
    return_documents_address_id: str | None = None
    delivery_saturday: bool = False
    bringing_pack: bool = False
    customer_shipment_number: str | None = None
    insurance: bool = False
    insurance_value: float = 0
    receiver_type: str = ""
    correspondence_address_id: str | None = None
    check_shipment_content_by_receiver: bool = False
    voivodeship_id: str = ""
    delivery9: bool = False
    delivery12: bool = False


class CreateShipmentRequest(BaseModel):
    credentials: PocztaPolskaCredentials
    shipper: ShipmentParty = Field(default_factory=ShipmentParty)
    receiver: ShipmentParty = Field(default_factory=ShipmentParty)
    parcels: list[Parcel] = Field(default_factory=list)
    payment: Payment = Field(default_factory=Payment)
    content: str = ""
    shipment_date: str = ""
    cod: bool = False
    cod_value: float = 0
    extras: dict = Field(default_factory=dict)


class LabelRequest(BaseModel):
    credentials: PocztaPolskaCredentials
    waybill_numbers: list[str] = Field(default_factory=list)
    external_id: list[str] | None = None


class PointsRequest(BaseModel):
    credentials: PocztaPolskaCredentials
    voivodeship_id: str = ""
