"""InPost Courier Integration — migrated from meriship codebase.

Handles all InPost ShipX REST API interactions including:
- Shipment creation (simplified mode)
- Label retrieval (PDF)
- Shipment status tracking
- Order management (get, delete)
- Locker / service-point lookup
- Waybill number retrieval with retry
"""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime
from http import HTTPStatus
from typing import ClassVar

import httpx

from src.config import settings
from src.schemas import (
    CreateShipmentRequest,
    InpostCredentials,
    ShipmentParty,
    Tracking,
)

logger = logging.getLogger("courier-inpost")

# ---------------------------------------------------------------------------
# Utility helpers (ported from app.integrations.utils / schema_templates)
# ---------------------------------------------------------------------------

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

GET_TRACKING_SCHEMA: dict = {
    "tracking_number": "",
    "tracking_url": None,
}


def get_extras(data: dict, namespace: str | None = None) -> dict:
    """Extract the ``extras`` sub-dict, optionally narrowed to *namespace*."""
    if "extras" not in data:
        return {}
    obj = data["extras"]
    if isinstance(obj, str):
        obj = json.loads(obj)
    if not isinstance(obj, dict):
        raise ValueError('extras must be a JSON object, e.g. {"inpost": {...}}')
    if namespace:
        obj = obj.get(namespace, {})
        if not isinstance(obj, dict):
            raise ValueError(f"extras.{namespace} must be a dict")
    return obj


def _deep_copy_schema(schema: dict) -> dict:
    """Return a deep copy of a nested dict template."""
    return json.loads(json.dumps(schema))


# ---------------------------------------------------------------------------
# InPost Integration
# ---------------------------------------------------------------------------


