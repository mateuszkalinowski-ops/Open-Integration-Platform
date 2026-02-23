"""GLS-specific request/response schemas."""

from pydantic import BaseModel, Field


class GlsCredentials(BaseModel):
    username: str
    password: str


class Parcel(BaseModel):
    weight: float = 0
    length: float = 0
    width: float = 0
    height: float = 0
    quantity: int = 1
    parcel_type: str = "PACKAGE"


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


class CreateShipmentRequest(BaseModel):
    credentials: GlsCredentials
    command: dict = Field(default_factory=dict)


class LabelRequest(BaseModel):
    waybill_numbers: list[str]
    credentials: GlsCredentials
    external_id: str | None = None
