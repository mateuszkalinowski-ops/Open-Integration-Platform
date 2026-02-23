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
