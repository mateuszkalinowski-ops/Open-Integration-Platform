"""InPost International 2025 — modular API classes.

Ported from meriship version_international_2025/api/ directory.
All calls converted from requests (sync) to httpx (async).

Key differences from 2024 API:
- OAuth2 endpoint: /oauth2/token
- Versioned routes: /shipping/v2, /tracking/v1, /pickups/v1, /location/v1, /returns/v1
- Tracking API does not require auth header
- Shipping returns trackingNumber directly
- Returns API for return shipments
- Location API replaces Points API
"""

from __future__ import annotations

import functools
import inspect
import logging

import httpx

from src.config import settings
from src.schemas import (
    GetPointsResponse,
    InpostCredentials,
    PickupsCreatePickupOrderDto,
    PointDto,
    ReturnsCreateShipmentDto,
    ShippingCreateShipmentDto,
)

logger = logging.getLogger("courier-inpost-int-2025")

AUTH_SCOPES = (
    "openid api:points:read api:shipments:write "
    "api:tracking:read api:one-time-pickups:write api:one-time-pickups:read"
)


# ---------------------------------------------------------------------------
# Auth helpers
# ---------------------------------------------------------------------------

class ApiAuth:
    def __init__(self, client: httpx.AsyncClient, base_url: str = "") -> None:
        self._client = client
        self._base_url = base_url or settings.api_url

    async def get_access_token(self, client_id: str, client_secret: str) -> str:
        """POST /oauth2/token — obtain OAuth2 access token (2025 endpoint)."""
        response = await self._client.post(
            f"{self._base_url}/oauth2/token",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data={
                "client_id": client_id,
                "client_secret": client_secret,
                "grant_type": "client_credentials",
                "scope": AUTH_SCOPES,
            },
        )
        response.raise_for_status()
        return response.json()["access_token"]


async def refresh_credentials(
    credentials: InpostCredentials,
    client: httpx.AsyncClient,
    base_url: str = "",
) -> str:
    """Refresh InPost access token and update credentials object."""
    token = await ApiAuth(client, base_url).get_access_token(
        credentials.organization_id, credentials.client_secret,
    )
    credentials.access_token = token
    return token


def retry_on_unauthorized(func):
    """Decorator: retry on 401 after refreshing the access token."""
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 401:
                sig = inspect.signature(func)
                bound_args = sig.bind(*args, **kwargs)
                bound_args.apply_defaults()
                credentials = bound_args.arguments.get("credentials")
                self = bound_args.arguments.get("self")
                if credentials and self:
                    await refresh_credentials(credentials, self._client)
                    return await func(*args, **kwargs)
            raise
    return wrapper


def handle_errors(func):
    """Decorator: convert httpx.HTTPStatusError to formatted error tuple."""
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except httpx.HTTPStatusError as exc:
            return _format_rest_error_response(exc.response)
    return wrapper


def _format_rest_error_response(response: httpx.Response) -> tuple[str, int]:
    try:
        resp_json = response.json()
        msg = resp_json.get("message", "")
        if not msg:
            msg = str(resp_json)
    except Exception:
        msg = response.text
    logger.error(
        "InPost API error — path=%s status=%s",
        response.url.path, response.status_code,
    )
    return msg, response.status_code


# ---------------------------------------------------------------------------
# Shipping API (v2)
# ---------------------------------------------------------------------------

class ApiShipping:
    def __init__(self, client: httpx.AsyncClient, base_url: str = "") -> None:
        self._client = client
        self._base_url = base_url or settings.api_url

    async def post_create_shipment(
        self,
        organization_id: str,
        shipment_data: ShippingCreateShipmentDto,
        auth_header: dict[str, str],
        deduplication_id: str | None = None,
    ) -> str:
        """POST /shipping/v2/organizations/{orgId}/shipments — returns trackingNumber."""
        headers: dict[str, str] = {"Content-Type": "application/json", **auth_header}
        if deduplication_id:
            headers["X-Inpost-Deduplication-Id"] = deduplication_id
        url = f"{self._base_url}/shipping/v2/organizations/{organization_id}/shipments"
        response = await self._client.post(
            url,
            headers=headers,
            json=shipment_data.model_dump(by_alias=True, exclude_none=True),
        )
        response.raise_for_status()
        return response.json()["trackingNumber"]

    async def get_shipment_label(
        self,
        organization_id: str,
        tracking_number: str,
        accept_format: str,
        auth_header: dict[str, str],
    ) -> dict:
        """GET /shipping/v2/organizations/{orgId}/shipments/{trackingNumber}/label."""
        url = (
            f"{self._base_url}/shipping/v2/organizations/{organization_id}"
            f"/shipments/{tracking_number}/label"
        )
        response = await self._client.get(
            url,
            headers={
                "Content-Type": "application/json",
                "Accept": accept_format,
                **auth_header,
            },
        )
        response.raise_for_status()
        return response.json()

    async def get_shipment_details_by_tracking_number(
        self,
        organization_id: str,
        tracking_number: str,
        auth_header: dict[str, str],
    ) -> dict:
        """GET /shipping/v2/organizations/{orgId}/shipments/{trackingNumber}."""
        url = (
            f"{self._base_url}/shipping/v2/organizations/{organization_id}"
            f"/shipments/{tracking_number}"
        )
        response = await self._client.get(
            url,
            headers={"Content-Type": "application/json", **auth_header},
        )
        response.raise_for_status()
        return response.json()


