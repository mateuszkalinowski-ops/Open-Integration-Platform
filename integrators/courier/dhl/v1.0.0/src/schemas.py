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
