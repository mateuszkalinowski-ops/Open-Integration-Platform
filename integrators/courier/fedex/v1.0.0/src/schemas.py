"""FedEx-specific request/response schemas."""

from pydantic import BaseModel, Field


class FedexCredentials(BaseModel):
    client_id: str
    client_secret: str


class FedexExtras(BaseModel):
    service_type: str = "FEDEX_INTERNATIONAL_PRIORITY"
    packaging_type: str = "YOUR_PACKAGING"
    account_id: str = ""


class CreateShipmentRequest(BaseModel):
    credentials: FedexCredentials
    command: dict = Field(default_factory=dict)


class DeleteShipmentRequest(BaseModel):
    credentials: FedexCredentials
    extras: dict = Field(default_factory=dict)


class LabelRequest(BaseModel):
    credentials: FedexCredentials
    waybill_numbers: list[str]


class PointsRequest(BaseModel):
    credentials: FedexCredentials
    city: str = ""
    postcode: str = ""


# ---------------------------------------------------------------------------
# Rate request / standardized response (for shipping price comparison)
# ---------------------------------------------------------------------------


class RateRequest(BaseModel):
    credentials: FedexCredentials | None = None
    sender_postal_code: str = ""
    sender_city: str = ""
    sender_country_code: str = "PL"
    receiver_postal_code: str = ""
    receiver_city: str = ""
    receiver_country_code: str = "PL"
    weight: float = 0
    length: float = 0
    width: float = 0
    height: float = 0
    account_id: str = ""


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
