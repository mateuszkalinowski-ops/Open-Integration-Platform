"""DHL Express REST API integration client.

Handles all DHL Express MyDHL API interactions via REST:
- Shipment creation with labels
- Tracking
- Rating
- Pickup management
- Address validation
- Service points
"""

from __future__ import annotations

import base64
import logging
from http import HTTPStatus
from typing import Any

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from src.config import settings

logger = logging.getLogger("courier-dhl-express")

RETRIABLE_STATUS_CODES = {502, 503, 504, 429}


class DhlExpressError(Exception):
    """Raised when the DHL Express API returns an error."""

    def __init__(self, status_code: int, detail: Any) -> None:
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"DHL Express API error {status_code}: {detail}")


class DhlExpressIntegration:
    """DHL Express REST client.

    Uses multiple DHL API endpoints:
    - MyDHL Express API (shipments, rates, pickups) — Basic Auth
    - DHL Unified Tracking API — DHL-API-Key header
    - DHL Unified Location Finder API — DHL-API-Key header
    """

    TRACKING_URL = (
        "https://www.dhl.com/pl-en/home/tracking/tracking-parcel.html"
        "?submit=1&tracking-id={tracking_number}"
    )

    def __init__(self) -> None:
        self._base_url = settings.api_base_url.rstrip("/")
        self._api_key = settings.dhl_express_api_key
        self._api_secret = settings.dhl_express_api_secret

        self._auth_header = self._build_auth_header(
            self._api_key, self._api_secret,
        )

        # MyDHL Express API client (Basic Auth — for shipments, rates, pickups)
        self._express_client = httpx.AsyncClient(
            base_url=self._base_url,
            headers={
                "Authorization": self._auth_header,
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            timeout=httpx.Timeout(settings.http_timeout, connect=10.0),
        )

        # DHL Unified APIs client (DHL-API-Key header — for tracking, locations)
        self._unified_client = httpx.AsyncClient(
            headers={
                "DHL-API-Key": self._api_key,
                "Accept": "application/json",
            },
            timeout=httpx.Timeout(settings.http_timeout, connect=10.0),
        )

        logger.info(
            "DHL Express client initialised — express=%s, tracking=%s, locations=%s",
            self._base_url,
            settings.dhl_tracking_url,
            settings.dhl_location_finder_url,
        )

    async def close(self) -> None:
        await self._express_client.aclose()
        await self._unified_client.aclose()

    @property
    def is_configured(self) -> bool:
        return bool(self._api_key)

    # ------------------------------------------------------------------
    # Shipment creation
    # ------------------------------------------------------------------

    async def create_shipment(self, payload: dict) -> tuple[dict, int]:
        """Create a DHL Express shipment.

        POST /shipments
        Returns shipment details including tracking number and label images.
        """
        response = await self._request("POST", "/shipments", json=payload)
        return response, HTTPStatus.CREATED

    # ------------------------------------------------------------------
    # Tracking
    # ------------------------------------------------------------------

    async def get_tracking(
        self,
        tracking_number: str,
        *,
        tracking_view: str = "all-checkpoints",
        level_of_detail: str = "all",
    ) -> tuple[dict, int]:
        """Retrieve tracking information via DHL Unified Tracking API.

        GET https://api-eu.dhl.com/track/shipments?trackingNumber={number}
        """
        params: dict[str, str] = {"trackingNumber": tracking_number}
        if tracking_view:
            params["trackingView"] = tracking_view
        if level_of_detail:
            params["levelOfDetail"] = level_of_detail

        response = await self._unified_request(
            "GET", settings.dhl_tracking_url, params=params,
        )
        tracking_url = self.TRACKING_URL.format(tracking_number=tracking_number)
        response["_trackingUrl"] = tracking_url
        return response, HTTPStatus.OK

    # ------------------------------------------------------------------
    # Rating
    # ------------------------------------------------------------------

    async def get_rates(self, payload: dict) -> tuple[dict, int]:
        """Retrieve DHL Express rates and products.

        POST /rates
        Returns available products, delivery times, and pricing.
        """
        response = await self._request("POST", "/rates", json=payload)
        return response, HTTPStatus.OK

    async def get_products(
        self,
        *,
        shipper_country_code: str,
        shipper_postal_code: str,
        receiver_country_code: str,
        receiver_postal_code: str,
        weight: float,
        length: float = 1,
        width: float = 1,
        height: float = 1,
        planned_shipping_date: str,
        is_customs_declarable: bool = False,
        unit_of_measurement: str = "metric",
    ) -> tuple[dict, int]:
        """Retrieve available DHL Express products (lightweight rating).

        GET /products
        """
        params = {
            "originCountryCode": shipper_country_code,
            "originPostalCode": shipper_postal_code,
            "receiverCountryCode": receiver_country_code,
            "receiverPostalCode": receiver_postal_code,
            "weight": weight,
            "length": length,
            "width": width,
            "height": height,
            "plannedShippingDate": planned_shipping_date,
            "isCustomsDeclarable": str(is_customs_declarable).lower(),
            "unitOfMeasurement": unit_of_measurement,
        }
        response = await self._request("GET", "/products", params=params)
        return response, HTTPStatus.OK

    # ------------------------------------------------------------------
    # Labels / document images
    # ------------------------------------------------------------------

    async def get_shipment_image(
        self,
        tracking_number: str,
        *,
        type_code: str = "label",
    ) -> tuple[bytes | dict, int]:
        """Retrieve shipment document images (label, invoice, waybill).

        GET /shipments/{trackingNumber}/get-image
        """
        params = {"typeCode": type_code}
        response = await self._request(
            "GET",
            f"/shipments/{tracking_number}/get-image",
            params=params,
        )
        if isinstance(response, dict) and "documents" in response:
            for doc in response["documents"]:
                if "content" in doc:
                    doc["_decoded_content"] = base64.b64decode(doc["content"])
            return response, HTTPStatus.OK
        return response, HTTPStatus.OK

    async def get_label_bytes(self, tracking_number: str) -> tuple[bytes, int]:
        """Convenience method returning raw PDF label bytes."""
        response, status_code = await self.get_shipment_image(
            tracking_number, type_code="label",
        )
        if isinstance(response, dict) and "documents" in response:
            for doc in response["documents"]:
                if "_decoded_content" in doc:
                    return doc["_decoded_content"], HTTPStatus.OK
        return b"", HTTPStatus.NOT_FOUND

    # ------------------------------------------------------------------
    # Pickup management
    # ------------------------------------------------------------------

    async def create_pickup(self, payload: dict) -> tuple[dict, int]:
        """Request a DHL Express pickup.

        POST /pickups
        """
        response = await self._request("POST", "/pickups", json=payload)
        return response, HTTPStatus.CREATED

    async def update_pickup(
        self,
        dispatch_confirmation_number: str,
        payload: dict,
    ) -> tuple[dict, int]:
        """Update an existing pickup request.

        PATCH /pickups/{dispatchConfirmationNumber}
        """
        response = await self._request(
            "PATCH",
            f"/pickups/{dispatch_confirmation_number}",
            json=payload,
        )
        return response, HTTPStatus.OK

    async def cancel_pickup(
        self,
        dispatch_confirmation_number: str,
        *,
        requestor_name: str = "",
        reason: str = "not needed",
    ) -> tuple[dict, int]:
        """Cancel a pickup request.

        DELETE /pickups/{dispatchConfirmationNumber}
        """
        params: dict[str, str] = {"reason": reason}
        if requestor_name:
            params["requestorName"] = requestor_name
        response = await self._request(
            "DELETE",
            f"/pickups/{dispatch_confirmation_number}",
            params=params,
        )
        return response, HTTPStatus.OK

    # ------------------------------------------------------------------
    # Address validation
    # ------------------------------------------------------------------

    async def validate_address(
        self,
        *,
        country_code: str,
        postal_code: str = "",
        city: str = "",
        address_type: str = "delivery",
    ) -> tuple[dict, int]:
        """Validate if DHL Express can pick up / deliver at an address.

        GET /address-validate
        """
        params: dict[str, str] = {
            "countryCode": country_code,
            "type": address_type,
        }
        if postal_code:
            params["postalCode"] = postal_code
        if city:
            params["cityName"] = city
        response = await self._request("GET", "/address-validate", params=params)
        return response, HTTPStatus.OK

    # ------------------------------------------------------------------
    # Service points
    # ------------------------------------------------------------------

    async def get_service_points(
        self,
        *,
        country_code: str,
        postal_code: str = "",
        city: str = "",
        latitude: float | None = None,
        longitude: float | None = None,
        radius: int = 5000,
        max_results: int = 25,
    ) -> tuple[dict, int]:
        """Find DHL service points via Unified Location Finder API.

        GET https://api.dhl.com/location-finder/v1/find-by-address
        or  https://api.dhl.com/location-finder/v1/find-by-geo
        """
        base = settings.dhl_location_finder_url.rstrip("/")

        if latitude is not None and longitude is not None:
            url = f"{base}/find-by-geo"
            params: dict[str, Any] = {
                "latitude": latitude,
                "longitude": longitude,
                "radius": radius,
                "limit": max_results,
                "countryCode": country_code,
            }
        else:
            url = f"{base}/find-by-address"
            params = {
                "countryCode": country_code,
                "radius": radius,
                "limit": max_results,
            }
            if postal_code:
                params["postalCode"] = postal_code
            if city:
                params["addressLocality"] = city

        response = await self._unified_request("GET", url, params=params)
        return response, HTTPStatus.OK

    # ------------------------------------------------------------------
    # Landed cost
    # ------------------------------------------------------------------

    async def get_landed_cost(self, payload: dict) -> tuple[dict, int]:
        """Estimate landed cost (duties + taxes).

        POST /landed-cost
        """
        response = await self._request("POST", "/landed-cost", json=payload)
        return response, HTTPStatus.OK

    # ------------------------------------------------------------------
    # Private — HTTP client helpers
    # ------------------------------------------------------------------

    @retry(
        retry=retry_if_exception_type(httpx.TransportError),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    async def _request(
        self,
        method: str,
        path: str,
        *,
        json: dict | None = None,
        params: dict | None = None,
    ) -> dict | Any:
        """Execute HTTP request against MyDHL Express API (Basic Auth)."""
        logger.debug("DHL Express API %s %s params=%s", method, path, params)
        response = await self._express_client.request(
            method, path, json=json, params=params,
        )
        return self._handle_response(response)

    @retry(
        retry=retry_if_exception_type(httpx.TransportError),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    async def _unified_request(
        self,
        method: str,
        url: str,
        *,
        params: dict | None = None,
    ) -> dict | Any:
        """Execute HTTP request against DHL Unified APIs (DHL-API-Key header)."""
        logger.debug("DHL Unified API %s %s params=%s", method, url, params)
        response = await self._unified_client.request(
            method, url, params=params,
        )
        return self._handle_response(response)

    @staticmethod
    def _handle_response(response: httpx.Response) -> dict | Any:
        if response.status_code in RETRIABLE_STATUS_CODES:
            raise httpx.TransportError(
                f"Retriable status {response.status_code}",
            )

        if response.status_code >= 400:
            try:
                detail = response.json()
            except Exception:
                detail = response.text
            raise DhlExpressError(response.status_code, detail)

        if not response.content:
            return {}

        try:
            return response.json()
        except Exception:
            return {"raw": response.text}

    @staticmethod
    def _build_auth_header(api_key: str, api_secret: str) -> str:
        if not api_key or not api_secret:
            return ""
        credentials = f"{api_key}:{api_secret}"
        encoded = base64.b64encode(credentials.encode()).decode()
        return f"Basic {encoded}"
