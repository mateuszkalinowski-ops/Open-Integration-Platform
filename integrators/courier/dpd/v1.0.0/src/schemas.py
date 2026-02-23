"""DPD-specific request/response schemas."""

from pydantic import BaseModel, Field


class DpdCredentials(BaseModel):
    login: str
    password: str
    master_fid: int | None = None


class DpdInfoCredentials(BaseModel):
    login: str
    password: str
    channel: str = ""


class Parcel(BaseModel):
    weight: float = 0
    length: float = 0
    width: float = 0
    height: float = 0
    quantity: int = 1
    parcel_type: str = "PACKAGE"
    content: str = ""


class ShipmentParty(BaseModel):
    first_name: str = ""
    last_name: str = ""
    company_name: str = ""
    street: str = ""
    building_number: str = ""
    city: str = ""
    postal_code: str = ""
    country_code: str = "PL"
    phone: str = ""
    email: str = ""
    contact_person: str = ""


class Payment(BaseModel):
    payment_method: str = ""
    payer_type: str = "SHIPPER"
    account_id: str = ""


class CreateShipmentRequest(BaseModel):
    credentials: DpdCredentials
    command: dict = Field(default_factory=dict)


class LabelRequest(BaseModel):
    waybill_numbers: list[str]
    credentials: DpdCredentials
    external_id: str | None = None


class ProtocolRequest(BaseModel):
    waybill_numbers: list[str]
    credentials: DpdCredentials
    session_type: str = "DOMESTIC"


class StatusRequest(BaseModel):
    credentials: DpdCredentials
    info_credentials: DpdInfoCredentials | None = None
