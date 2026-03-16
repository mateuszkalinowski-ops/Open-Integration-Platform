"""Paxy Courier Integration — migrated from meriship codebase.

Handles all Paxy REST API interactions including:
- Registry book creation
- Parcel/shipment creation
- Label retrieval via /labels/print
- Shipment status tracking via /trackings
- Shipment deletion via DELETE /parcels/{waybill}
"""

from __future__ import annotations

import logging
import urllib.parse
from http import HTTPStatus

import httpx

from src.config import settings
from src.schemas import CreateOrderCommand, PaxyCredentials

logger = logging.getLogger("courier-paxy")

STATUS_MAP: dict[str, str] = {
    "NEW": "NEW",
    "COLLECTED": "IN_TRANSIT",
    "IN_TRANSIT": "IN_TRANSIT",
    "OUT_FOR_DELIVERY": "OUT_FOR_DELIVERY",
    "DELIVERED": "DELIVERED",
    "RETURNED": "RETURNED",
    "CANCELLED": "CANCELLED",
}


class PaxyIntegration:
    """Paxy REST integration for parcel shipments."""

    def __init__(self) -> None:
        self.base_url = settings.paxy_api_url
        self.timeout = settings.rest_timeout
        logger.info("Paxy REST integration initialized — %s", self.base_url)

    @staticmethod
    def _get_headers(api_key: str, api_token: str) -> dict[str, str]:
        return {
            "CL-API-KEY": api_key,
            "CL-API-TOKEN": api_token,
            "Content-Type": "application/json",
        }

    @staticmethod
    def _normalize_shipment_party(party) -> dict:
        street = getattr(party, "street", "") or ""
        building = getattr(party, "building_number", "") or ""
        postal = getattr(party, "postal_code", "") or ""
        city = getattr(party, "city", "") or ""
        country = getattr(party, "country_code", "PL") or "PL"
        return {
            "first_name": getattr(party, "first_name", "") or "",
            "last_name": getattr(party, "last_name", "") or "",
            "contact_person": getattr(party, "contact_person", "") or "",
            "phone": getattr(party, "phone", "") or "",
            "email": getattr(party, "email", "") or "",
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
    def map_status(status: str) -> str:
        return STATUS_MAP.get(status, status)

    # ------------------------------------------------------------------
    # Order status
    # ------------------------------------------------------------------

    async def get_order_status(
        self,
        credentials: PaxyCredentials,
        waybill_number: str,
    ) -> tuple[str, int]:
        """Get order status via POST /trackings."""
        headers = self._get_headers(credentials.api_key, credentials.api_token)
        payload = {"trackingNrs": [waybill_number]}

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/trackings",
                headers=headers,
                json=payload,
            )

        if response.status_code == HTTPStatus.OK:
            status_response = response.json()
            items = status_response.get("items", [])
            if len(items) > 0:
                item = items[0]
                current_status = item.get("statusCode", "UNKNOWN")
                return self.map_status(current_status), HTTPStatus.OK
            return "UNKNOWN", response.status_code

        return self._format_rest_error_response(response)

    # ------------------------------------------------------------------
    # Create order
    # ------------------------------------------------------------------

    async def create_order(
        self,
        credentials: PaxyCredentials,
        command: CreateOrderCommand,
    ) -> tuple[object, int]:
        """Create order — first creates registry book, then the parcel."""
        headers = self._get_headers(credentials.api_key, credentials.api_token)
        create_command = await self._get_create_order_command(command, credentials)

        async with httpx.AsyncClient(timeout=45) as client:
            response = await client.post(
                f"{self.base_url}/parcels",
                headers=headers,
                json=create_command,
            )

        if response.status_code == HTTPStatus.OK:
            order = response.json()
            logger.info("Paxy shipment created: %s", order.get("trackingNr", ""))
            normalized = self._normalize_order_item(order, command)
            normalized["service_name"] = command.service_name
            return normalized, response.status_code

        return self._format_rest_error_response(response)

    # ------------------------------------------------------------------
    # Labels
    # ------------------------------------------------------------------

    async def get_waybill_label_bytes(
        self,
        credentials: PaxyCredentials,
        waybill_numbers: list[str],
        _data: dict | None = None,
    ) -> tuple[bytes | str, int]:
        """Retrieve waybill label via POST /labels/print."""
        headers = self._get_headers(credentials.api_key, credentials.api_token)

        for waybill_number in waybill_numbers:
            payload = {
                "trackingNrs": [waybill_number],
                "bookNr": "",
            }

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/labels/print",
                    headers=headers,
                    json=payload,
                )

            if response.status_code == HTTPStatus.OK:
                return response.content, response.status_code

            return self._format_error_response(response)

        return "No waybill numbers provided", HTTPStatus.BAD_REQUEST

    # ------------------------------------------------------------------
    # Delete order
    # ------------------------------------------------------------------

    async def delete_order(
        self,
        credentials: PaxyCredentials,
        waybill_number: str,
        _data: dict | None = None,
    ) -> tuple[str, int]:
        """Delete order via DELETE /parcels/{waybill}."""
        headers = self._get_headers(credentials.api_key, credentials.api_token)
        payload = {"reason": "wrong data"}

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.request(
                "DELETE",
                f"{self.base_url}/parcels/{urllib.parse.quote(waybill_number, safe='')}",
                headers=headers,
                json=payload,
            )

        response_formatted = response.json()
        if response.status_code == HTTPStatus.OK:
            logger.info("Paxy shipment deleted: %s", waybill_number)
            return {"message": "Shipment deleted successfully"}, HTTPStatus.OK

        logger.error("Paxy delete error for %s: %s", waybill_number, str(response_formatted.get("message", ""))[:200])
        return {"error": "Paxy API request failed"}, HTTPStatus.BAD_REQUEST

    # ------------------------------------------------------------------
    # Private — build create order command
    # ------------------------------------------------------------------

    async def _get_create_order_command(
        self,
        command: CreateOrderCommand,
        credentials: PaxyCredentials,
    ) -> dict:
        """Build the Paxy parcel creation payload.

        Creates registry book first, then assembles the parcel command using the
        book number, carrier codes from service_name split, and optional COD/insurance.
        """
        paxy_extras: dict = command.extras.get("paxy", {})
        office_id = ""

        weights: list[float] = []
        weight: float = 0

        for parcel in command.parcels:
            if parcel.weight and parcel.weight > 0:
                weights.append(parcel.weight)
                weight += parcel.weight

        carrier_code = ""
        carrier_type = ""
        services = command.service_name.split("-")
        if len(services) > 1:
            carrier_code = services[0]
            carrier_type = services[1]

        name_parts = []
        if command.receiver.first_name:
            name_parts.append(command.receiver.first_name)
        if command.receiver.last_name:
            name_parts.append(command.receiver.last_name)
        recipient_name = " ".join(name_parts)

        insurance: float = 0
        if paxy_extras.get("insurance") and paxy_extras.get("insurance_value", 0) > 0:
            insurance = paxy_extras["insurance_value"]

        cod: float = 0
        if command.cod and command.cod_value > 0:
            cod = command.cod_value

        # Create registry book before parcel
        book_number = await self._create_registry_book(command, credentials)

        point_id = ""
        custom_attrs = paxy_extras.get("custom_attributes", {})
        if custom_attrs and custom_attrs.get("target_point"):
            point_id = custom_attrs["target_point"]
            if "office" in command.service_name:
                office_id = custom_attrs["target_point"]

        return {
            "bookNr": book_number,
            "carrierCode": carrier_code,
            "type": carrier_type,
            "quantity": str(len(command.parcels)),
            "recipientName": recipient_name,
            "recipientCity": command.receiver.city,
            "recipientRegion": "",
            "recipientPostCode": command.receiver.postal_code.replace("-", ""),
            "recipientStreet": command.receiver.street,
            "recipientAddressNr": command.receiver.building_number,
            "recipientEmail": command.receiver.email,
            "recipientTel": command.receiver.phone,
            "weight": str(weight),
            "weights": weights,
            "cod": str(cod),
            "insurance": str(insurance),
            "reference": command.content,
            "docWz": "",
            "pointId": point_id,
            "officeId": office_id,
            "externalNr": "",
        }

    async def _create_registry_book(
        self,
        command: CreateOrderCommand,
        credentials: PaxyCredentials,
    ) -> str:
        """Create a registry book via POST /books and return the book number."""
        headers = self._get_headers(credentials.api_key, credentials.api_token)
        registry_book_command = {
            "countryCode": command.receiver.country_code,
            "comments": "",
            "postingDate": command.shipment_date,
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/books",
                headers=headers,
                json=registry_book_command,
            )

        book_number = ""

        if response.status_code == HTTPStatus.OK:
            book_registry = response.json()
            book = book_registry.get("book", {})
            if book and book.get("nr"):
                book_number = book["nr"]

        if response.status_code == HTTPStatus.BAD_REQUEST:
            book_registry = response.json()
            if book_registry.get("nr"):
                book_number = book_registry["nr"]

        return book_number

    # ------------------------------------------------------------------
    # Private — normalisation
    # ------------------------------------------------------------------

    def _normalize_order_item(
        self,
        parcel: dict,
        command: CreateOrderCommand,
    ) -> dict:
        return {
            "id": "",
            "waybill_number": parcel["trackingNr"],
            "shipper": self._normalize_shipment_party(command.shipper),
            "receiver": self._normalize_shipment_party(command.receiver),
            "orderStatus": "CREATED",
            "tracking": {
                "tracking_number": parcel["trackingNr"],
                "tracking_url": None,
            },
        }

    # ------------------------------------------------------------------
    # Private — error formatting
    # ------------------------------------------------------------------

    @staticmethod
    def _format_error_response(response: httpx.Response) -> tuple[str, int]:
        status = response.status_code
        try:
            body = response.json()
            message = body.get("message", "")
        except (ValueError, UnicodeDecodeError):
            message = ""
        logger.error("Paxy REST error %s [%s]: %s", response.url.path, status, message or response.text[:200])
        safe_messages = {
            400: "Bad request",
            401: "Authentication failed",
            403: "Access denied",
            404: "Resource not found",
            429: "Rate limited",
        }
        return safe_messages.get(status, f"Paxy API error (HTTP {status})"), HTTPStatus.BAD_REQUEST

    @staticmethod
    def _format_rest_error_response(response: httpx.Response) -> tuple[str, int]:
        status = response.status_code
        try:
            body = response.json()
            message = body.get("message", "")
        except (ValueError, UnicodeDecodeError):
            message = ""
        logger.error("Paxy REST error %s [%s]: %s", response.url.path, status, message or response.text[:200])
        safe_messages = {
            400: "Bad request",
            401: "Authentication failed",
            403: "Access denied",
            404: "Resource not found",
            429: "Rate limited",
        }
        return safe_messages.get(status, f"Paxy API error (HTTP {status})"), HTTPStatus.BAD_REQUEST
