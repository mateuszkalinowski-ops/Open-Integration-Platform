"""InPost International 2024 Courier Integration.

Ported from meriship version_international_2024/inpost_integration.py.
Handles:
- Shipment creation (point-to-point, point-to-address, address-to-point, address-to-address)
- Label retrieval (PDF via base64)
- Shipment status tracking
- Order management (get by UUID)
- Pickup order creation
- Locker / service-point lookup
- Pickup cutoff time
"""

from __future__ import annotations

import base64
import json
import logging
from datetime import datetime
from http import HTTPStatus
from zoneinfo import ZoneInfo

import httpx

from src.api import (
    ApiPickups,
    ApiPoints,
    ApiShipping,
    ApiTracking,
    handle_errors,
    refresh_credentials,
    retry_on_unauthorized,
)
from src.config import settings
from src.schemas import (
    AddressDto,
    AddressFieldDto,
    AddedServicesDto,
    ContactInfoDto,
    CreateShipmentDTO,
    CreateShipmentRequest,
    CreateShipmentResponseDto,
    CustomReferences,
    DimensionsDto,
    DestinationPointDto,
    InsuranceDto,
    InpostCredentials,
    OriginPointDto,
    ParcelDto,
    PhoneNumberDto,
    PickupAddress,
    PickupContactInfo,
    PickupPhoneNumber,
    PickupTime,
    PickupsCreatePickupOrderDto,
    PickupVolume,
    ShipmentDto,
    ShipmentParty,
    Tracking,
    TotalWeight,
    WeightDto,
)

logger = logging.getLogger("courier-inpost-int-2024")

GET_POINT_SCHEMA: dict = {
    "type": "",
    "name": "",
    "address": {
        "line1": "",
        "line2": "",
        "state_code": "",
        "postal_code": "",
        "country_code": "",
        "city": "",
        "longitude": "",
        "latitude": "",
    },
    "image_url": "",
    "open_hours": "",
    "option_cod": False,
    "option_send": True,
    "option_deliver": False,
    "additional_info": "",
    "distance": 0,
    "foreign_address_id": "",
}


def _deep_copy_schema(schema: dict) -> dict:
    return json.loads(json.dumps(schema))


