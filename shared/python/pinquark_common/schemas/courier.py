"""Normalized courier DTOs.

Platform-agnostic models for shipment operations.
Each courier integrator maps its API responses to/from these DTOs.
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ShipmentStatus(str, Enum):
    CREATED = "CREATED"
    CONFIRMED = "CONFIRMED"
    PICKED_UP = "PICKED_UP"
    IN_TRANSIT = "IN_TRANSIT"
    OUT_FOR_DELIVERY = "OUT_FOR_DELIVERY"
    DELIVERED = "DELIVERED"
    RETURNED = "RETURNED"
    CANCELLED = "CANCELLED"
    FAILED = "FAILED"


class ParcelType(str, Enum):
    PACKAGE = "PACKAGE"
    LETTER = "LETTER"
    PALLET = "PALLET"
    ENVELOPE = "ENVELOPE"
    OTHER = "OTHER"


class PayerType(str, Enum):
    SENDER = "SENDER"
    RECIPIENT = "RECIPIENT"
    THIRD_PARTY = "THIRD_PARTY"


class Parcel(BaseModel):
    height: Decimal
    length: Decimal
    weight: Decimal
    width: Decimal
    quantity: int = 1
    parcel_type: str = "PACKAGE"


class ShipmentAddress(BaseModel):
    street: str = ""
    building_number: str = ""
    apartment_number: str = ""
    city: str = ""
    postal_code: str = ""
    country_code: str = "PL"
    province: str = ""


class ShipmentParty(BaseModel):
    first_name: str = ""
    last_name: str = ""
    company_name: str = ""
    contact_person: str = ""
    email: str = ""
    phone: str = ""
    address: ShipmentAddress = Field(default_factory=ShipmentAddress)
    tax_number: str = ""
    client_id: str = ""


class PaymentDetails(BaseModel):
    account_id: str = ""
    payer_type: str = ""
    payment_method: str = ""
    transfer_title: str = ""
    customs_payer_type: str = ""
    receiver_account_id: str = ""


class CreateShipmentCommand(BaseModel):
    """Normalized command to create a shipment across any courier.

    Courier-specific fields go into `extras` keyed by courier name,
    e.g. extras = {"dhl": {"pickup_date": "...", ...}}.
    """

    service_name: str = ""
    content: str = ""
    content2: str = ""
    parcels: list[Parcel] = Field(default_factory=list)
    shipment_date: str = ""
    cod: bool = False
    cod_value: Decimal | None = None
    cod_currency: str = "PLN"
    insurance: bool = False
    insurance_value: Decimal | None = None
    shipper: ShipmentParty = Field(default_factory=ShipmentParty)
    receiver: ShipmentParty = Field(default_factory=ShipmentParty)
    payment: PaymentDetails | None = None
    extras: dict[str, Any] = Field(default_factory=dict)


class Tracking(BaseModel):
    tracking_number: str = ""
    tracking_url: str = ""


class ShipmentResponse(BaseModel):
    """Normalized response after creating a shipment."""

    order_id: str = ""
    waybill_number: str = ""
    shipper: ShipmentParty = Field(default_factory=ShipmentParty)
    receiver: ShipmentParty = Field(default_factory=ShipmentParty)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    tracking: Tracking = Field(default_factory=Tracking)
    status: ShipmentStatus = ShipmentStatus.CREATED
    service_name: str = ""
    extras: dict[str, Any] = Field(default_factory=dict)


class ShipmentStatusUpdate(BaseModel):
    """Status update event from a courier tracking webhook or poll."""

    waybill_number: str
    status: ShipmentStatus
    timestamp: datetime
    description: str = ""
    location: str = ""
    raw_status: str = ""


class PickupPoint(BaseModel):
    """Courier pickup / drop-off point (paczkomat, point, etc.)."""

    point_id: str = ""
    name: str = ""
    address: ShipmentAddress = Field(default_factory=ShipmentAddress)
    latitude: Decimal | None = None
    longitude: Decimal | None = None
    point_type: str = ""
    operating_hours: str = ""