# ---------------------------------------------------------------------------
# Tracking API (v1)
# ---------------------------------------------------------------------------

class ApiTracking:
    def __init__(self, client: httpx.AsyncClient, base_url: str = "") -> None:
        self._client = client
        self._base_url = base_url or settings.api_url

    async def get_parcel_tracking_events(
        self,
        tracking_numbers: list[str],
        event_version: str | None = None,
    ) -> dict:
        """GET /tracking/v1/parcels — no auth header required in 2025 API."""
        headers: dict[str, str] = {"Content-Type": "application/json"}
        if event_version:
            headers["x-inpost-event-version"] = event_version
        response = await self._client.get(
            f"{self._base_url}/tracking/v1/parcels",
            headers=headers,
            params={"trackingNumbers": tracking_numbers},
        )
        response.raise_for_status()
        return response.json()


# ---------------------------------------------------------------------------
# Pickups API (v1)
# ---------------------------------------------------------------------------

class ApiPickups:
    def __init__(self, client: httpx.AsyncClient, base_url: str = "") -> None:
        self._client = client
        self._base_url = base_url or settings.api_url

    async def post_create_pickup_order(
        self,
        organization_id: str,
        pickup_data: PickupsCreatePickupOrderDto,
        auth_header: dict[str, str],
    ) -> dict:
        """POST /pickups/v1/organizations/{orgId}/one-time-pickups."""
        url = f"{self._base_url}/pickups/v1/organizations/{organization_id}/one-time-pickups"
        response = await self._client.post(
            url,
            headers={"Content-Type": "application/json", **auth_header},
            json=pickup_data.model_dump(by_alias=True, exclude_none=True),
        )
        response.raise_for_status()
        return response.json()

    async def get_pickup_orders(
        self,
        organization_id: str,
        auth_header: dict[str, str],
        page: int | None = None,
        size: int | None = None,
    ) -> dict:
        """GET /pickups/v1/organizations/{orgId}/one-time-pickups."""
        url = f"{self._base_url}/pickups/v1/organizations/{organization_id}/one-time-pickups"
        response = await self._client.get(
            url,
            headers={"Content-Type": "application/json", **auth_header},
            params={"page": page, "size": size},
        )
        response.raise_for_status()
        return response.json()

    async def get_pickup_order_by_id(
        self,
        organization_id: str,
        order_id: str,
        auth_header: dict[str, str],
    ) -> dict:
        """GET /pickups/v1/organizations/{orgId}/one-time-pickups/{orderId}."""
        url = (
            f"{self._base_url}/pickups/v1/organizations/{organization_id}"
            f"/one-time-pickups/{order_id}"
        )
        response = await self._client.get(
            url,
            headers={"Content-Type": "application/json", **auth_header},
        )
        response.raise_for_status()
        return response.json()

    async def put_cancel_pickup_order(
        self,
        organization_id: str,
        order_id: str,
        auth_header: dict[str, str],
    ) -> dict:
        """PUT /pickups/v1/organizations/{orgId}/one-time-pickups/{orderId}/cancel."""
        url = (
            f"{self._base_url}/pickups/v1/organizations/{organization_id}"
            f"/one-time-pickups/{order_id}/cancel"
        )
        response = await self._client.put(
            url,
            headers={"Content-Type": "application/json", **auth_header},
        )
        response.raise_for_status()
        return response.json()

    async def get_cutoff_pickup_time(
        self,
        postal_code: str,
        country_code: str,
        auth_header: dict[str, str],
    ) -> dict:
        """GET /pickups/v1/cutoff-time."""
        response = await self._client.get(
            f"{self._base_url}/pickups/v1/cutoff-time",
            headers={"Content-Type": "application/json", **auth_header},
            params={"postalCode": postal_code, "countryCode": country_code},
        )
        response.raise_for_status()
        return response.json()


# ---------------------------------------------------------------------------
# Location API (v1) — replaces Points API from 2024
# ---------------------------------------------------------------------------