class InpostIntegration:
    """InPost International 2024 REST integration."""

    TRACKING_URL = "https://inpost.pl/sledzenie-przesylek?number={tracking_number}"

    def __init__(self) -> None:
        self._client = httpx.AsyncClient(timeout=settings.rest_timeout)
        logger.info("InPost International 2024 integration initialised")

    def _get_base_url(self, credentials: InpostCredentials) -> str:
        if credentials.sandbox_mode:
            return settings.inpost_int_2024_sandbox_api_url
        return settings.inpost_int_2024_api_url

    def _shipping(self, credentials: InpostCredentials) -> ApiShipping:
        return ApiShipping(self._client, self._get_base_url(credentials))

    def _tracking(self, credentials: InpostCredentials) -> ApiTracking:
        return ApiTracking(self._client, self._get_base_url(credentials))

    def _pickups(self, credentials: InpostCredentials) -> ApiPickups:
        return ApiPickups(self._client, self._get_base_url(credentials))

    def _points(self, credentials: InpostCredentials) -> ApiPoints:
        return ApiPoints(self._client, self._get_base_url(credentials))

    # ------------------------------------------------------------------
    # Auth helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _get_auth_headers(token: str) -> dict[str, str]:
        return {"Authorization": f"Bearer {token}"}

    async def _get_api_token(self, credentials: InpostCredentials) -> str:
        if not credentials.access_token:
            await refresh_credentials(credentials, self._client, self._get_base_url(credentials))
        return credentials.access_token  # type: ignore[return-value]

    # ------------------------------------------------------------------
    # Order status
    # ------------------------------------------------------------------

    @handle_errors
    @retry_on_unauthorized
    async def get_order_status(
        self,
        credentials: InpostCredentials,
        waybill_number: str,
    ) -> tuple[str, int]:
        token = await self._get_api_token(credentials)
        response = await self._tracking(credentials).get_parcel_tracking_events(
            auth_header=self._get_auth_headers(token),
            tracking_numbers=[waybill_number],
        )
        status = response["parcels"][0]["status"]
        return status, HTTPStatus.OK

    # ------------------------------------------------------------------
    # Tracking info
    # ------------------------------------------------------------------

    async def get_tracking_info(
        self,
        waybill_number: str,
    ) -> tuple[Tracking, int]:
        resp = Tracking(
            tracking_number=waybill_number,
            tracking_url=self.TRACKING_URL.format(tracking_number=waybill_number),
        )
        return resp, HTTPStatus.OK

    # ------------------------------------------------------------------
    # Create shipment
    # ------------------------------------------------------------------

    @handle_errors
    async def create_order(
        self,
        credentials: InpostCredentials,
        command: CreateShipmentRequest,
    ) -> tuple[object, int]:
        request_extras = command.extras.get("inpost", {})
        book_courier = request_extras.get("book_courier", False)

        inpost_shipment_command = self._build_create_shipment_dto(command)
        response_extras: dict = {}

        order = await self._create_shipment(inpost_shipment_command, credentials)

        if book_courier:
            pickup_dto = self._build_pickup_order_dto(command)
            response_extras["pickup"] = await self._create_pickup_order(pickup_dto, credentials)

        tracking, _ = await self.get_tracking_info(order.tracking_number)

        normalized = {
            "id": order.uuid,
            "waybill_number": order.tracking_number,
            "shipper": self._normalize_shipment_party(command.shipper),
            "receiver": self._normalize_shipment_party(command.receiver),
            "orderStatus": "CREATED",
            "tracking": tracking.model_dump(),
            "extras": response_extras,
        }
        return normalized, HTTPStatus.CREATED

    @retry_on_unauthorized
    async def _create_shipment(
        self,
        command: CreateShipmentDTO,
        credentials: InpostCredentials,
    ) -> CreateShipmentResponseDto:
        token = await self._get_api_token(credentials)
        return await self._shipping(credentials).post_create_shipment(
            shipment_data=command,
            auth_header=self._get_auth_headers(token),
            shipment_type=command.get_shipment_type(),
        )

    @retry_on_unauthorized
    async def _create_pickup_order(
        self,
        command: PickupsCreatePickupOrderDto,
        credentials: InpostCredentials,
    ) -> dict:
        token = await self._get_api_token(credentials)
        return await self._pickups(credentials).post_create_pickup_order(
            pickup_data=command,
            auth_header=self._get_auth_headers(token),
        )

    # ------------------------------------------------------------------
    # Labels
    # ------------------------------------------------------------------

    @handle_errors
    @retry_on_unauthorized
    async def get_waybill_label_bytes(
        self,
        credentials: InpostCredentials,
        shipment_uuid: str,
    ) -> tuple[bytes | str, int]:
        token = await self._get_api_token(credentials)
        response = await self._shipping(credentials).get_shipment_label(
            shipment_uuid=shipment_uuid,
            auth_header=self._get_auth_headers(token),
        )
        content_base64 = response["label"]["content"]
        content_bytes = base64.b64decode(content_base64)
        return content_bytes, HTTPStatus.OK

    # ------------------------------------------------------------------
    # Get order
    # ------------------------------------------------------------------

    @handle_errors
    @retry_on_unauthorized
    async def get_order(
        self,
        credentials: InpostCredentials,
        shipment_uuid: str,
    ) -> tuple[dict | str, int]:
        token = await self._get_api_token(credentials)
        response = await self._shipping(credentials).get_shipment_details_by_uuid(
            shipment_uuid=shipment_uuid,
            auth_header=self._get_auth_headers(token),
        )
        return response, HTTPStatus.OK

    # ------------------------------------------------------------------
    # Waybill number
    # ------------------------------------------------------------------

    @handle_errors
    @retry_on_unauthorized
    async def get_waybill_number(
        self,
        credentials: InpostCredentials,
        shipment_uuid: str,
    ) -> tuple[str, int]:
        token = await self._get_api_token(credentials)
        response = await self._shipping(credentials).get_shipment_details_by_uuid(
            shipment_uuid=shipment_uuid,
            auth_header=self._get_auth_headers(token),
        )
        waybill_number = response["trackingNumber"]
        return waybill_number, HTTPStatus.OK

    # ------------------------------------------------------------------
    # Pickup hours
    # ------------------------------------------------------------------

    @handle_errors
    @retry_on_unauthorized
    async def get_pickup_hours(
        self,
        credentials: InpostCredentials,
        postal_code: str,
        country_code: str,
    ) -> tuple[object, int]:
        token = await self._get_api_token(credentials)
        response = await self._pickups(credentials).get_cutoff_pickup_time(
            postal_code=postal_code,
            country_code=country_code,
            auth_header=self._get_auth_headers(token),
        )
        return response, HTTPStatus.OK

    # ------------------------------------------------------------------
    # Points
    # ------------------------------------------------------------------

    @handle_errors
    @retry_on_unauthorized
    async def get_points(
        self,
        credentials: InpostCredentials,
        data: dict,
    ) -> tuple[dict, int]:
        token = await self._get_api_token(credentials)
        city = data.get("city")
        postal_code = data.get("postcode")

        inpost_points = await self._points(credentials).get_points(
            auth_header=self._get_auth_headers(token),
            address_city=city,
            address_postal_code=postal_code,
        )

        points: dict = {}
        for point in inpost_points.items:
            p = _deep_copy_schema(GET_POINT_SCHEMA)
            p["type"] = point.type
            p["name"] = point.id
            p["address"]["line1"] = f"{point.address.street} {point.address.building_number}"
            p["address"]["state_code"] = point.address.administrative_area or ""
            p["address"]["postal_code"] = point.address.postal_code or ""
            p["address"]["country_code"] = point.address.country or ""
            p["address"]["city"] = point.address.city or ""
            p["address"]["longitude"] = str(point.coordinates.longitude)
            p["address"]["latitude"] = str(point.coordinates.latitude)
            p["image_url"] = point.image_url
            p["open_hours"] = point.operating_hours.model_dump()
            p["distance"] = point.distance if point.distance else 0
            points[point.id] = p

        return points, HTTPStatus.OK

    # ------------------------------------------------------------------
    # Build DTOs from request
    # ------------------------------------------------------------------

    def _build_create_shipment_dto(self, command: CreateShipmentRequest) -> CreateShipmentDTO:
        extras = command.extras.get("inpost", {})
        parcel = command.parcels[0]
        target_point = extras.get("custom_attributes", {}).get("target_point")
        sending_method = extras.get("custom_attributes", {}).get("sending_method")

        sender_contact = ContactInfoDto(
            company_name=command.shipper.company_name,
            first_name=command.shipper.first_name,
            last_name=command.shipper.last_name,
            email=command.shipper.email or "",
            phone=PhoneNumberDto.from_phone_string(command.shipper.phone or ""),
        )
        receiver_contact = ContactInfoDto(
            company_name=command.receiver.company_name,
            first_name=command.receiver.first_name,
            last_name=command.receiver.last_name,
            email=command.receiver.email or "",
            phone=PhoneNumberDto.from_phone_string(command.receiver.phone or ""),
        )

        origin: OriginPointDto | AddressFieldDto
        if sending_method:
            origin = OriginPointDto(
                country_code=command.shipper.country_code,
                shipping_methods=[sending_method],
            )
        else:
            origin = AddressFieldDto(
                address=AddressDto(
                    street=command.shipper.street,
                    house_number=command.shipper.building_number,
                    postal_code=command.shipper.postal_code,
                    city=command.shipper.city,
                    country_code=command.shipper.country_code,
                ),
            )

        destination: DestinationPointDto | AddressFieldDto
        if target_point:
            destination = DestinationPointDto(
                country_code=command.receiver.country_code,
                point_name=target_point,
            )
        else:
            destination = AddressFieldDto(
                address=AddressDto(
                    street=command.receiver.street,
                    house_number=command.receiver.building_number,
                    postal_code=command.receiver.postal_code,
                    city=command.receiver.city,
                    country_code=command.receiver.country_code,
                ),
            )

        value_added_services = None
        if extras.get("insurance_value"):
            value_added_services = AddedServicesDto(
                insurance=InsuranceDto(
                    value=str(extras.get("insurance_value", "0")),
                    currency=extras.get("insurance_curr", "EUR"),
                ),
            )

        references = None
        if command.content:
            references = CustomReferences(custom={"content": command.content})

        return CreateShipmentDTO(
            label_format="PDF_URL",
            shipment=ShipmentDto(
                sender=sender_contact,
                recipient=receiver_contact,
                origin=origin,
                destination=destination,
                priority=extras.get("priority", "STANDARD"),
                value_added_services=value_added_services,
                references=references,
                parcel=ParcelDto(
                    type="STANDARD",
                    dimensions=DimensionsDto(
                        length=str(parcel.length),
                        width=str(parcel.width),
                        height=str(parcel.height),
                        unit="CM",
                    ),
                    weight=WeightDto(
                        amount=str(parcel.weight),
                        unit="KG",
                    ),
                ),
            ),
        )

    def _build_pickup_order_dto(self, command: CreateShipmentRequest) -> PickupsCreatePickupOrderDto:
        extras = command.extras.get("inpost", {})
        pickup_date = extras.get("pickup_date")
        pickup_time_from_str = extras.get("pickup_time_from")
        pickup_time_to_str = extras.get("pickup_time_to")

        pickup_time = None
        if pickup_date and pickup_time_from_str and pickup_time_to_str:
            from_ = datetime.strptime(
                f"{pickup_date} {pickup_time_from_str}", "%Y-%m-%d %H:%M",
            ).replace(tzinfo=ZoneInfo("Europe/Warsaw"))
            to_ = datetime.strptime(
                f"{pickup_date} {pickup_time_to_str}", "%Y-%m-%d %H:%M",
            ).replace(tzinfo=ZoneInfo("Europe/Warsaw"))
            pickup_time = PickupTime(from_=from_.isoformat(), to_=to_.isoformat())

        phone = PhoneNumberDto.from_phone_string(command.shipper.phone or "")

        references = None
        if command.content:
            references = CustomReferences(custom={"content": command.content})

        return PickupsCreatePickupOrderDto(
            address=PickupAddress(
                country_code=command.shipper.country_code,
                street=command.shipper.street,
                house_number=command.shipper.building_number,
                flat_number=command.shipper.flat_number,
                city=command.shipper.city,
                postal_code=command.shipper.postal_code,
            ),
            contact_person=PickupContactInfo(
                first_name=command.shipper.first_name,
                last_name=command.shipper.last_name,
                phone=PickupPhoneNumber(prefix=phone.prefix, number=phone.number),
                email=command.shipper.email or "",
            ),
            pickup_time=pickup_time,
            references=references,
            volume=PickupVolume(
                item_type="PARCEL",
                count=len(command.parcels),
                total_weight=TotalWeight(
                    amount=sum(p.weight for p in command.parcels),
                    unit="KG",
                ),
            ),
        )

    # ------------------------------------------------------------------
    # Normalization helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _normalize_shipment_party(party: ShipmentParty) -> dict:
        street = party.street
        building = party.building_number
        postal = party.postal_code
        city = party.city
        country = party.country_code
        return {
            "first_name": party.first_name,
            "last_name": party.last_name,
            "contact_person": party.contact_person or "",
            "phone": party.phone or "",
            "email": party.email or "",
            "address": {
                "building_number": building,
                "city": city,
                "country_code": country,
                "line1": f"{street} {building}",
                "line2": f"{postal} {city} {country}",
                "post_code": postal,
                "street": street,
            },
        }
