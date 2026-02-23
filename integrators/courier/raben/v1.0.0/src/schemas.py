"""Raben Group — request/response schemas.

Raben Group provides freight logistics (LTL/FTL) across Europe.
Key services:
- myOrder: Transport order placement
- Track & Trace: Shipment tracking with ETA
- PCD: Photo Confirming Delivery
- myClaim: Complaint submission
- myOffer: Price offer requests

Service types:
- Cargo Classic (24/48h standard delivery)
- Cargo Premium (priority delivery)
- Cargo Premium 08/10/12/16 (time-definite delivery windows)
"""

from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Credentials
# ---------------------------------------------------------------------------

class RabenCredentials(BaseModel):
    username: str = Field(description="myRaben login / API username")
    password: str = Field(description="myRaben password / API password")
    customer_number: str | None = Field(default=None, description="Raben customer number")
    access_token: str | None = Field(default=None, description="Cached JWT access token")
    sandbox_mode: bool = Field(default=False, description="Use sandbox API instead of production")


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class ServiceType(str, Enum):
    CARGO_CLASSIC = "cargo_classic"
    CARGO_PREMIUM = "cargo_premium"
    CARGO_PREMIUM_08 = "cargo_premium_08"
    CARGO_PREMIUM_10 = "cargo_premium_10"
    CARGO_PREMIUM_12 = "cargo_premium_12"
    CARGO_PREMIUM_16 = "cargo_premium_16"


class ShipmentStatus(str, Enum):
    CREATED = "created"
    PICKED_UP = "picked_up"
    IN_TRANSIT = "in_transit"
    AT_TERMINAL = "at_terminal"
    OUT_FOR_DELIVERY = "out_for_delivery"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    EXCEPTION = "exception"
    RETURNED = "returned"


class PackageType(str, Enum):
    PALLET = "pallet"
    HALF_PALLET = "half_pallet"
    PACKAGE = "package"
    OTHER = "other"


class ClaimType(str, Enum):
    DAMAGE = "damage"
    LOSS = "loss"
    DELAY = "delay"
    OTHER = "other"


# ---------------------------------------------------------------------------
# Address / Party DTOs
# ---------------------------------------------------------------------------

class Address(BaseModel):
    street: str = Field(...)
    building_number: str | None = Field(default=None, alias="buildingNumber")
    apartment_number: str | None = Field(default=None, alias="apartmentNumber")
    city: str = Field(...)
    postal_code: str = Field(..., alias="postalCode")
    country_code: str = Field(default="PL", alias="countryCode")

    model_config = {"populate_by_name": True}


class ContactInfo(BaseModel):
    company_name: str = Field(..., alias="companyName")
    contact_person: str | None = Field(default=None, alias="contactPerson")
    phone: str = Field(...)
    email: str | None = Field(default=None)

    model_config = {"populate_by_name": True}


class ShipmentParty(BaseModel):
    company_name: str = Field(..., alias="companyName")
    contact_person: str | None = Field(default=None, alias="contactPerson")
    phone: str = Field(...)
    email: str | None = None
    street: str = Field(...)
    building_number: str | None = Field(default=None, alias="buildingNumber")
    apartment_number: str | None = Field(default=None, alias="apartmentNumber")
    city: str = Field(...)
    postal_code: str = Field(..., alias="postalCode")
    country_code: str = Field(default="PL", alias="countryCode")

    model_config = {"populate_by_name": True}


# ---------------------------------------------------------------------------
# Package DTOs
# ---------------------------------------------------------------------------

class PackageDimensions(BaseModel):
    length: float = Field(..., description="Length in cm")
    width: float = Field(..., description="Width in cm")
    height: float = Field(..., description="Height in cm")


class Package(BaseModel):
    package_type: PackageType = Field(default=PackageType.PALLET, alias="packageType")
    quantity: int = Field(default=1)
    weight: float = Field(..., description="Weight in kg")
    dimensions: PackageDimensions | None = None
    description: str | None = None
    is_stackable: bool = Field(default=True, alias="isStackable")
    ldm: float | None = Field(default=None, description="Loading meters (LDM)")

    model_config = {"populate_by_name": True}


# ---------------------------------------------------------------------------
# Transport order DTOs (myOrder)
# ---------------------------------------------------------------------------

class AdditionalServices(BaseModel):
    pcd_enabled: bool = Field(default=False, alias="pcdEnabled", description="Photo Confirming Delivery")
    email_notification: bool = Field(default=False, alias="emailNotification", description="Email notification to receiver with ETA")
    notification_email: str | None = Field(default=None, alias="notificationEmail")
    delivery_window_from: str | None = Field(default=None, alias="deliveryWindowFrom")
    delivery_window_to: str | None = Field(default=None, alias="deliveryWindowTo")
    tail_lift_pickup: bool = Field(default=False, alias="tailLiftPickup", description="Tail lift required at pickup")
    tail_lift_delivery: bool = Field(default=False, alias="tailLiftDelivery", description="Tail lift required at delivery")

    model_config = {"populate_by_name": True}


class CreateTransportOrderRequest(BaseModel):
    sender: Address = Field(...)
    sender_contact: ContactInfo = Field(..., alias="senderContact")
    receiver: Address = Field(...)
    receiver_contact: ContactInfo = Field(..., alias="receiverContact")
    packages: list[Package] = Field(...)
    service_type: ServiceType = Field(default=ServiceType.CARGO_CLASSIC, alias="serviceType")
    pickup_date: date | None = Field(default=None, alias="pickupDate")
    reference: str | None = None
    comments: str | None = None
    additional_services: AdditionalServices | None = Field(default=None, alias="additionalServices")
    cod: bool = False
    cod_amount: float | None = Field(default=None, alias="codAmount")
    cod_currency: str = Field(default="PLN", alias="codCurrency")

    model_config = {"populate_by_name": True}


