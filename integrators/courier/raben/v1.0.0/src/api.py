"""Raben Group — modular API classes.

Raben myRaben platform API integration.
All calls use httpx (async).

API areas:
- Auth: JWT token-based authentication via myRaben
- Orders: Transport order creation and management (myOrder)
- Tracking: Shipment tracking with ETA (Track & Trace)
- Labels: Shipping label/document retrieval
- Claims: Complaint submission (myClaim)
- PCD: Photo Confirming Delivery document retrieval
"""

from __future__ import annotations

import functools
import inspect
import logging

import httpx

from src.config import settings
from src.schemas import (
    CreateClaimRequest,
    CreateTransportOrderRequest,
    RabenCredentials,
)

logger = logging.getLogger("courier-raben")


# ---------------------------------------------------------------------------
# Auth helpers
# ---------------------------------------------------------------------------

class ApiAuth:
    def __init__(self, client: httpx.AsyncClient, base_url: str = "") -> None:
        self._client = client
        self._base_url = base_url or settings.api_url

    async def get_access_token(self, username: str, password: str) -> str:
        """POST /auth/login — obtain JWT access token."""
        response = await self._client.post(
            f"{self._base_url}/auth/login",
            headers={"Content-Type": "application/json"},
            json={"username": username, "password": password},
        )
        response.raise_for_status()
        return response.json()["accessToken"]


async def refresh_credentials(
    credentials: RabenCredentials,
    client: httpx.AsyncClient,
    base_url: str = "",
) -> str:
    """Refresh Raben JWT token and update credentials object."""
    token = await ApiAuth(client, base_url).get_access_token(
        credentials.username, credentials.password,
    )
    credentials.access_token = token
    return token


def _build_auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


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
                self_ = bound_args.arguments.get("self")
                if credentials and self_:
                    await refresh_credentials(credentials, self_._client, self_._base_url)
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
            return _format_error_response(exc.response)
    return wrapper


def _format_error_response(response: httpx.Response) -> tuple[str, int]:
    try:
        resp_json = response.json()
        msg = resp_json.get("message", "") or resp_json.get("error", "")
        if not msg:
            msg = str(resp_json)
    except Exception:
        msg = response.text
    logger.error(
        "Raben API error — url=%s status=%s",
        response.url.path, response.status_code,
    )
    return msg, response.status_code


# ---------------------------------------------------------------------------
# Orders API (myOrder)
# ---------------------------------------------------------------------------

class ApiOrders:
    def __init__(self, client: httpx.AsyncClient, base_url: str = "") -> None:
        self._client = client
        self._base_url = base_url or settings.api_url

    @retry_on_unauthorized
    @handle_errors
    async def create_transport_order(
        self,
        order_data: CreateTransportOrderRequest,
        credentials: RabenCredentials,
    ) -> tuple[dict, int]:
        """POST /orders — create a new transport order."""
        auth_header = _build_auth_header(credentials.access_token or "")
        response = await self._client.post(
            f"{self._base_url}/orders",
            headers={"Content-Type": "application/json", **auth_header},
            json=order_data.model_dump(by_alias=True, exclude_none=True, mode="json"),
        )
        response.raise_for_status()
        return response.json(), response.status_code

    @retry_on_unauthorized
    @handle_errors
    async def get_order(
        self,
        waybill_number: str,
        credentials: RabenCredentials,
    ) -> tuple[dict, int]:
        """GET /orders/{waybillNumber} — get order details."""
        auth_header = _build_auth_header(credentials.access_token or "")
        response = await self._client.get(
            f"{self._base_url}/orders/{waybill_number}",
            headers={"Content-Type": "application/json", **auth_header},
        )
        response.raise_for_status()
        return response.json(), response.status_code

    @retry_on_unauthorized
    @handle_errors
    async def cancel_order(
        self,
        waybill_number: str,
        credentials: RabenCredentials,
    ) -> tuple[dict, int]:
        """PUT /orders/{waybillNumber}/cancel — cancel transport order."""
        auth_header = _build_auth_header(credentials.access_token or "")
        response = await self._client.put(
            f"{self._base_url}/orders/{waybill_number}/cancel",
            headers={"Content-Type": "application/json", **auth_header},
        )
        response.raise_for_status()
        return response.json(), response.status_code


# ---------------------------------------------------------------------------
# Tracking API (Track & Trace)
# ---------------------------------------------------------------------------

