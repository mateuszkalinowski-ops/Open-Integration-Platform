"""InPost International 2024 — modular API classes.

Ported from meriship version_international_2024/api/ directory.
All calls converted from requests (sync) to httpx (async).
"""

from __future__ import annotations

import functools
import inspect
import logging

import httpx

from src.config import settings
from src.schemas import (
    CreateShipmentDTO,
    CreateShipmentResponseDto,
    GetPointsResponse,
    InpostCredentials,
    PickupsCreatePickupOrderDto,
    PointDto,
    ShipmentTypeEnum,
)

logger = logging.getLogger("courier-inpost-int-2024")

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
        """POST /auth/token — obtain OAuth2 access token."""
        response = await self._client.post(
            f"{self._base_url}/auth/token",
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
        "InPost API error — url=%s status=%s",
        response.url.path, response.status_code,
    )
    return msg, response.status_code


# ---------------------------------------------------------------------------
# Shipping API
# ---------------------------------------------------------------------------

class ApiShipping:
    def __init__(self, client: httpx.AsyncClient, base_url: str = "") -> None:
        self._client = client
        self._base_url = base_url or settings.api_url

    async def post_create_shipment(
        self,
        shipment_data: CreateShipmentDTO,
        auth_header: dict[str, str],
        shipment_type: ShipmentTypeEnum,
    ) -> CreateShipmentResponseDto:
        """POST /shipments/{type} — create shipment."""
        response = await self._client.post(
            f"{self._base_url}{shipment_type.value}",
            headers={"Content-Type": "application/json", **auth_header},
            json=shipment_data.model_dump(by_alias=True),
        )
        response.raise_for_status()
        return CreateShipmentResponseDto(**response.json())

    async def get_shipment_label(
        self,
        shipment_uuid: str,
        auth_header: dict[str, str],
    ) -> dict:
        """GET /shipments/{uuid}/label — retrieve label."""
        response = await self._client.get(
            f"{self._base_url}/shipments/{shipment_uuid}/label",
            headers={"Content-Type": "application/json", **auth_header},
        )
        response.raise_for_status()
        return response.json()

    async def get_shipment_details_by_uuid(
        self,
        shipment_uuid: str,
        auth_header: dict[str, str],
    ) -> dict:
        """GET /shipments/{uuid} — shipment details."""
        response = await self._client.get(
            f"{self._base_url}/shipments/{shipment_uuid}",
            headers={"Content-Type": "application/json", **auth_header},
        )
        response.raise_for_status()
        return response.json()


# ---------------------------------------------------------------------------
# Tracking API
# ---------------------------------------------------------------------------

class ApiTracking:
    def __init__(self, client: httpx.AsyncClient, base_url: str = "") -> None:
        self._client = client
        self._base_url = base_url or settings.api_url

    async def get_parcel_tracking_events(
        self,
        auth_header: dict[str, str],
        tracking_numbers: list[str],
        event_version: str | None = None,
    ) -> dict:
        """GET /track/parcels — parcel tracking events."""
        headers: dict[str, str] = {"Content-Type": "application/json", **auth_header}
        if event_version:
            headers["x-inpost-event-version"] = event_version
        response = await self._client.get(
            f"{self._base_url}/track/parcels",
            headers=headers,
            params={"trackingNumbers": tracking_numbers},
        )
        response.raise_for_status()
        return response.json()


# ---------------------------------------------------------------------------
# Pickups API
# ---------------------------------------------------------------------------

class ApiPickups:
    def __init__(self, client: httpx.AsyncClient, base_url: str = "") -> None:
        self._client = client
        self._base_url = base_url or settings.api_url

    async def post_create_pickup_order(
        self,
        pickup_data: PickupsCreatePickupOrderDto,
        auth_header: dict[str, str],
    ) -> dict:
        """POST /one-time-pickups — create pickup order."""
        response = await self._client.post(
            f"{self._base_url}/one-time-pickups",
            headers={"Content-Type": "application/json", **auth_header},
            json=pickup_data.model_dump(by_alias=True),
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
        order_id: str,
        auth_header: dict[str, str],
    ) -> dict:
        """GET /one-time-pickups/{orderId}."""
        response = await self._client.get(
            f"{self._base_url}/one-time-pickups/{order_id}",
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
        """GET /cutoff-time — latest hour for pickup creation."""
        response = await self._client.get(
            f"{self._base_url}/cutoff-time",
            headers={"Content-Type": "application/json", **auth_header},
            params={"postalCode": postal_code, "countryCode": country_code},
        )
        response.raise_for_status()
        return response.json()


# ---------------------------------------------------------------------------
# Points API
# ---------------------------------------------------------------------------

class ApiPoints:
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
        """GET /points — search InPost points."""
        response = await self._client.get(
            f"{self._base_url}/points",
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
        """GET /points/{id} — point details."""
        response = await self._client.get(
            f"{self._base_url}/points/{id_}",
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
        """GET /points/search-by-location — proximity search."""
        response = await self._client.get(
            f"{self._base_url}/points/search-by-location",
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