class ApiLocation:
    def __init__(self, client: httpx.AsyncClient, base_url: str = "") -> None:
        self._client = client
        self._base_url = base_url or settings.api_url

    async def get_points(
        self,
        auth_header: dict[str, str],
        page: str | None = None,
        per_page: str | None = None,
        limit: str | None = None,
        address_country: str | None = None,
        address_administrative_area: str | None = None,
        address_city: str | None = None,
        address_postal_code: str | None = None,
        capabilities: str | None = None,
        type_: str | None = None,
        header_accept_language: str | None = None,
    ) -> GetPointsResponse:
        """GET /location/v1/points."""
        response = await self._client.get(
            f"{self._base_url}/location/v1/points",
            params={
                "page": page,
                "perPage": per_page,
                "limit": limit,
                "address.country": address_country,
                "address.administrativeArea": address_administrative_area,
                "address.city": address_city,
                "address.postalCode": address_postal_code,
                "capabilities": capabilities,
                "type": type_,
            },
            headers=self._create_headers(auth_header, header_accept_language),
        )
        response.raise_for_status()
        return GetPointsResponse(**response.json())

    async def get_point_by_id(
        self,
        id_: str,
        auth_header: dict[str, str],
        header_accept_language: str | None = None,
    ) -> PointDto:
        """GET /location/v1/points/{id}."""
        response = await self._client.get(
            f"{self._base_url}/location/v1/points/{id_}",
            headers=self._create_headers(auth_header, header_accept_language),
        )
        response.raise_for_status()
        return PointDto(**response.json())

    async def get_points_by_location(
        self,
        auth_header: dict[str, str],
        header_accept_language: str | None = None,
        page: str | None = None,
        per_page: str | None = None,
        relative_point: str | None = None,
        relative_post_code: str | None = None,
        max_distance: str | None = None,
        address_country: str | None = None,
        limit: str | None = None,
        capabilities: str | None = None,
        type_: str | None = None,
    ) -> GetPointsResponse:
        """GET /location/v1/points/search-by-location."""
        response = await self._client.get(
            f"{self._base_url}/location/v1/points/search-by-location",
            params={
                "page": page,
                "perPage": per_page,
                "relativePoint": relative_point,
                "relativePostCode": relative_post_code,
                "maxDistance": max_distance,
                "address.country": address_country,
                "limit": limit,
                "capabilities": capabilities,
                "type": type_,
            },
            headers=self._create_headers(auth_header, header_accept_language),
        )
        response.raise_for_status()
        return GetPointsResponse(**response.json())

    @staticmethod
    def _create_headers(
        auth_header: dict[str, str],
        header_accept_language: str | None,
    ) -> dict[str, str]:
        return {
            "Accept-Language": header_accept_language or "pl-PL",
            "Content-Type": "application/json",
            **auth_header,
        }


# ---------------------------------------------------------------------------
# Returns API (v1)
# ---------------------------------------------------------------------------

class ApiReturns:
    def __init__(self, client: httpx.AsyncClient, base_url: str = "") -> None:
        self._client = client
        self._base_url = base_url or settings.api_url

    async def post_create_shipment(
        self,
        organization_id: str,
        shipment_data: ReturnsCreateShipmentDto,
        auth_header: dict[str, str],
    ) -> dict:
        """POST /returns/v1/organizations/{orgId}/shipments — create return shipment."""
        url = f"{self._base_url}/returns/v1/organizations/{organization_id}/shipments"
        response = await self._client.post(
            url,
            headers={"Content-Type": "application/json", **auth_header},
            json=shipment_data.model_dump(by_alias=True, exclude_none=True),
        )
        response.raise_for_status()
        return response.json()

    async def get_shipment_information(
        self,
        organization_id: str,
        shipment_id: str,
        auth_header: dict[str, str],
    ) -> dict:
        """GET /returns/v1/organizations/{orgId}/shipments/{shipmentId}."""
        url = (
            f"{self._base_url}/returns/v1/organizations/{organization_id}"
            f"/shipments/{shipment_id}"
        )
        response = await self._client.get(
            url,
            headers={"Content-Type": "application/json", **auth_header},
        )
        response.raise_for_status()
        return response.json()

    async def get_parcel_label(
        self,
        organization_id: str,
        tracking_number: str,
        accept_format: str,
        auth_header: dict[str, str],
    ) -> dict:
        """GET /returns/v1/organizations/{orgId}/shipments/{trackingNumber}/label."""
        url = (
            f"{self._base_url}/returns/v1/organizations/{organization_id}"
            f"/shipments/{tracking_number}/label"
        )
        response = await self._client.get(
            url,
            headers={
                "Content-Type": "application/json",
                "Accept": accept_format,
                **auth_header,
            },
        )
        response.raise_for_status()
        return response.json()
