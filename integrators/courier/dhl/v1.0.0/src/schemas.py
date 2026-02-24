"""DHL-specific request/response schemas."""

from pydantic import BaseModel, Field


class DhlCredentials(BaseModel):
    username: str
    password: str
    account_number: str = ""
    sap_number: str = ""


class DhlExtras(BaseModel):
    pickup_date: str = ""
    pickup_time_from: str = ""
    pickup_time_to: str = ""
    book_courier: bool = False
    insurance: bool = False
    insurance_value: float = 0
    return_on_delivery: bool = False
    proof_of_delivery: bool = False


class LabelRequest(BaseModel):
    waybill_numbers: list[str]
    credentials: DhlCredentials


class CreateShipmentRequest(BaseModel):
    credentials: DhlCredentials
    command: dict = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Rate request / standardized response (for shipping price comparison)
# ---------------------------------------------------------------------------

class RateRequest(BaseModel):
    credentials: DhlCredentials | None = None
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