class InpostIntegration:
    """InPost REST (ShipX) integration.

    Implements shipment creation (simplified mode), label retrieval,
    order status, tracking, point lookup, and deletion.
    """

    TRACKING_URL = "https://inpost.pl/sledzenie-przesylek?number={tracking_number}"

    COURIER_SERVICES: ClassVar[list[str]] = [
        "inpost_courier_standard",
        "inpost_courier_express_1000",
        "inpost_courier_express_1200",
        "inpost_courier_express_1700",
        "inpost_courier_palette",
        "inpost_courier_alcohol",
    ]

    def __init__(self) -> None:
        self._client = httpx.AsyncClient(timeout=settings.rest_timeout)
        logger.info("InPost integration initialised")

    def _api_url(self, credentials: InpostCredentials) -> str:
        if credentials.sandbox_mode:
            return settings.inpost_sandbox_api_url
        return settings.inpost_prod_api_url

    # ------------------------------------------------------------------
    # Order status
    # ------------------------------------------------------------------

    async def get_order_status(
        self,
        credentials: InpostCredentials,
        waybill_number: str,
    ) -> tuple[str, int]:
        """Retrieve the latest shipment status.

        Tries the public tracking endpoint first; falls back to
        ``get_order`` on sandbox where tracking may not be available.
        """
        if not waybill_number:
            return "Należy podać numer listu przewozowego", HTTPStatus.BAD_REQUEST

        response = await self._client.get(
            f"{self._api_url(credentials)}v1/tracking/{waybill_number}",
        )

        if response.status_code == HTTPStatus.OK:
            order_tracking_json = response.json()
            status_history = order_tracking_json.get("tracking_details", [])
            if status_history:
                status_history = sorted(
                    status_history,
                    key=lambda x: datetime.fromisoformat(x["datetime"]),
                    reverse=True,
                )
                return status_history[0].get("status", ""), HTTPStatus.OK
        elif response.status_code == HTTPStatus.NOT_FOUND:
            order, get_order_status_code = await self.get_order(credentials, waybill_number)
            if get_order_status_code == HTTPStatus.OK:
                return order["status"], HTTPStatus.OK
            return (
                f"Nie znaleziono zamówienia o podanym numerze listu przewozowego {waybill_number}",
                HTTPStatus.NOT_FOUND,
            )

        return self._format_rest_error_response(response)

    # ------------------------------------------------------------------
    # Tracking info
    # ------------------------------------------------------------------

    async def get_tracking_info(
        self,
        waybill_number: str,
    ) -> tuple[Tracking, int]:
        """Return tracking URL — no API call required."""
        resp = Tracking(
            tracking_number=waybill_number,
            tracking_url=self.TRACKING_URL.format(tracking_number=waybill_number),
        )
        return resp, HTTPStatus.OK

    # ------------------------------------------------------------------
    # Create shipment
    # ------------------------------------------------------------------

    async def create_order(
        self,
        credentials: InpostCredentials,
        command: CreateShipmentRequest,
    ) -> tuple[object, int]:
        """Create an InPost shipment in simplified mode.

        After creation, retries to obtain the waybill number since
        InPost may not return it immediately.
        """
        inpost_create_command = self._get_create_order_command(command)
        response = await self._client.post(
            f"{self._api_url(credentials)}v1/organizations/{credentials.organization_id}/shipments",
            headers=self._get_headers(credentials.api_token),
            json=inpost_create_command,
        )

        if response.status_code != HTTPStatus.CREATED:
            return self._format_rest_error_response(response)

        order = response.json()
        logger.debug(
            "InPost shipment first stage passed — shipment id=%s",
            order["id"],
        )

        waybill_number, waybill_status_code = await self._get_waybill_number_with_retry(
            credentials,
            order["id"],
        )
        if waybill_status_code == HTTPStatus.NOT_ACCEPTABLE:
            return waybill_number, HTTPStatus.NOT_ACCEPTABLE

        tracking = GET_TRACKING_SCHEMA.copy()
        if waybill_status_code == HTTPStatus.OK and waybill_number:
            tracking["tracking_number"] = waybill_number
            tracking["tracking_url"] = self.TRACKING_URL.format(tracking_number=waybill_number)
        order["tracking"] = tracking
        normalized = self._normalize_order_item(command, order)
        return normalized, response.status_code

    # ------------------------------------------------------------------
    # Delete shipment
    # ------------------------------------------------------------------

    async def delete_order(
        self,
        credentials: InpostCredentials,
        waybill_number: str,
    ) -> tuple[str | None, int]:
        """Cancel / delete an InPost shipment.

        InPost API does not support deleting already-paid shipments.
        """
        found_orders, get_order_status = await self.get_order(credentials, waybill_number)
        if get_order_status != HTTPStatus.OK:
            return found_orders, get_order_status

        order_id = found_orders["id"]
        response = await self._client.delete(
            f"{self._api_url(credentials)}v1/shipments/{order_id}",
            headers=self._get_headers(credentials.api_token),
        )

        match response.status_code:
            case HTTPStatus.NO_CONTENT:
                return None, response.status_code
            case HTTPStatus.BAD_REQUEST if response.json().get("error") == "invalid_action":
                return "Nie można anulowac oplaconej paczki", HTTPStatus.BAD_REQUEST
            case _:
                return self._format_rest_error_response(response)

    # ------------------------------------------------------------------
    # Labels
    # ------------------------------------------------------------------

    async def get_waybill_label_bytes(
        self,
        credentials: InpostCredentials,
        waybill_numbers: list[str],
    ) -> tuple[bytes | str, int]:
        """Retrieve label PDF bytes for the given waybill numbers.

        InPost labels are fetched by shipment IDs, so we first resolve
        each waybill number to its shipment ID.
        """
        order_ids: list[str] = []
        for waybill_number in waybill_numbers:
            order_id, get_order_id_status = await self.get_order_id(credentials, waybill_number)
            if get_order_id_status == HTTPStatus.OK:
                order_ids.append(order_id)
            else:
                return order_id, get_order_id_status

        response = await self._client.get(
            f"{self._api_url(credentials)}v1/organizations/{credentials.organization_id}/shipments/labels",
            params={
                "shipment_ids[]": [int(oid) for oid in order_ids],
                "type": "A6",
            },
            headers=self._get_headers(credentials.api_token),
        )

        if response.status_code != HTTPStatus.OK:
            return self._format_rest_error_response(response)

        return response.content, response.status_code

    # ------------------------------------------------------------------
    # Get order
    # ------------------------------------------------------------------

    async def get_order(
        self,
        credentials: InpostCredentials,
        waybill_number: str,
    ) -> tuple[dict | str, int]:
        """Retrieve a shipment by tracking number."""
        if not waybill_number:
            return "Należy podać numer listu przewozowego", HTTPStatus.BAD_REQUEST

        response = await self._client.get(
            f"{self._api_url(credentials)}v1/organizations/{credentials.organization_id}/shipments",
            headers=self._get_headers(credentials.api_token),
            params={"tracking_number": waybill_number},
        )

        if response.status_code != HTTPStatus.OK:
            return self._format_rest_error_response(response)

        resp_json = response.json()
        if "count" not in resp_json:
            return resp_json, response.status_code

        if resp_json["count"] == 0:
            return (
                f"Nie znaleziono zamówienia o podanym numerze listu przewozowego {waybill_number}",
                HTTPStatus.NOT_FOUND,
            )

        tracking = GET_TRACKING_SCHEMA.copy()
        tracking["tracking_number"] = waybill_number
        tracking["tracking_url"] = self.TRACKING_URL.format(tracking_number=waybill_number)
        order = resp_json["items"][0]
        order["tracking"] = tracking
        return order, response.status_code

    # ------------------------------------------------------------------
    # Points (lockers / service points)
    # ------------------------------------------------------------------

    async def get_points(
        self,
        credentials: InpostCredentials,
        data: dict,
    ) -> tuple[dict, int]:
        """Look up InPost service points (lockers, PaczkoPunkty, etc.)."""
        search_query = get_extras(data, "inpost")
        if "city" in data:
            search_query["city"] = data["city"]
        if "postcode" in data:
            search_query["post_code"] = data["postcode"]

        response = await self._client.get(
            f"{self._api_url(credentials)}v1/points",
            headers=self._get_headers(credentials.api_token),
            params=search_query,
        )

        if response.status_code != HTTPStatus.OK:
            return self._format_rest_error_response(response)

        points: dict = {}
        for inpost_point in response.json().get("items", []):
            point = _deep_copy_schema(GET_POINT_SCHEMA)
            point["type"] = inpost_point["type"][0]
            point["name"] = inpost_point["name"]
            point["address"]["line1"] = inpost_point["address"]["line1"]
            point["address"]["line2"] = inpost_point["address"]["line2"]
            point["address"]["postal_code"] = inpost_point["address_details"]["post_code"]
            point["address"]["country_code"] = "PL"
            point["address"]["city"] = inpost_point["address_details"]["city"]
            point["address"]["longitude"] = inpost_point["location"]["longitude"]
            point["address"]["latitude"] = inpost_point["location"]["latitude"]
            point["image_url"] = inpost_point["image_url"]
            point["open_hours"] = inpost_point["opening_hours"]
            point["distance"] = inpost_point["distance"] if inpost_point["distance"] else 0
            point["option_send"] = "parcel_send" in inpost_point["functions"]

            points[point["name"]] = point

        return points, HTTPStatus.OK

    # ------------------------------------------------------------------
    # Waybill number helpers
    # ------------------------------------------------------------------

    async def get_waybill_number(
        self,
        credentials: InpostCredentials,
        order_id: str,
    ) -> tuple[str, int]:
        """Retrieve waybill number by shipment ID.

        InPost sometimes returns an empty waybill number right after
        creation — callers should retry.
        """
        response = await self._client.get(
            f"{self._api_url(credentials)}v1/organizations/{credentials.organization_id}/shipments",
            headers=self._get_headers(credentials.api_token),
            params={"id": order_id},
        )
        if response.status_code == HTTPStatus.OK:
            waybill_number = response.json().get("items", [{}])[0].get("tracking_number")

            if waybill_number is None:
                shipment = response.json().get("items", [None])[0]
                if shipment and (
                    shipment.get("selected_offer") is None
                    and shipment.get("offers")
                    and len(shipment.get("offers")) > 0
                ):
                    offer = shipment["offers"][0]
                    if offer.get("status") == "unavailable" and offer.get("unavailability_reasons"):
                        error_unavailable = "Błąd podczas zamawiania w Inpost:"
                        for reason in offer["unavailability_reasons"]:
                            error_unavailable += " " + str(reason)
                        return error_unavailable, HTTPStatus.NOT_ACCEPTABLE

            if waybill_number is not None:
                return waybill_number, response.status_code

            return (
                "Podana przesyłka nie posiada numeru listu przewozowego",
                HTTPStatus.NOT_FOUND,
            )

        return self._format_rest_error_response(response)

    async def get_order_id(
        self,
        credentials: InpostCredentials,
        waybill_number: str,
    ) -> tuple[str, int]:
        """Resolve a waybill number to the InPost internal shipment ID."""
        get_order_response, get_order_status = await self.get_order(credentials, waybill_number)
        if get_order_status == HTTPStatus.OK:
            return get_order_response["id"], get_order_status
        return get_order_response, get_order_status

    # ------------------------------------------------------------------
    # Private — waybill retry loop
    # ------------------------------------------------------------------

    async def _get_waybill_number_with_retry(
        self,
        credentials: InpostCredentials,
        order_id: str,
    ) -> tuple[object, int]:
        """Retry waybill retrieval because InPost may not assign it immediately."""
        waybill_number: object = None
        status_code = HTTPStatus.BAD_REQUEST
        for _ in range(settings.inpost_waybill_retry_count):
            waybill_number, status_code = await self.get_waybill_number(credentials, order_id)
            if status_code == HTTPStatus.NOT_ACCEPTABLE:
                break
            if self._is_valid_waybill_number(waybill_number, status_code):
                break
            await asyncio.sleep(settings.inpost_waybill_retry_wait)
        return waybill_number, status_code

    # ------------------------------------------------------------------
    # Private — additional courier services
    # ------------------------------------------------------------------

    def _get_additional_services(self, inpost_extras: dict, service_name: str) -> list[str]:
        """Build the ``additional_services`` list for courier-type shipments."""
        if service_name not in self.COURIER_SERVICES:
            return []
        service_mappings = {
            "delivery_saturday": "saturday",
            "delivery9": "forhour_9",
            "delivery12": "forhour_12",
            "delivery_sms": "sms",
            "delivery_email": "email",
            "rod": "rod",
        }
        return [service for key, service in service_mappings.items() if inpost_extras.get(key, False)]

    # ------------------------------------------------------------------
    # Private — build create-order payload
    # ------------------------------------------------------------------

    def _get_create_order_command(self, command: CreateShipmentRequest) -> dict:
        """Assemble the JSON payload for the InPost simplified shipment creation."""
        inpost_extras: dict = command.extras.get("inpost", {})
        receiver = command.receiver
        shipper = command.shipper
        additional_services = self._get_additional_services(inpost_extras, command.service_name)

        end_of_week_collection = False
        if "locker" in command.service_name and inpost_extras.get("delivery_saturday"):
            end_of_week_collection = True

        insurance_amount = 0
        if inpost_extras.get("insurance") is True:
            insurance_amount = inpost_extras.get("insurance_value", 0)

        if command.cod:
            insurance_amount = command.cod_value

        service = command.service_name
        if inpost_extras.get("delivery9") is True:
            service = "inpost_courier_express_1000"
        elif inpost_extras.get("delivery12") is True:
            service = "inpost_courier_express_1200"

        return {
            "service": service,
            "custom_attributes": inpost_extras.get("custom_attributes", {}),
            "parcels": [
                {
                    "dimensions": {
                        "height": parcel.height * 10.0,
                        "length": parcel.length * 10.0,
                        "unit": "mm",
                        "width": parcel.width * 10.0,
                    },
                    "id": id_,
                    "weight": {
                        "amount": parcel.weight,
                        "unit": "kg",
                    },
                }
                for id_, parcel in enumerate(command.parcels, start=1)
            ],
            "receiver": {
                "address": {
                    "building_number": receiver.building_number,
                    "city": receiver.city,
                    "country_code": receiver.country_code,
                    "post_code": receiver.postal_code,
                    "street": receiver.street,
                },
                "email": receiver.email,
                "company_name": receiver.company_name,
                "first_name": receiver.first_name,
                "last_name": receiver.last_name,
                "name": f"{receiver.first_name} {receiver.last_name}",
                "phone": self._format_phone(receiver.phone),
            },
            "sender": {
                "address": {
                    "building_number": shipper.building_number,
                    "city": shipper.city,
                    "country_code": shipper.country_code,
                    "post_code": shipper.postal_code,
                    "street": shipper.street,
                },
                "email": shipper.email,
                "company_name": shipper.company_name,
                "first_name": shipper.first_name,
                "last_name": shipper.last_name,
                "name": f"{shipper.first_name} {shipper.last_name}",
                "phone": self._format_phone(shipper.phone),
            },
            "reference": command.content,
            "end_of_week_collection": end_of_week_collection,
            "cod": {
                "amount": command.cod_value,
                "currency": settings.default_currency,
            }
            if command.cod
            else None,
            "insurance": {
                "amount": insurance_amount,
                "currency": settings.default_currency,
            }
            if command.cod or inpost_extras.get("insurance") is True
            else None,
            "additional_services": additional_services,
            "is_return": inpost_extras.get("return_pack", False),
        }

    # ------------------------------------------------------------------
    # Private — normalisation helpers
    # ------------------------------------------------------------------

    def _normalize_order_item(
        self,
        command: CreateShipmentRequest,
        order: dict,
    ) -> dict:
        """Build a normalised response dict from a raw InPost order."""
        tracking = order["tracking"]
        return {
            "id": order["id"],
            "waybill_number": tracking.get("tracking_number"),
            "shipper": self._normalize_shipment_party_from_schema(command.shipper),
            "receiver": self._normalize_shipment_party_from_schema(command.receiver),
            "orderStatus": order.get("status", ""),
            "created_at": order.get("created_at", ""),
            "tracking": tracking,
        }

    @staticmethod
    def _normalize_shipment_party_from_schema(party: ShipmentParty) -> dict:
        """Convert a command-side ShipmentParty to a response-side structure."""
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

    # ------------------------------------------------------------------
    # Private — headers & formatting
    # ------------------------------------------------------------------

    @staticmethod
    def _get_headers(api_token: str) -> dict:
        """Return authorization headers for InPost REST API."""
        return {
            "Authorization": f"Bearer {api_token}",
        }

    @staticmethod
    def _format_phone(phone: str | None) -> str:
        """Normalise phone to last 9 digits (Polish mobile format)."""
        if phone:
            return phone.strip().replace(" ", "")[-9:]
        return ""

    @staticmethod
    def _is_valid_waybill_number(waybill_number: object, status_code: int) -> bool:
        return status_code == HTTPStatus.OK and bool(waybill_number)

    @staticmethod
    def _format_rest_error_response(response: httpx.Response) -> tuple[str, int]:
        """Format an error response from the InPost REST API."""
        try:
            resp_json = response.json()
            msg = resp_json.get("message", "")
            if "Check details object for more info" in msg:
                msg = msg + " " + str(resp_json.get("details", ""))
            if not msg:
                msg = str(resp_json)
        except Exception:
            msg = response.text
        logger.error(
            "InPost API error — url=%s status=%s",
            response.url.path,
            response.status_code,
        )
        return msg, response.status_code
