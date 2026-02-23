"""FedEx PL-specific request/response schemas."""

from pydantic import BaseModel, Field


class FedexPlCredentials(BaseModel):
    api_key: str
    client_id: str
    courier_number: str = ""
    account_number: str = ""


class Address(BaseModel):
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


class Parcel(BaseModel):
    parcel_type: str = "PACKAGE"
    weight: float = 0
    length: float = 0
    width: float = 0
    height: float = 0


class CreateOrderCommand(BaseModel):
    shipper: Address = Field(default_factory=Address)
    receiver: Address = Field(default_factory=Address)
    parcels: list[Parcel] = Field(default_factory=list)
    shipment_date: str = ""
    content: str = ""
    cod: bool = False
    cod_value: float = 0
    extras: dict = Field(default_factory=dict)


class CreateShipmentRequest(BaseModel):
    credentials: FedexPlCredentials
    command: CreateOrderCommand


class LabelRequest(BaseModel):
    credentials: FedexPlCredentials
    waybill_numbers: list[str]
