"""InPost International 2025 — request/response schemas.

Ported from meriship version_international_2025 DTOs.
Key differences from 2024:
- OAuth2 token endpoint: /oauth2/token (not /auth/token)
- Shipping API: /shipping/v2/organizations/{orgId}/shipments
- Tracking API: /tracking/v1/parcels (no auth header required)
- Pickups API: /pickups/v1/organizations/{orgId}/one-time-pickups
- Location API: /location/v1/points
- Returns API: /returns/v1/organizations/{orgId}/shipments
- Phone is a plain string in shipping (not PhoneNumber object)
- create_shipment returns trackingNumber directly
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Credentials
# ---------------------------------------------------------------------------


class InpostCredentials(BaseModel):
    organization_id: str = Field(description="InPost organization ID (login / client_id)")
    client_secret: str = Field(description="InPost client_secret (password_ext)")
    access_token: str | None = Field(default=None, description="Cached access token")
    sandbox_mode: bool = Field(default=False, description="Use sandbox API instead of production")


# ---------------------------------------------------------------------------
# Shipping request DTOs
# ---------------------------------------------------------------------------


class ShippingContactInfo(BaseModel):
    company_name: str | None = Field(default=None, alias="companyName")
    first_name: str = Field(..., alias="firstName")
    last_name: str = Field(..., alias="lastName")
    phone: str = Field(...)
    email: str = Field(...)
    language_code: str | None = Field(default=None, alias="languageCode")

    model_config = {"populate_by_name": True}


class ShippingAddress(BaseModel):
    country_code: str = Field(..., alias="countryCode")
    street: str = Field(...)
    house_number: str | None = Field(default=None, alias="houseNumber")
    flat_number: str | None = Field(default=None, alias="flatNumber")
    city: str = Field(...)
    postal_code: str = Field(..., alias="postalCode")

    model_config = {"populate_by_name": True}


class AnyPoint(BaseModel):
    country_code: str = Field(..., alias="countryCode")
    shipping_method: Literal["APM", "PUDO", "HUB", "ANY_POINT"] = Field(..., alias="shippingMethod")
    subdivision_code: str | None = Field(default=None, alias="subdivisionCode")

    model_config = {"populate_by_name": True}


class DestinationPoint(BaseModel):
    country_code: str = Field(..., alias="countryCode")
    point_id: str = Field(..., alias="pointId")

    model_config = {"populate_by_name": True}


class ReturnDestination(BaseModel):
    recipient: ShippingContactInfo = Field(...)
    address: ShippingAddress


class ShippingCustomReferences(BaseModel):
    custom: dict[str, str] = {}


class StandardValueAdded(BaseModel):
    id_: Literal["priority"] = Field(..., alias="id")
    value: Literal["STANDARD", "EXPRESS"]

    model_config = {"populate_by_name": True}


class FlagValueAdded(BaseModel):
    id_: Literal["cross_dock"] = Field(..., alias="id")

    model_config = {"populate_by_name": True}


class CurrencyValueAdded(BaseModel):
    id_: Literal["additionalCover"] = Field(..., alias="id")
    value: str = Field(...)
    currency: Literal["PLN", "EUR"]

    model_config = {"populate_by_name": True}


class ShippingDimensions(BaseModel):
    length: float
    width: float
    height: float
    unit: Literal["MM", "CM", "M"]


class ShippingWeight(BaseModel):
    amount: float = Field(...)
    unit: Literal["G", "KG"]


class ShippingLabel(BaseModel):
    type_: Literal["PLAIN_TEXT", "BARCODE"] = Field(..., alias="type")
    content: str = Field(...)

    model_config = {"populate_by_name": True}


class ShippingRemarks(BaseModel):
    original_tracking_number: str | None = Field(default=None, alias="originalTrackingNumber")
    label: list[ShippingLabel] | None = None

    model_config = {"populate_by_name": True}


class StandardParcel(BaseModel):
    remarks: ShippingRemarks | None = None
    references: ShippingCustomReferences | None = None
    type_: Literal["STANDARD"] = Field(default="STANDARD", alias="type")
    dimensions: ShippingDimensions
    weight: ShippingWeight

    model_config = {"populate_by_name": True}


class RvmVolume(BaseModel):
    amount: int | None = Field(...)
    unit: Literal["L"] = "L"


class RvmParcel(BaseModel):
    remarks: ShippingRemarks | None = None
    references: ShippingCustomReferences | None = None
    type_: Literal["RVM"] = Field(default="RVM", alias="type")
    seal_number: str = Field(..., alias="sealNumber")
    volume: RvmVolume
    collection_type: Literal["Manual", "Automatic"] = Field(..., alias="collectionType")
    content_type: Literal["Plastic", "Glass", "Aluminium", "Mixed"] = Field(..., alias="contentType")

    model_config = {"populate_by_name": True}


class ShippingCreateShipmentDto(BaseModel):
    enable_drop_off_code: bool | None = Field(default=None, alias="enableDropOffCode")
    sender: ShippingContactInfo = Field(...)
    recipient: ShippingContactInfo = Field(...)
    origin: ShippingAddress | AnyPoint
    destination: ShippingAddress | DestinationPoint
    return_destination: ReturnDestination | None = Field(default=None, alias="returnDestination")
    references: ShippingCustomReferences | None = None
    value_added_services: list[StandardValueAdded | FlagValueAdded | CurrencyValueAdded] | None = Field(
        default=None,
        alias="valueAddedServices",
    )
    parcels: list[RvmParcel] | list[StandardParcel]

    model_config = {"populate_by_name": True}


# ---------------------------------------------------------------------------
# Returns DTOs
# ---------------------------------------------------------------------------


class ReturnsContactInfo(BaseModel):
    company_name: str | None = Field(default=None, alias="companyName")
    first_name: str | None = Field(default=None, alias="firstName")
    last_name: str | None = Field(default=None, alias="lastName")
    phone: str = Field(...)
    email: str = Field(...)

    model_config = {"populate_by_name": True}


class ReturnsOrigin(BaseModel):
    country_code: str = Field(..., alias="countryCode")

    model_config = {"populate_by_name": True}


class ReturnsAddress(BaseModel):
    country_code: str = Field(..., alias="countryCode")
    street: str = Field(...)
    house_number: str = Field(..., alias="houseNumber")
    flat_number: str | None = Field(default=None, alias="flatNumber")
    city: str = Field(...)
    postal_code: str = Field(..., alias="postalCode")

    model_config = {"populate_by_name": True}


class ReturnsReferences(BaseModel):
    client_id: str | None = Field(default=None, alias="clientId")
    order_number: str | None = Field(default=None, alias="orderNumber")

    model_config = {"populate_by_name": True}


class ReturnsDimensions(BaseModel):
    length: float
    width: float
    height: float
    unit: Literal["MM", "CM"]


class ReturnsWeight(BaseModel):
    amount: str = Field(...)
    unit: Literal["G", "KG"]


class ReturnsLabel(BaseModel):
    type_: Literal["PLAIN_TEXT", "BARCODE", "QRCODE"] = Field(..., alias="type")
    content: str = Field(...)

    model_config = {"populate_by_name": True}


class ReturnsRemarks(BaseModel):
    sender: str | None = None
    recipient: str | None = None
    courier: str | None = None
    label: list[ReturnsLabel] | None = None


class ReturnsParcel(BaseModel):
    remarks: ReturnsRemarks | None = None
    dimensions: ReturnsDimensions | None = None
    weight: ReturnsWeight | None = None


class ReturnsCreateShipmentDto(BaseModel):
    enable_drop_off_code: bool | None = Field(default=None, alias="enableDropOffCode")
    sender: ReturnsContactInfo = Field(...)
    recipient: ReturnsContactInfo | None = None
    origin: ReturnsOrigin | None = None
    destination: ReturnsAddress | None = None
    references: ReturnsReferences | None = None
    parcels: list[ReturnsParcel] | None = None
    expiration_date: datetime | None = Field(default=None, alias="expirationDate")

    model_config = {"populate_by_name": True}


# ---------------------------------------------------------------------------
# Pickup DTOs
# ---------------------------------------------------------------------------


class PickupPhoneNumber(BaseModel):
    prefix: str = Field(...)
    number: str = Field(...)


class PickupContactInfo(BaseModel):
    first_name: str = Field(..., alias="firstName")
    last_name: str = Field(..., alias="lastName")
    phone: PickupPhoneNumber = Field(...)
    email: str = Field(...)

    model_config = {"populate_by_name": True}


class PickupAddress(BaseModel):
    country_code: str = Field(..., alias="countryCode")
    street: str = Field(...)
    house_number: str = Field(..., alias="houseNumber")
    flat_number: str | None = Field(default=None, alias="flatNumber")
    city: str = Field(...)
    postal_code: str = Field(..., alias="postalCode")
    location_description: str | None = Field(default=None, alias="locationDescription")

    model_config = {"populate_by_name": True}


class PickupCustomReferences(BaseModel):
    custom: dict[str, str] = {}


class PickupTotalVolume(BaseModel):
    amount: int = Field(...)
    unit: Literal["L"] = "L"


class PickupVolume(BaseModel):
    item_type: Literal["PARCEL", "PALLET", "RECYCLABLE_PACKAGING"] = Field(..., alias="itemType")
    count: int = Field(...)
    total_volume: PickupTotalVolume = Field(..., alias="totalVolume")

    model_config = {"populate_by_name": True}


class PickupTime(BaseModel):
    from_: datetime = Field(..., alias="from")
    to_: datetime = Field(..., alias="to")

    model_config = {"populate_by_name": True}


class PickupsCreatePickupOrderDto(BaseModel):
    address: PickupAddress
    contact_person: PickupContactInfo = Field(..., alias="contactPerson")
    pickup_time: PickupTime | None = Field(default=None, alias="pickupTime")
    references: PickupCustomReferences | None = None
    volume: PickupVolume | None = None
    tracking_numbers: list[str] | None = Field(default=None, alias="trackingNumbers")

    model_config = {"populate_by_name": True}


# ---------------------------------------------------------------------------
# Points / location response DTOs
# ---------------------------------------------------------------------------


class PointCoordinatesDto(BaseModel):
    latitude: float = Field(...)
    longitude: float = Field(...)


class PointAddressDto(BaseModel):
    country: str | None = None
    administrative_area: str | None = Field(default=None, alias="administrativeArea")
    city: str | None = None
    postal_code: str | None = Field(default=None, alias="postalCode")
    street: str | None = None
    building_number: str | None = Field(default=None, alias="buildingNumber")

    model_config = {"populate_by_name": True}


class PointDescriptionDto(BaseModel):
    content: str
    translations: dict


class PointSectionDto(BaseModel):
    start: str
    end: str


class PointCustomerDto(BaseModel):
    monday: list[PointSectionDto]
    tuesday: list[PointSectionDto]
    wednesday: list[PointSectionDto]
    thursday: list[PointSectionDto]
    friday: list[PointSectionDto]
    saturday: list[PointSectionDto]
    sunday: list[PointSectionDto]


class PointOperatingHoursDto(BaseModel):
    customer: PointCustomerDto


class PointDto(BaseModel):
    id: str = Field(...)
    type: str
    country: str
    location_type: str = Field(..., alias="locationType")
    image_url: str = Field(..., alias="imageUrl")
    coordinates: PointCoordinatesDto
    location247: bool = Field(..., alias="location247")
    capabilities: list[dict]
    address: PointAddressDto
    description: PointDescriptionDto
    description2: PointDescriptionDto
    description3: PointDescriptionDto
    operating_hours: PointOperatingHoursDto = Field(..., alias="operatingHours")
    guaranteed_locker_temperatures: dict | None = Field(default=None, alias="guaranteedLockerTemperatures")
    distance: int | None = Field(default=None)

    model_config = {"populate_by_name": True}


class GetPointsResponse(BaseModel):
    count: int
    page: int
    per_page: int = Field(..., alias="perPage")
    total_pages: int = Field(..., alias="totalPages")
    items: list[PointDto]

    model_config = {"populate_by_name": True}


# ---------------------------------------------------------------------------
# Tracking
# ---------------------------------------------------------------------------


class Tracking(BaseModel):
    tracking_number: str | None = None
    tracking_url: str | None = None


# ---------------------------------------------------------------------------
# FastAPI request schemas
# ---------------------------------------------------------------------------


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
    flat_number: str | None = None

    model_config = {"populate_by_name": True}


class Parcel(BaseModel):
    height: float
    length: float
    weight: float
    width: float
    quantity: int | None = 1
    parcel_type: str | None = Field(default=None, alias="type")

    model_config = {"populate_by_name": True}


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
    credentials: InpostCredentials
    tracking_number: str = Field(..., alias="trackingNumber")

    model_config = {"populate_by_name": True}


class PointsQuery(BaseModel):
    credentials: InpostCredentials
    city: str | None = None
    postcode: str | None = None
    extras: dict = Field(default_factory=dict)


class PickupRequest(BaseModel):
    credentials: InpostCredentials
    shipper: ShipmentParty
    parcels: list[Parcel]
    content: str | None = None
    extras: dict = Field(default_factory=dict)
    tracking_numbers: list[str] | None = Field(default=None, alias="trackingNumbers")

    model_config = {"populate_by_name": True}


class PickupHoursRequest(BaseModel):
    credentials: InpostCredentials
    postcode: str
    country_code: str = Field("PL", alias="countryCode")

    model_config = {"populate_by_name": True}


class ReturnsShipmentRequest(BaseModel):
    credentials: InpostCredentials
    sender_phone: str = Field(..., alias="senderPhone")
    sender_email: str = Field(..., alias="senderEmail")
    sender_first_name: str | None = Field(default=None, alias="senderFirstName")
    sender_last_name: str | None = Field(default=None, alias="senderLastName")
    sender_company: str | None = Field(default=None, alias="senderCompany")
    origin_country_code: str | None = Field(default=None, alias="originCountryCode")
    destination: dict | None = None
    references: dict | None = None
    parcels: list[dict] | None = None
    enable_drop_off_code: bool | None = Field(default=None, alias="enableDropOffCode")

    model_config = {"populate_by_name": True}


# ---------------------------------------------------------------------------
# Rate request / standardized response (for shipping price comparison)
# ---------------------------------------------------------------------------


class RateRequest(BaseModel):
    credentials: InpostCredentials | None = None
    sender_postal_code: str = Field("", alias="senderPostalCode")
    sender_country_code: str = Field("PL", alias="senderCountryCode")
    receiver_postal_code: str = Field("", alias="receiverPostalCode")
    receiver_country_code: str = Field("PL", alias="receiverCountryCode")
    weight: float = 0
    length: float = 0
    width: float = 0
    height: float = 0

    model_config = {"populate_by_name": True}


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
