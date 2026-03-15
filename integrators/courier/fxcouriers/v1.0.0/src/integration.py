"""FX Couriers (KurierSystem) — business logic layer.

Orchestrates API calls and transforms data between the FastAPI
request schemas and the FX Couriers REST API.
"""

from __future__ import annotations

import logging

import httpx

from src.api import (
    ApiCompany,
    ApiLabels,
    ApiOrders,
    ApiServices,
    ApiShipments,
    ApiTracking,
)
from src.config import settings
from src.schemas import (
    CreateOrderApiRequest,
    CreatePickupApiRequest,
    FxCouriersCredentials,
    FxCreateOrderRequest,
    FxCreateShipmentRequest,
)

logger = logging.getLogger("courier-fxcouriers")

FXCOURIERS_STATUS_MAP: dict[str, str] = {
    "NEW": "CREATED",
    "WAITING_APPROVAL": "CREATED",
    "ACCEPTED": "CONFIRMED",
    "RUNNING": "IN_TRANSIT",
    "PICKUP": "PICKED_UP",
    "CLOSED": "DELIVERED",
    "RETURN": "RETURNED",
    "PROBLEM": "FAILED",
    "FAILED": "FAILED",
    "CANCELLED": "CANCELLED",
}


def _map_status(raw_status: str) -> str:
    return FXCOURIERS_STATUS_MAP.get(raw_status.upper(), raw_status)


