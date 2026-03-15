"""InPost International 2025 Courier Integration.

Ported from meriship version_international_2025/inpost_integration.py.
Handles:
- Shipment creation via /shipping/v2 (returns trackingNumber directly)
- Label retrieval (PDF via base64)
- Shipment status tracking via /tracking/v1
- Order management (get by tracking number)
- Pickup order creation and cancellation via /pickups/v1
- Point/locker lookup via /location/v1
- Return shipment creation via /returns/v1
- Pickup cutoff time
"""

from __future__ import annotations

import base64
import json
import logging
from datetime import datetime
from http import HTTPStatus

import httpx

from src.api import (
    ApiLocation,
    ApiPickups,
    ApiReturns,
    ApiShipping,
    ApiTracking,
    handle_errors,
    refresh_credentials,
    retry_on_unauthorized,
)
from src.config import settings
from src.schemas import (
    CreateShipmentRequest,
    CurrencyValueAdded,
    InpostCredentials,
    PickupAddress,
    PickupContactInfo,
    PickupCustomReferences,
    PickupPhoneNumber,
    PickupsCreatePickupOrderDto,
    PickupTime,
    PickupTotalVolume,
    PickupVolume,
    ReturnsAddress,
    ReturnsContactInfo,
    ReturnsCreateShipmentDto,
    ReturnsDimensions,
    ReturnsOrigin,
    ReturnsParcel,
    ReturnsReferences,
    ReturnsShipmentRequest,
    ReturnsWeight,
    ShipmentParty,
    ShippingAddress,
    ShippingContactInfo,
    ShippingCreateShipmentDto,
    ShippingDimensions,
    ShippingWeight,
    StandardParcel,
    StandardValueAdded,
    Tracking,
)

