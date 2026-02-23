"""InPost-specific request/response schemas."""

from pydantic import BaseModel, Field


class InpostCredentials(BaseModel):
    organization_id: str = Field(description="InPost organization ID (login)")
    api_token: str = Field(description="InPost API bearer token (password)")
    sandbox_mode: bool = Field(default=False, description="Use sandbox API instead of production")


class InpostExtras(BaseModel):
    custom_attributes: dict = Field(default_factory=dict)
    delivery_saturday: bool = False
    delivery9: bool = False
    delivery12: bool = False
    delivery_sms: bool = False
    delivery_email: bool = False
    rod: bool = False
    insurance: bool = False
    insurance_value: float = 0
    return_pack: bool = False


class Parcel(BaseModel):
    height: float
    length: float
    weight: float
    width: float
    quantity: int | None = 1
    parcel_type: str | None = Field(default=None, alias="type")


class ShipmentParty(BaseModel):
    first_name: str
    last_name: str
    contact_person: str | None = None
    email: str | None = None
    phone: str | None = None
    company_name: str | None = Field(default=None, alias="company")
    building_number: str
    city: str
    country_code: str = "PL"
    postal_code: str
    street: str
    tax_number: str | None = None
    client_id: str | None = None
    province: str | None = None


class CreateShipmentRequest(BaseModel):
    credentials: InpostCredentials
    service_name: str = Field(alias="serviceName")
    extras: dict = Field(default_factory=dict)
    content: str | None = None
    parcels: list[Parcel]
    cod: bool = False
    cod_value: float | None = Field(default=None, alias="codValue")
    shipper: ShipmentParty
    receiver: ShipmentParty

    model_config = {"populate_by_name": True}


class LabelRequest(BaseModel):
    waybill_numbers: list[str]
    credentials: InpostCredentials


class PointsQuery(BaseModel):
    credentials: InpostCredentials
    city: str | None = None
    postcode: str | None = None
    extras: dict = Field(default_factory=dict)


class Tracking(BaseModel):
    tracking_number: str | None = None
    tracking_url: str | None = None
