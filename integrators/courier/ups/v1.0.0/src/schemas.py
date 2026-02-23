"""UPS-specific request/response schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# UPS service / parcel-type constants (ported from legacy create_order_commands)
# ---------------------------------------------------------------------------

UPS_LIMIT_DESCRIPTION = 50
UPS_LIMIT_EMAIL = 50
UPS_LIMIT_NAME = 35
UPS_LIMIT_CITY = 30

UPS_AVAILABLE_SERVICES = [
    "01", "02", "03", "07", "08", "11", "12", "13", "14", "17",
    "54", "59", "65",
    "M2", "M3", "M4", "M5", "M6", "M7",
    "70", "71", "72", "74", "75",
    "82", "83", "84", "85", "86", "96",
]

UPS_AVAILABLE_PARCEL_TYPES = [
    "01", "02", "03", "04",
    "21", "24", "25", "30",
    "2a", "2b", "2c",
    "56", "57", "58", "59", "60", "61", "62", "63", "64", "65", "66", "67",
]


# ---------------------------------------------------------------------------
# Credentials
# ---------------------------------------------------------------------------

class UpsCredentials(BaseModel):
    """Credentials sent with every UPS API request.

    * ``login`` / ``password`` — OAuth2 client_id / client_secret
    * ``shipper_number`` — 6-character UPS account/shipper number
    * ``access_token`` — current Bearer token (populated after login)
    """
    login: str
    password: str
    shipper_number: str = ""
    access_token: str = ""


# ---------------------------------------------------------------------------
# UPS extras (per-shipment options)
# ---------------------------------------------------------------------------

class UpsExtras(BaseModel):
    delivery12: bool = False
    insurance: bool = False
    insurance_value: float = 0
    insurance_curr: str = "PLN"
    custom_document_ids: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Parcel / shipment-party models
# ---------------------------------------------------------------------------

class Parcel(BaseModel):
    height: float
    length: float
    weight: float
    width: float
    quantity: int = 1
    parcel_type: str = Field(default="02", alias="type")

    model_config = {"populate_by_name": True}


class ShipmentParty(BaseModel):
    first_name: str = ""
    last_name: str = ""
    company_name: str | None = Field(default=None, alias="company")
    contact_person: str | None = None
    email: str | None = None
    phone: str | None = None
    building_number: str = ""
    city: str = ""
    country_code: str = "PL"
    postal_code: str = ""
    street: str = ""
    province: str | None = None
    tax_number: str | None = None

    model_config = {"populate_by_name": True}


class PaymentDetails(BaseModel):
    account_id: str | None = None
    payer_type: str | None = None
    payment_method: str | None = None
    transfer_title: str | None = None
    customs_payer_type: str | None = None
    receiver_account_id: str | None = None


# ---------------------------------------------------------------------------
# API request / response models
# ---------------------------------------------------------------------------

class CreateShipmentRequest(BaseModel):
    credentials: UpsCredentials
    service_name: str = Field(alias="serviceName", default="11")
    content: str | None = None
    content2: str | None = None
    parcels: list[Parcel]
    shipment_date: str = ""
    cod: bool = False
    cod_value: float | None = Field(default=None, alias="codValue")
    cod_curr: str = "PLN"
    shipper: ShipmentParty
    receiver: ShipmentParty
    payment: PaymentDetails | None = None
    extras: dict = Field(default_factory=dict)

    model_config = {"populate_by_name": True}


class LabelRequest(BaseModel):
    waybill_numbers: list[str]
    credentials: UpsCredentials


class StatusRequest(BaseModel):
    credentials: UpsCredentials


class UploadDocumentRequest(BaseModel):
    credentials: UpsCredentials
    waybill: str
    filename: str
    file: str  # base64-encoded file content
    document_type: str = Field(default="001", alias="type")

    model_config = {"populate_by_name": True}


class LoginRequest(BaseModel):
    credentials: UpsCredentials


# ---------------------------------------------------------------------------
# Normalised response schemas
# ---------------------------------------------------------------------------

class AddressResponse(BaseModel):
    building_number: str = ""
    city: str = ""
    country_code: str = "PL"
    line1: str = ""
    line2: str = ""
    post_code: str = ""
    street: str = ""


class ShipmentPartyResponse(BaseModel):
    first_name: str = ""
    last_name: str = ""
    contact_person: str | None = None
    phone: str | None = None
    email: str | None = None
    address: AddressResponse = Field(default_factory=AddressResponse)


class CreateOrderResponse(BaseModel):
    id: str
    waybill_number: str
    shipper: ShipmentPartyResponse
    receiver: ShipmentPartyResponse
    order_status: str = Field(default="CREATED", alias="orderStatus")

    model_config = {"populate_by_name": True}