logger = logging.getLogger("courier-inpost-int-2025")

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
    """InPost International 2025 REST integration."""

    TRACKING_URL = "https://inpost.pl/sledzenie-przesylek?number={tracking_number}"

    def __init__(self) -> None:
        self._client = httpx.AsyncClient(timeout=settings.rest_timeout)
        logger.info("InPost International 2025 integration initialised")

    def _get_base_url(self, credentials: InpostCredentials) -> str:
        if credentials.sandbox_mode:
            return settings.inpost_int_2025_sandbox_api_url
        return settings.inpost_int_2025_api_url

    def _shipping(self, credentials: InpostCredentials) -> ApiShipping:
        return ApiShipping(self._client, self._get_base_url(credentials))

    def _tracking(self, credentials: InpostCredentials) -> ApiTracking:
        return ApiTracking(self._client, self._get_base_url(credentials))

    def _pickups(self, credentials: InpostCredentials) -> ApiPickups:
        return ApiPickups(self._client, self._get_base_url(credentials))

    def _location(self, credentials: InpostCredentials) -> ApiLocation:
        return ApiLocation(self._client, self._get_base_url(credentials))

    def _returns(self, credentials: InpostCredentials) -> ApiReturns:
        return ApiReturns(self._client, self._get_base_url(credentials))

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
        response = await self._tracking(credentials).get_parcel_tracking_events(
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

        inpost_create_command = self._build_create_shipment_dto(command)
        response_extras: dict = {}

        tracking_number = await self._create_shipment(
            inpost_create_command,
            credentials,
        )

        if book_courier:
            pickup_dto = self._build_pickup_order_dto(command, tracking_number)
            response_extras["pickup"] = await self._create_pickup_order(
                pickup_dto,
                credentials,
            )

        tracking, _ = await self.get_tracking_info(tracking_number)

        normalized = {
            "id": tracking_number,
            "waybill_number": tracking_number,
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
        command: ShippingCreateShipmentDto,
        credentials: InpostCredentials,
    ) -> str:
        token = await self._get_api_token(credentials)
        return await self._shipping(credentials).post_create_shipment(
            organization_id=credentials.organization_id,
            shipment_data=command,
            auth_header=self._get_auth_headers(token),
        )

    @retry_on_unauthorized
    async def _create_pickup_order(
        self,
        command: PickupsCreatePickupOrderDto,
        credentials: InpostCredentials,
    ) -> dict:
        token = await self._get_api_token(credentials)
        return await self._pickups(credentials).post_create_pickup_order(
            organization_id=credentials.organization_id,
            pickup_data=command,
            auth_header=self._get_auth_headers(token),
        )

    # ------------------------------------------------------------------
    # Delete / cancel order (cancels pickup)
    # ------------------------------------------------------------------

    @handle_errors
    @retry_on_unauthorized
    async def delete_order(
        self,
        credentials: InpostCredentials,
        waybill_number: str,
        order_id: str | None = None,
    ) -> tuple[str | dict | None, int]:
        token = await self._get_api_token(credentials)
        response = await self._pickups(credentials).put_cancel_pickup_order(
            organization_id=credentials.organization_id,
            order_id=order_id or waybill_number,
            auth_header=self._get_auth_headers(token),
        )
        return response, HTTPStatus.OK

    # ------------------------------------------------------------------
    # Labels
    # ------------------------------------------------------------------

    @handle_errors
    @retry_on_unauthorized
    async def get_waybill_label_bytes(
        self,
        credentials: InpostCredentials,
        tracking_number: str,
    ) -> tuple[bytes | str, int]:
        token = await self._get_api_token(credentials)
        response = await self._shipping(credentials).get_shipment_label(
            organization_id=credentials.organization_id,
            tracking_number=tracking_number,
            accept_format="application/json",
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
        tracking_number: str,
    ) -> tuple[dict | str, int]:
        token = await self._get_api_token(credentials)
        response = await self._shipping(credentials).get_shipment_details_by_tracking_number(
            organization_id=credentials.organization_id,
            tracking_number=tracking_number,
            auth_header=self._get_auth_headers(token),
        )
        return response, HTTPStatus.OK

    # ------------------------------------------------------------------
    # Waybill number (via returns API)
    # ------------------------------------------------------------------

    @handle_errors
    @retry_on_unauthorized
    async def get_waybill_number(
        self,
        credentials: InpostCredentials,
        shipment_id: str,
    ) -> tuple[str, int]:
        token = await self._get_api_token(credentials)
        response = await self._returns(credentials).get_shipment_information(
            organization_id=credentials.organization_id,
            shipment_id=shipment_id,
            auth_header=self._get_auth_headers(token),
        )
        waybill_number = response["parcels"][0]["tracking_number"]
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
    # Points (via Location API)
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

        inpost_points = await self._location(credentials).get_points(
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
    # Returns
    # ------------------------------------------------------------------

    @handle_errors
    @retry_on_unauthorized
    async def create_return_shipment(
        self,
        credentials: InpostCredentials,
        returns_dto: ReturnsCreateShipmentDto,
    ) -> tuple[dict, int]:
        token = await self._get_api_token(credentials)
        response = await self._returns(credentials).post_create_shipment(
            organization_id=credentials.organization_id,
            shipment_data=returns_dto,
            auth_header=self._get_auth_headers(token),
        )
        return response, HTTPStatus.CREATED

    @handle_errors
    @retry_on_unauthorized
    async def get_return_label_bytes(
        self,
        credentials: InpostCredentials,
        tracking_number: str,
    ) -> tuple[bytes | str, int]:
        token = await self._get_api_token(credentials)
        response = await self._returns(credentials).get_parcel_label(
            organization_id=credentials.organization_id,
            tracking_number=tracking_number,
            accept_format="application/json",
            auth_header=self._get_auth_headers(token),
        )
        content_base64 = response["label"]["content"]
        content_bytes = base64.b64decode(content_base64)
        return content_bytes, HTTPStatus.OK

    # ------------------------------------------------------------------
    # Build DTOs from request
    # ------------------------------------------------------------------

    def _build_create_shipment_dto(self, command: CreateShipmentRequest) -> ShippingCreateShipmentDto:
        extras = command.extras.get("inpost", {})
        value_added_services: list = []

        if extras.get("insurance") is True:
            value_added_services.append(
                CurrencyValueAdded(
                    id_="additionalCover",
                    value=str(extras.get("insurance_value")),
                    currency=extras.get("insurance_curr", settings.default_currency),
                )
            )
        if priority_value := extras.get("priority"):
            value_added_services.append(
                StandardValueAdded(
                    id_="priority",
                    value=priority_value,
                )
            )
        elif extras.get("express"):
            value_added_services.append(
                StandardValueAdded(
                    id_="priority",
                    value="EXPRESS",
                )
            )

        return ShippingCreateShipmentDto(
            enable_drop_off_code=None,
            sender=ShippingContactInfo(
                company_name=command.shipper.company_name,
                first_name=command.shipper.first_name,
                last_name=command.shipper.last_name,
                phone=command.shipper.phone or "",
                email=command.shipper.email or "",
                language_code=command.shipper.country_code,
            ),
            recipient=ShippingContactInfo(
                company_name=command.receiver.company_name,
                first_name=command.receiver.first_name,
                last_name=command.receiver.last_name,
                phone=command.receiver.phone or "",
                email=command.receiver.email or "",
                language_code=command.receiver.country_code,
            ),
            origin=ShippingAddress(
                country_code=command.shipper.country_code,
                street=command.shipper.street,
                house_number=command.shipper.building_number,
                flat_number=command.shipper.flat_number,
                city=command.shipper.city,
                postal_code=command.shipper.postal_code,
            ),
            destination=ShippingAddress(
                country_code=command.receiver.country_code,
                street=command.receiver.street,
                house_number=command.receiver.building_number,
                flat_number=command.receiver.flat_number,
                city=command.receiver.city,
                postal_code=command.receiver.postal_code,
            ),
            return_destination=None,
            references=command.content,
            value_added_services=value_added_services or None,
            parcels=[
                StandardParcel(
                    dimensions=ShippingDimensions(
                        length=parcel.length,
                        width=parcel.width,
                        height=parcel.height,
                        unit="CM",
                    ),
                    weight=ShippingWeight(
                        amount=parcel.weight,
                        unit="KG",
                    ),
                )
                for parcel in command.parcels
            ],
        )

    def _build_pickup_order_dto(
        self,
        command: CreateShipmentRequest,
        tracking_number: str,
    ) -> PickupsCreatePickupOrderDto:
        extras = command.extras.get("inpost", {})
        pickup_time_from = extras.get("pickup_time_from")
        pickup_time_to = extras.get("pickup_time_to")

        pickup_time = None
        if pickup_time_from and pickup_time_to:
            pickup_time = PickupTime(
                from_=datetime.fromisoformat(pickup_time_from),
                to_=datetime.fromisoformat(pickup_time_to),
            )

        phone = self._parse_phone(command.shipper.phone or "")

        references = None
        if command.content:
            references = PickupCustomReferences(custom={"content": command.content})

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
                phone=PickupPhoneNumber(prefix=phone[0], number=phone[1]),
                email=command.shipper.email or "",
            ),
            pickup_time=pickup_time,
            references=references,
            volume=PickupVolume(
                item_type="PARCEL",
                count=len(command.parcels),
                total_volume=PickupTotalVolume(
                    amount=len(command.parcels),
                    unit="L",
                ),
            ),
            tracking_numbers=[tracking_number],
        )

    def build_returns_dto(self, request: ReturnsShipmentRequest) -> ReturnsCreateShipmentDto:
        destination = None
        if request.destination:
            destination = ReturnsAddress(
                country_code=request.destination.get("countryCode", "PL"),
                street=request.destination.get("street", ""),
                house_number=request.destination.get("houseNumber", ""),
                flat_number=request.destination.get("flatNumber"),
                city=request.destination.get("city", ""),
                postal_code=request.destination.get("postalCode", ""),
            )

        references = None
        if request.references:
            references = ReturnsReferences(
                client_id=request.references.get("clientId"),
                order_number=request.references.get("orderNumber"),
            )

        parcels = None
        if request.parcels:
            parcels = [
                ReturnsParcel(
                    dimensions=ReturnsDimensions(
                        length=p.get("length", 0),
                        width=p.get("width", 0),
                        height=p.get("height", 0),
                        unit=p.get("unit", "CM"),
                    )
                    if p.get("length")
                    else None,
                    weight=ReturnsWeight(
                        amount=str(p.get("weight", "0")),
                        unit=p.get("weightUnit", "KG"),
                    )
                    if p.get("weight")
                    else None,
                )
                for p in request.parcels
            ]

        origin = None
        if request.origin_country_code:
            origin = ReturnsOrigin(country_code=request.origin_country_code)

        return ReturnsCreateShipmentDto(
            enable_drop_off_code=request.enable_drop_off_code,
            sender=ReturnsContactInfo(
                company_name=request.sender_company,
                first_name=request.sender_first_name,
                last_name=request.sender_last_name,
                phone=request.sender_phone,
                email=request.sender_email,
            ),
            origin=origin,
            destination=destination,
            references=references,
            parcels=parcels,
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

    @staticmethod
    def _parse_phone(phone: str) -> tuple[str, str]:
        phone = phone.strip()
        prefix = "+48"
        number = phone
        if phone.startswith("+"):
            parts = phone.split(" ", 1)
            if len(parts) == 2:
                prefix = parts[0]
                number = parts[1]
        number = number.replace(" ", "")
        return prefix, number
