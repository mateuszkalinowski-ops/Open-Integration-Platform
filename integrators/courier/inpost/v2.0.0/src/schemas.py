"""InPost International 2024 — request/response schemas.

Ported from meriship version_international_2024 DTOs.
"""

from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Credentials
# ---------------------------------------------------------------------------


class InpostCredentials(BaseModel):
    organization_id: str = Field(description="InPost client_id (login)")
    client_secret: str = Field(description="InPost client_secret")
    access_token: str | None = Field(default=None, description="Cached access token")
    sandbox_mode: bool = Field(default=False, description="Use sandbox API instead of production")


# ---------------------------------------------------------------------------
# Shared DTOs
# ---------------------------------------------------------------------------


class PhoneNumberDto(BaseModel):
    prefix: str = Field(..., examples=["+48"])
    number: str = Field(..., examples=["123123123"])

    @staticmethod
    def from_phone_string(phone: str) -> PhoneNumberDto:
        phone = phone.strip()
        if phone.startswith("+"):
            prefix_end_index = phone.find(" ") if " " in phone else 3
            prefix = phone[:prefix_end_index]
            number = phone[prefix_end_index:].strip()
        else:
            prefix = "+48"
            number = phone
        return PhoneNumberDto(prefix=prefix, number=number)


class ContactInfoDto(BaseModel):
    company_name: str | None = Field(default=None, alias="companyName")
    first_name: str = Field(..., alias="firstName")
    last_name: str = Field(..., alias="lastName")
    email: str
    phone: PhoneNumberDto

    model_config = {"populate_by_name": True}


class AddressDto(BaseModel):
    street: str = Field(..., examples=["Marszalkowska"])
    house_number: str = Field(..., alias="houseNumber", examples=["4"])
    flat_number: str | None = Field(default=None, alias="flatNumber", examples=["28"])
    postal_code: str = Field(..., alias="postalCode", examples=["00-850"])
    city: str = Field(..., examples=["Warszawa"])
    country_code: str = Field(..., alias="countryCode", examples=["PL"])

    model_config = {"populate_by_name": True}


# ---------------------------------------------------------------------------
# Shipment creation request DTOs
# ---------------------------------------------------------------------------


class ShipmentTypeEnum(str, Enum):
    POINT_TO_POINT = "/shipments/point-to-point"
    POINT_TO_ADDRESS = "/shipments/point-to-address"
    ADDRESS_TO_POINT = "/shipments/address-to-point"
    ADDRESS_TO_ADDRESS = "/shipments/address-to-address"


class OriginPointDto(BaseModel):
    country_code: str = Field("PL", alias="countryCode", examples=["PL"])
    shipping_methods: list[str] = Field(..., alias="shippingMethods", examples=[["APM", "PUDO", "HUB"]])

    model_config = {"populate_by_name": True}


class DestinationPointDto(BaseModel):
    country_code: str = Field(..., alias="countryCode", examples=["PL"])
    point_name: str = Field(..., alias="pointName", examples=["KRA108"])

    model_config = {"populate_by_name": True}


class AddressFieldDto(BaseModel):
    address: AddressDto


class InsuranceDto(BaseModel):
    value: str = Field(..., examples=["0"])
    currency: str = Field("EUR", examples=["EUR"])


class AddedServicesDto(BaseModel):
    insurance: InsuranceDto | None = None


class CustomReferences(BaseModel):
    custom: dict[str, str] = {}


class DimensionsDto(BaseModel):
    length: str = Field(..., examples=["10"])
    width: str = Field(..., examples=["15"])
    height: str = Field(..., examples=["20"])
    unit: str = Field(..., examples=["MM", "CM", "M"])


class WeightDto(BaseModel):
    amount: str = Field(..., examples=["2"])
    unit: str = Field(..., examples=["G", "KG"])


class LabelDto(BaseModel):
    comment: str = Field(..., examples=["ADR-12343"])


class ParcelDto(BaseModel):
    type: str = Field("STANDARD", examples=["STANDARD"])
    dimensions: DimensionsDto
    weight: WeightDto
    label: LabelDto | None = None


class ShipmentDto(BaseModel):
    sender: ContactInfoDto
    recipient: ContactInfoDto
    origin: OriginPointDto | AddressFieldDto
    destination: DestinationPointDto | AddressFieldDto
    priority: str = Field(..., examples=["STANDARD"])
    value_added_services: AddedServicesDto | None = Field(default=None, alias="valueAddedServices")
    references: CustomReferences | None = None
    parcel: ParcelDto

    model_config = {"populate_by_name": True}


