"""FX Couriers (KurierSystem) — modular API classes.

Base URL: https://fxcouriers.kuriersystem.pl/api/rest
Authentication: Bearer token in Authorization header.

API areas:
- Health: GET /health-check
- Services: GET /services
- Company: GET|PUT /company/{company_id}
- Orders: POST /order, GET /orders, GET /order/{id}, DELETE /order/{id}
- Tracking: GET /order-tracking/{order_id}
- Labels: GET /label/{order_id}
- Shipments: POST /shipments, GET|DELETE /shipment/{order_id}
"""

from __future__ import annotations

import functools
import logging

import httpx

from src.config import settings
from src.schemas import FxCouriersCredentials

logger = logging.getLogger("courier-fxcouriers")


# ---------------------------------------------------------------------------
# Auth helpers
# ---------------------------------------------------------------------------

def _build_auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def handle_errors(func):
    """Decorator: convert httpx.HTTPStatusError to formatted error tuple."""
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except httpx.HTTPStatusError as exc:
            return _format_error_response(exc.response)
    return wrapper


def _format_error_response(response: httpx.Response) -> tuple[str, int]:
    try:
        resp_json = response.json()
        msg = resp_json.get("message", "") or resp_json.get("error", "")
        if not msg:
            msg = str(resp_json)
    except (ValueError, KeyError):
        msg = response.text
    logger.error(
        "FX Couriers API error — url=%s status=%s",
        response.url, response.status_code,
    )
    return msg, response.status_code


# ---------------------------------------------------------------------------
# Services API
# ---------------------------------------------------------------------------

class ApiServices:
    def __init__(self, client: httpx.AsyncClient) -> None:
        self._client = client

    @handle_errors
    async def get_services(
        self, credentials: FxCouriersCredentials,
    ) -> tuple[dict, int]:
        """GET /services — available services and package configuration."""
        response = await self._client.get(
            f"{settings.fxcouriers_api_url}/services",
            headers=_build_auth_header(credentials.api_token),
        )
        response.raise_for_status()
        return response.json(), response.status_code


# ---------------------------------------------------------------------------
# Company API
# ---------------------------------------------------------------------------

class ApiCompany:
    def __init__(self, client: httpx.AsyncClient) -> None:
        self._client = client

    @handle_errors
    async def get_company(
        self, company_id: int, credentials: FxCouriersCredentials,
    ) -> tuple[dict, int]:
        """GET /company/{company_id} — company registration and address data."""
        response = await self._client.get(
            f"{settings.fxcouriers_api_url}/company/{company_id}",
            headers=_build_auth_header(credentials.api_token),
        )
        response.raise_for_status()
        return response.json(), response.status_code


# ---------------------------------------------------------------------------
# Orders API
# ---------------------------------------------------------------------------

class ApiOrders:
    def __init__(self, client: httpx.AsyncClient) -> None:
        self._client = client

    @handle_errors
    async def create_order(
        self, order_data: dict, credentials: FxCouriersCredentials,
    ) -> tuple[dict, int]:
        """POST /order — create a new transport order."""
        response = await self._client.post(
            f"{settings.fxcouriers_api_url}/order",
            headers={
                "Content-Type": "application/json",
                **_build_auth_header(credentials.api_token),
            },
            json=order_data,
        )
        response.raise_for_status()
        return response.json(), response.status_code

    @handle_errors
    async def get_orders(
        self,
        credentials: FxCouriersCredentials,
        since: str | None = None,
        offset: int | None = None,
        company_id: int | None = None,
    ) -> tuple[dict, int]:
        """GET /orders — list orders with optional filtering."""
        params: dict[str, str | int] = {}
        if since:
            params["since"] = since
        if offset is not None:
            params["offset"] = offset
        if company_id is not None:
            params["company_id"] = company_id

        response = await self._client.get(
            f"{settings.fxcouriers_api_url}/orders",
            headers=_build_auth_header(credentials.api_token),
            params=params,
        )
        response.raise_for_status()
        return response.json(), response.status_code

    @handle_errors
    async def get_order(
        self, order_id: int, credentials: FxCouriersCredentials,
    ) -> tuple[dict, int]:
        """GET /order/{order_id} — single order details."""
        response = await self._client.get(
            f"{settings.fxcouriers_api_url}/order/{order_id}",
            headers=_build_auth_header(credentials.api_token),
        )
        response.raise_for_status()
        return response.json(), response.status_code

    @handle_errors
    async def delete_order(
        self, order_id: int, credentials: FxCouriersCredentials,
    ) -> tuple[dict | str, int]:
        """DELETE /order/{order_id} — delete an unshipped order."""
        response = await self._client.delete(
            f"{settings.fxcouriers_api_url}/order/{order_id}",
            headers=_build_auth_header(credentials.api_token),
        )
        response.raise_for_status()
        try:
            return response.json(), response.status_code
        except (ValueError, KeyError):
            return response.text, response.status_code