class ApiTracking:
    def __init__(self, client: httpx.AsyncClient, base_url: str = "") -> None:
        self._client = client
        self._base_url = base_url or settings.api_url

    @retry_on_unauthorized
    @handle_errors
    async def get_tracking(
        self,
        waybill_number: str,
        credentials: RabenCredentials,
    ) -> tuple[dict, int]:
        """GET /tracking/{waybillNumber} — full tracking history."""
        auth_header = _build_auth_header(credentials.access_token or "")
        response = await self._client.get(
            f"{self._base_url}/tracking/{waybill_number}",
            headers={"Content-Type": "application/json", **auth_header},
        )
        response.raise_for_status()
        return response.json(), response.status_code

    @retry_on_unauthorized
    @handle_errors
    async def get_shipment_status(
        self,
        waybill_number: str,
        credentials: RabenCredentials,
    ) -> tuple[dict, int]:
        """GET /tracking/{waybillNumber}/status — current status with ETA."""
        auth_header = _build_auth_header(credentials.access_token or "")
        response = await self._client.get(
            f"{self._base_url}/tracking/{waybill_number}/status",
            headers={"Content-Type": "application/json", **auth_header},
        )
        response.raise_for_status()
        return response.json(), response.status_code

    @retry_on_unauthorized
    @handle_errors
    async def get_eta(
        self,
        waybill_number: str,
        credentials: RabenCredentials,
    ) -> tuple[dict, int]:
        """GET /tracking/{waybillNumber}/eta — estimated time of arrival."""
        auth_header = _build_auth_header(credentials.access_token or "")
        response = await self._client.get(
            f"{self._base_url}/tracking/{waybill_number}/eta",
            headers={"Content-Type": "application/json", **auth_header},
        )
        response.raise_for_status()
        return response.json(), response.status_code


# ---------------------------------------------------------------------------
# Labels API
# ---------------------------------------------------------------------------

class ApiLabels:
    def __init__(self, client: httpx.AsyncClient, base_url: str = "") -> None:
        self._client = client
        self._base_url = base_url or settings.api_url

    @retry_on_unauthorized
    @handle_errors
    async def get_label(
        self,
        waybill_number: str,
        label_format: str,
        credentials: RabenCredentials,
    ) -> tuple[bytes | str, int]:
        """GET /labels/{waybillNumber} — shipping label (PDF or ZPL)."""
        auth_header = _build_auth_header(credentials.access_token or "")
        accept = "application/pdf" if label_format == "pdf" else "application/x-zpl"
        response = await self._client.get(
            f"{self._base_url}/labels/{waybill_number}",
            headers={"Accept": accept, **auth_header},
        )
        response.raise_for_status()
        return response.content, response.status_code


# ---------------------------------------------------------------------------
# Claims API (myClaim)
# ---------------------------------------------------------------------------

class ApiClaims:
    def __init__(self, client: httpx.AsyncClient, base_url: str = "") -> None:
        self._client = client
        self._base_url = base_url or settings.api_url

    @retry_on_unauthorized
    @handle_errors
    async def create_claim(
        self,
        claim_data: CreateClaimRequest,
        credentials: RabenCredentials,
    ) -> tuple[dict, int]:
        """POST /claims — submit a complaint."""
        auth_header = _build_auth_header(credentials.access_token or "")
        response = await self._client.post(
            f"{self._base_url}/claims",
            headers={"Content-Type": "application/json", **auth_header},
            json=claim_data.model_dump(by_alias=True, exclude_none=True),
        )
        response.raise_for_status()
        return response.json(), response.status_code

    @retry_on_unauthorized
    @handle_errors
    async def get_claim(
        self,
        claim_id: str,
        credentials: RabenCredentials,
    ) -> tuple[dict, int]:
        """GET /claims/{claimId} — get claim details."""
        auth_header = _build_auth_header(credentials.access_token or "")
        response = await self._client.get(
            f"{self._base_url}/claims/{claim_id}",
            headers={"Content-Type": "application/json", **auth_header},
        )
        response.raise_for_status()
        return response.json(), response.status_code


# ---------------------------------------------------------------------------
# PCD API (Photo Confirming Delivery)
# ---------------------------------------------------------------------------

class ApiPcd:
    def __init__(self, client: httpx.AsyncClient, base_url: str = "") -> None:
        self._client = client
        self._base_url = base_url or settings.api_url

    @retry_on_unauthorized
    @handle_errors
    async def get_delivery_confirmation(
        self,
        waybill_number: str,
        credentials: RabenCredentials,
    ) -> tuple[dict, int]:
        """GET /deliveries/{waybillNumber}/confirmation — PCD with photos."""
        auth_header = _build_auth_header(credentials.access_token or "")
        response = await self._client.get(
            f"{self._base_url}/deliveries/{waybill_number}/confirmation",
            headers={"Content-Type": "application/json", **auth_header},
        )
        response.raise_for_status()
        return response.json(), response.status_code