class CreateShipmentDTO(BaseModel):
    label_format: str = Field(..., alias="labelFormat", examples=["PDF_URL", "QUICK_SEND_CODE"])
    shipment: ShipmentDto

    model_config = {"populate_by_name": True}

    def get_shipment_type(self) -> ShipmentTypeEnum:
        origin_is_address = isinstance(self.shipment.origin, AddressFieldDto)
        destination_is_address = isinstance(self.shipment.destination, AddressFieldDto)
        match (origin_is_address, destination_is_address):
            case (True, True):
                return ShipmentTypeEnum.ADDRESS_TO_ADDRESS
            case (True, False):
                return ShipmentTypeEnum.ADDRESS_TO_POINT
            case (False, True):
                return ShipmentTypeEnum.POINT_TO_ADDRESS
            case (False, False):
                return ShipmentTypeEnum.POINT_TO_POINT
        raise ValueError("Cannot determine shipment type.")


# ---------------------------------------------------------------------------
# Shipment creation response DTOs
# ---------------------------------------------------------------------------


class ParcelNumberDto(BaseModel):
    in_post_parcel_number: str = Field(..., alias="inPostParcelNumber")
    mondial_relay_parcel_number: str = Field("", alias="mondialRelayParcelNumber")
    mondial_relay_short_parcel_number: str = Field("", alias="mondialRelayShortParcelNumber")

    model_config = {"populate_by_name": True}


class ResponseParcelDto(BaseModel):
    uuid: str = Field(...)
    parcel_numbers: ParcelNumberDto = Field(..., alias="parcelNumbers")

    model_config = {"populate_by_name": True}


class ResponseLabelDto(BaseModel):
    url: str = Field(...)
    content: str | None = None


class RoutingDto(BaseModel):
    delivery_area: str = Field(..., alias="deliverArea")
    delivery_depot_number: str = Field(..., alias="deliveryDepotNumber")

    model_config = {"populate_by_name": True}


class CreateShipmentResponseDto(BaseModel):
    label: ResponseLabelDto
    uuid: str = Field(...)
    tracking_number: str = Field(..., alias="trackingNumber")
    parcel: ResponseParcelDto
    status: str = Field(...)
    routing: RoutingDto

    model_config = {"populate_by_name": True}


# ---------------------------------------------------------------------------
# Pickup DTOs
# ---------------------------------------------------------------------------


class PickupPhoneNumber(BaseModel):
    prefix: str = Field(..., examples=["+48"])
    number: str = Field(..., examples=["123123123"])


class PickupContactInfo(BaseModel):
    first_name: str = Field(..., alias="firstName", examples=["John"])
    last_name: str = Field(..., alias="lastName", examples=["Doe"])
    phone: PickupPhoneNumber = Field(...)
    email: str = Field(...)

    model_config = {"populate_by_name": True}


class PickupAddress(BaseModel):
    country_code: str = Field(..., alias="countryCode", examples=["PL"])
    street: str = Field(...)
    house_number: str = Field(..., alias="houseNumber")
    flat_number: str | None = Field(default=None, alias="flatNumber")
    city: str = Field(...)
    postal_code: str = Field(..., alias="postalCode")
    location_description: str | None = Field(default=None, alias="locationDescription")

    model_config = {"populate_by_name": True}


class TotalWeight(BaseModel):
    amount: float = Field(...)
    unit: Literal["G", "DAG", "KG"]


class PickupVolume(BaseModel):
    item_type: Literal["PARCEL", "PALLET"] = Field(..., alias="itemType")
    count: int = Field(...)
    total_weight: TotalWeight = Field(..., alias="totalWeight")

    model_config = {"populate_by_name": True}


class PickupTime(BaseModel):
    from_: str = Field(..., alias="from", examples=["2030-10-31T10:00:00+01:00"])
    to_: str = Field(..., alias="to", examples=["2030-10-31T13:00:00+01:00"])

    model_config = {"populate_by_name": True}


class PickupsCreatePickupOrderDto(BaseModel):
    address: PickupAddress
    contact_person: PickupContactInfo = Field(..., alias="contactPerson")
    pickup_time: PickupTime | None = Field(default=None, alias="pickupTime")
    references: CustomReferences | None = None
    volume: PickupVolume

    model_config = {"populate_by_name": True}


# ---------------------------------------------------------------------------
# Points / locations response DTOs
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
    shipment_uuid: str = Field(..., alias="shipmentUuid")

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


class PickupHoursRequest(BaseModel):
    credentials: InpostCredentials
    postcode: str
    country_code: str = Field("PL", alias="countryCode")

    model_config = {"populate_by_name": True}