# ---------------------------------------------------------------------------
# Tracking API
# ---------------------------------------------------------------------------

class ApiTracking:
    def __init__(self, client: httpx.AsyncClient) -> None:
        self._client = client

    @handle_errors
    async def get_tracking(
        self, order_id: int, credentials: FxCouriersCredentials,
    ) -> tuple[dict, int]:
        """GET /order-tracking/{order_id} — tracking events."""
        response = await self._client.get(
            f"{settings.fxcouriers_api_url}/order-tracking/{order_id}",
            headers=_build_auth_header(credentials.api_token),
        )
        response.raise_for_status()
        return response.json(), response.status_code


# ---------------------------------------------------------------------------
# Labels API
# ---------------------------------------------------------------------------

class ApiLabels:
    def __init__(self, client: httpx.AsyncClient) -> None:
        self._client = client

    @handle_errors
    async def get_label(
        self, order_id: int, credentials: FxCouriersCredentials,
    ) -> tuple[bytes | str, int]:
        """GET /label/{order_id} — shipping label as PDF."""
        response = await self._client.get(
            f"{settings.fxcouriers_api_url}/label/{order_id}",
            headers=_build_auth_header(credentials.api_token),
        )
        response.raise_for_status()
        return response.content, response.status_code


# ---------------------------------------------------------------------------
# Shipments API (pickup scheduling)
# ---------------------------------------------------------------------------

class ApiShipments:
    def __init__(self, client: httpx.AsyncClient) -> None:
        self._client = client

    @handle_errors
    async def create_shipment(
        self, shipment_data: dict, credentials: FxCouriersCredentials,
    ) -> tuple[dict, int]:
        """POST /shipments — schedule pickup for given orders."""
        response = await self._client.post(
            f"{settings.fxcouriers_api_url}/shipments",
            headers={
                "Content-Type": "application/json",
                **_build_auth_header(credentials.api_token),
            },
            json=shipment_data,
        )
        response.raise_for_status()
        return response.json(), response.status_code

    @handle_errors
    async def get_shipment(
        self, order_id: int, credentials: FxCouriersCredentials,
    ) -> tuple[dict, int]:
        """GET /shipment/{order_id} — get shipment/pickup details."""
        response = await self._client.get(
            f"{settings.fxcouriers_api_url}/shipment/{order_id}",
            headers=_build_auth_header(credentials.api_token),
        )
        response.raise_for_status()
        return response.json(), response.status_code

    @handle_errors
    async def delete_shipment(
        self, order_id: int, credentials: FxCouriersCredentials,
    ) -> tuple[dict | str, int]:
        """DELETE /shipment/{order_id} — cancel scheduled pickup."""
        response = await self._client.delete(
            f"{settings.fxcouriers_api_url}/shipment/{order_id}",
            headers=_build_auth_header(credentials.api_token),
        )
        response.raise_for_status()
        try:
            return response.json(), response.status_code
        except (ValueError, KeyError):
            return response.text, response.status_code