class FxCouriersIntegration:
    def __init__(self) -> None:
        self._client = httpx.AsyncClient(timeout=settings.rest_timeout)
        self._services = ApiServices(self._client)
        self._company = ApiCompany(self._client)
        self._orders = ApiOrders(self._client)
        self._tracking = ApiTracking(self._client)
        self._labels = ApiLabels(self._client)
        self._shipments = ApiShipments(self._client)

    # -------------------------------------------------------------------
    # Services
    # -------------------------------------------------------------------

    async def get_services(
        self,
        credentials: FxCouriersCredentials,
    ) -> tuple[dict, int]:
        """Retrieve available services and package configuration."""
        result = await self._services.get_services(credentials)
        if isinstance(result, tuple):
            return result
        return result, 200

    # -------------------------------------------------------------------
    # Company
    # -------------------------------------------------------------------

    async def get_company(
        self,
        credentials: FxCouriersCredentials,
        company_id: int,
    ) -> tuple[dict, int]:
        """Retrieve company registration and address data."""
        result = await self._company.get_company(company_id, credentials)
        if isinstance(result, tuple):
            return result
        return result, 200

    # -------------------------------------------------------------------
    # Order operations
    # -------------------------------------------------------------------

    async def create_order(
        self,
        credentials: FxCouriersCredentials,
        request: CreateOrderApiRequest,
    ) -> tuple[dict, int]:
        """Create a new transport order."""
        order_dto = FxCreateOrderRequest(
            company_id=request.company_id,
            service_code=request.service_code,
            payment_method=request.payment_method,
            comment=request.comment,
            sender=request.sender,
            recipient=request.recipient,
            items=request.items,
            services=request.services,
        )

        order_data = order_dto.model_dump(exclude_none=True)
        result = await self._orders.create_order(order_data, credentials)
        if isinstance(result, tuple):
            return result
        return result, 201

    async def get_orders(
        self,
        credentials: FxCouriersCredentials,
        since: str | None = None,
        offset: int | None = None,
        company_id: int | None = None,
    ) -> tuple[dict, int]:
        """List orders with optional date and pagination filters."""
        result = await self._orders.get_orders(
            credentials,
            since=since,
            offset=offset,
            company_id=company_id,
        )
        if isinstance(result, tuple):
            return result
        return result, 200

    async def get_order(
        self,
        credentials: FxCouriersCredentials,
        order_id: int,
    ) -> tuple[dict, int]:
        """Get single order details."""
        result = await self._orders.get_order(order_id, credentials)
        if isinstance(result, tuple):
            return result
        return result, 200

    async def find_order_by_number(
        self,
        credentials: FxCouriersCredentials,
        order_number: str,
    ) -> tuple[dict, int]:
        """Find order by order_number (e.g. E000123) via paginated search."""
        offset = 0
        while True:
            result = await self._orders.get_orders(credentials, offset=offset)
            if isinstance(result, tuple) and len(result) == 2 and isinstance(result[1], int):
                if result[1] >= 400:
                    return result
                data = result[0]
            else:
                data = result

            order_list = data.get("order_list", [])
            if not order_list:
                return {"error": f"Order with number '{order_number}' not found"}, 404

            for order in order_list:
                if order.get("order_number") == order_number:
                    return order, 200

            if len(order_list) < 100:
                return {"error": f"Order with number '{order_number}' not found"}, 404
            offset += 100

    async def delete_order(
        self,
        credentials: FxCouriersCredentials,
        order_id: int,
    ) -> tuple[dict | str, int]:
        """Delete an order (only before pickup is scheduled)."""
        result = await self._orders.delete_order(order_id, credentials)
        if isinstance(result, tuple):
            return result
        return result, 200

    # -------------------------------------------------------------------
    # Tracking
    # -------------------------------------------------------------------

    async def get_tracking(
        self,
        credentials: FxCouriersCredentials,
        order_id: int,
    ) -> tuple[dict, int]:
        """Get order tracking information."""
        result = await self._tracking.get_tracking(order_id, credentials)
        if isinstance(result, tuple) and len(result) == 2 and isinstance(result[1], int):
            if result[1] >= 400:
                return result
            raw = result[0]
        else:
            raw = result

        if isinstance(raw, dict) and "status" in raw:
            raw["mapped_status"] = _map_status(raw["status"])

        return raw, 200

    async def get_order_status(
        self,
        credentials: FxCouriersCredentials,
        order_id: int,
    ) -> tuple[dict, int]:
        """Get current order status."""
        result = await self._orders.get_order(order_id, credentials)
        if isinstance(result, tuple) and len(result) == 2 and isinstance(result[1], int):
            if result[1] >= 400:
                return result
            raw = result[0]
        else:
            raw = result

        status_raw = raw.get("status", "")
        return {
            "order_id": raw.get("order_id"),
            "order_number": raw.get("order_number"),
            "status": status_raw,
            "mapped_status": _map_status(status_raw),
            "tracking_number": raw.get("tracking_number"),
            "tracking_url_internal": raw.get("tracking_url_internal"),
            "tracking_url_external": raw.get("tracking_url_external"),
        }, 200

    # -------------------------------------------------------------------
    # Labels
    # -------------------------------------------------------------------

    async def get_label(
        self,
        credentials: FxCouriersCredentials,
        order_id: int,
    ) -> tuple[bytes | str, int]:
        """Get shipping label as PDF."""
        result = await self._labels.get_label(order_id, credentials)
        if isinstance(result, tuple):
            return result
        return result, 200

    # -------------------------------------------------------------------
    # Shipment / Pickup operations
    # -------------------------------------------------------------------

    async def create_shipment(
        self,
        credentials: FxCouriersCredentials,
        request: CreatePickupApiRequest,
    ) -> tuple[dict, int]:
        """Schedule a pickup for specified orders."""
        shipment_dto = FxCreateShipmentRequest(
            pickup_date=request.pickup_date,
            pickup_time_from=request.pickup_time_from,
            pickup_time_to=request.pickup_time_to,
            order_id_list=request.order_id_list,
        )

        shipment_data = shipment_dto.model_dump(exclude_none=True)
        result = await self._shipments.create_shipment(shipment_data, credentials)
        if isinstance(result, tuple):
            return result
        return result, 201

    async def get_shipment(
        self,
        credentials: FxCouriersCredentials,
        order_id: int,
    ) -> tuple[dict, int]:
        """Get shipment/pickup details for an order."""
        result = await self._shipments.get_shipment(order_id, credentials)
        if isinstance(result, tuple):
            return result
        return result, 200

    async def cancel_shipment(
        self,
        credentials: FxCouriersCredentials,
        order_id: int,
    ) -> tuple[dict | str, int]:
        """Cancel a scheduled pickup."""
        result = await self._shipments.delete_shipment(order_id, credentials)
        if isinstance(result, tuple):
            return result
        return result, 200
