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


# ---------------------------------------------------------------------------
# Rate request / standardized response (for shipping price comparison)
# ---------------------------------------------------------------------------


class RateRequest(BaseModel):
    credentials: GlsCredentials | None = None
    sender_postal_code: str = ""
    sender_country_code: str = "PL"
    receiver_postal_code: str = ""
    receiver_country_code: str = "PL"
    weight: float = 0
    length: float = 0
    width: float = 0
    height: float = 0


class RateProduct(BaseModel):
    name: str
    price: float
    currency: str = "PLN"
    delivery_days: int | None = None
    delivery_date: str = ""
    attributes: dict = Field(default_factory=dict)


class StandardizedRateResponse(BaseModel):
    products: list[RateProduct] = Field(default_factory=list)
    source: str = ""
    raw: dict = Field(default_factory=dict)