class TransportOrderResponse(BaseModel):
    order_id: str = Field(..., alias="orderId")
    waybill_number: str = Field(..., alias="waybillNumber")
    status: str
    service_type: str = Field(..., alias="serviceType")
    created_at: datetime = Field(..., alias="createdAt")

    model_config = {"populate_by_name": True}


# ---------------------------------------------------------------------------
# Tracking / Status DTOs
# ---------------------------------------------------------------------------

class TrackingEvent(BaseModel):
    timestamp: datetime
    status: str
    description: str
    location: str | None = None
    terminal: str | None = None


class EtaInfo(BaseModel):
    eta_from: datetime | None = Field(default=None, alias="etaFrom")
    eta_to: datetime | None = Field(default=None, alias="etaTo")
    last_updated: datetime | None = Field(default=None, alias="lastUpdated")

    model_config = {"populate_by_name": True}


class TrackingResponse(BaseModel):
    waybill_number: str = Field(..., alias="waybillNumber")
    status: ShipmentStatus
    events: list[TrackingEvent] = Field(default_factory=list)
    eta: EtaInfo | None = None
    delivered_at: datetime | None = Field(default=None, alias="deliveredAt")

    model_config = {"populate_by_name": True}


class ShipmentStatusResponse(BaseModel):
    waybill_number: str = Field(..., alias="waybillNumber")
    status: ShipmentStatus
    status_description: str = Field(..., alias="statusDescription")
    eta: EtaInfo | None = None
    last_event: TrackingEvent | None = Field(default=None, alias="lastEvent")

    model_config = {"populate_by_name": True}


# ---------------------------------------------------------------------------
# Label DTOs
# ---------------------------------------------------------------------------

class LabelResponse(BaseModel):
    waybill_number: str = Field(..., alias="waybillNumber")
    label_format: str = Field(..., alias="labelFormat")
    label_data: bytes | None = Field(default=None, alias="labelData")

    model_config = {"populate_by_name": True}


# ---------------------------------------------------------------------------
# Delivery confirmation (PCD) DTOs
# ---------------------------------------------------------------------------

class DeliveryConfirmation(BaseModel):
    waybill_number: str = Field(..., alias="waybillNumber")
    delivered_at: datetime = Field(..., alias="deliveredAt")
    delivery_location: str | None = Field(default=None, alias="deliveryLocation")
    gps_latitude: float | None = Field(default=None, alias="gpsLatitude")
    gps_longitude: float | None = Field(default=None, alias="gpsLongitude")
    vehicle_registration: str | None = Field(default=None, alias="vehicleRegistration")
    photos: list[str] = Field(default_factory=list, description="URLs to PCD photos")
    document_url: str | None = Field(default=None, alias="documentUrl")

    model_config = {"populate_by_name": True}


# ---------------------------------------------------------------------------
# Claim DTOs (myClaim)
# ---------------------------------------------------------------------------

class CreateClaimRequest(BaseModel):
    waybill_number: str = Field(..., alias="waybillNumber")
    claim_type: ClaimType = Field(..., alias="claimType")
    description: str = Field(...)
    contact_email: str = Field(..., alias="contactEmail")
    contact_phone: str | None = Field(default=None, alias="contactPhone")
    attachments: list[str] | None = Field(default=None, description="Base64-encoded file attachments")

    model_config = {"populate_by_name": True}


class ClaimResponse(BaseModel):
    claim_id: str = Field(..., alias="claimId")
    waybill_number: str = Field(..., alias="waybillNumber")
    claim_type: ClaimType = Field(..., alias="claimType")
    status: str
    created_at: datetime = Field(..., alias="createdAt")

    model_config = {"populate_by_name": True}


# ---------------------------------------------------------------------------
# FastAPI request schemas (wrapper with credentials)
# ---------------------------------------------------------------------------

class CreateShipmentRequest(BaseModel):
    credentials: RabenCredentials
    sender: ShipmentParty
    receiver: ShipmentParty
    packages: list[Package]
    service_type: ServiceType = Field(default=ServiceType.CARGO_CLASSIC, alias="serviceType")
    pickup_date: date | None = Field(default=None, alias="pickupDate")
    reference: str | None = None
    comments: str | None = None
    pcd_enabled: bool = Field(default=False, alias="pcdEnabled")
    email_notification: bool = Field(default=False, alias="emailNotification")
    cod: bool = False
    cod_amount: float | None = Field(default=None, alias="codAmount")
    tail_lift_pickup: bool = Field(default=False, alias="tailLiftPickup")
    tail_lift_delivery: bool = Field(default=False, alias="tailLiftDelivery")

    model_config = {"populate_by_name": True}


class LabelRequest(BaseModel):
    credentials: RabenCredentials
    waybill_number: str = Field(..., alias="waybillNumber")
    format: Literal["pdf", "zpl"] = "pdf"

    model_config = {"populate_by_name": True}


class ClaimSubmitRequest(BaseModel):
    credentials: RabenCredentials
    waybill_number: str = Field(..., alias="waybillNumber")
    claim_type: ClaimType = Field(..., alias="claimType")
    description: str
    contact_email: str = Field(..., alias="contactEmail")
    contact_phone: str | None = Field(default=None, alias="contactPhone")

    model_config = {"populate_by_name": True}
