"""Raben Group — business logic layer.

Orchestrates API calls, handles authentication, and transforms data
between the FastAPI request schemas and the Raben API DTOs.
"""

from __future__ import annotations

import logging

import httpx

from src.api import (
    ApiClaims,
    ApiLabels,
    ApiOrders,
    ApiPcd,
    ApiTracking,
    refresh_credentials,
)
from src.config import settings
from src.schemas import (
    AdditionalServices,
    Address,
    ClaimType,
    ContactInfo,
    CreateClaimRequest,
    CreateShipmentRequest,
    CreateTransportOrderRequest,
    EtaInfo,
    RabenCredentials,
    ShipmentStatus,
    ShipmentStatusResponse,
    TrackingEvent,
    TrackingResponse,
)

logger = logging.getLogger("courier-raben")

RABEN_STATUS_MAP: dict[str, ShipmentStatus] = {
    "new": ShipmentStatus.CREATED,
    "registered": ShipmentStatus.CREATED,
    "accepted": ShipmentStatus.CREATED,
    "picked_up": ShipmentStatus.PICKED_UP,
    "collected": ShipmentStatus.PICKED_UP,
    "in_transit": ShipmentStatus.IN_TRANSIT,
    "hub_scan": ShipmentStatus.IN_TRANSIT,
    "at_terminal": ShipmentStatus.AT_TERMINAL,
    "cross_dock": ShipmentStatus.AT_TERMINAL,
    "out_for_delivery": ShipmentStatus.OUT_FOR_DELIVERY,
    "on_vehicle": ShipmentStatus.OUT_FOR_DELIVERY,
    "delivered": ShipmentStatus.DELIVERED,
    "pcd_confirmed": ShipmentStatus.DELIVERED,
    "cancelled": ShipmentStatus.CANCELLED,
    "exception": ShipmentStatus.EXCEPTION,
    "damage": ShipmentStatus.EXCEPTION,
    "returned": ShipmentStatus.RETURNED,
}


def _map_status(raw_status: str) -> ShipmentStatus:
    return RABEN_STATUS_MAP.get(raw_status.lower(), ShipmentStatus.IN_TRANSIT)


class RabenIntegration:
    def __init__(self) -> None:
        self._client = httpx.AsyncClient(timeout=settings.rest_timeout)
        self._orders = ApiOrders(self._client)
        self._tracking = ApiTracking(self._client)
        self._labels = ApiLabels(self._client)
        self._claims = ApiClaims(self._client)
        self._pcd = ApiPcd(self._client)

    async def _ensure_token(self, credentials: RabenCredentials) -> None:
        if not credentials.access_token:
            base_url = self._resolve_base_url(credentials)
            await refresh_credentials(credentials, self._client, base_url)

    def _resolve_base_url(self, credentials: RabenCredentials) -> str:
        if credentials.sandbox_mode:
            return settings.raben_sandbox_api_url
        return settings.raben_api_url

    # -------------------------------------------------------------------
    # Transport order operations (myOrder)
    # -------------------------------------------------------------------

    async def create_order(
        self,
        credentials: RabenCredentials,
        request: CreateShipmentRequest,
    ) -> tuple[dict, int]:
        """Create a transport order via Raben myOrder."""
        await self._ensure_token(credentials)

        order_dto = CreateTransportOrderRequest(
            sender=Address(
                street=request.sender.street,
                buildingNumber=request.sender.building_number,
                city=request.sender.city,
                postalCode=request.sender.postal_code,
                countryCode=request.sender.country_code,
            ),
            senderContact=ContactInfo(
                companyName=request.sender.company_name,
                contactPerson=request.sender.contact_person,
                phone=request.sender.phone,
                email=request.sender.email,
            ),
            receiver=Address(
                street=request.receiver.street,
                buildingNumber=request.receiver.building_number,
                city=request.receiver.city,
                postalCode=request.receiver.postal_code,
                countryCode=request.receiver.country_code,
            ),
            receiverContact=ContactInfo(
                companyName=request.receiver.company_name,
                contactPerson=request.receiver.contact_person,
                phone=request.receiver.phone,
                email=request.receiver.email,
            ),
            packages=request.packages,
            serviceType=request.service_type,
            pickupDate=request.pickup_date,
            reference=request.reference,
            comments=request.comments,
            additionalServices=AdditionalServices(
                pcdEnabled=request.pcd_enabled,
                emailNotification=request.email_notification,
                tailLiftPickup=request.tail_lift_pickup,
                tailLiftDelivery=request.tail_lift_delivery,
            ),
            cod=request.cod,
            codAmount=request.cod_amount,
        )

        result = await self._orders.create_transport_order(order_dto, credentials)
        if isinstance(result, tuple):
            return result
        return result, 201

    async def get_order(
        self,
        credentials: RabenCredentials,
        waybill_number: str,
    ) -> tuple[dict, int]:
        """Get transport order details."""
        await self._ensure_token(credentials)
        result = await self._orders.get_order(waybill_number, credentials)
        if isinstance(result, tuple):
            return result
        return result, 200

    async def cancel_order(
        self,
        credentials: RabenCredentials,
        waybill_number: str,
    ) -> tuple[dict, int]:
        """Cancel a transport order."""
        await self._ensure_token(credentials)
        result = await self._orders.cancel_order(waybill_number, credentials)
        if isinstance(result, tuple):
            return result
        return result, 200

    # -------------------------------------------------------------------
    # Tracking operations (Track & Trace)
    # -------------------------------------------------------------------

    async def get_tracking(
        self,
        credentials: RabenCredentials,
        waybill_number: str,
    ) -> tuple[dict, int]:
        """Get full tracking history with events."""
        await self._ensure_token(credentials)
        result = await self._tracking.get_tracking(waybill_number, credentials)
        if isinstance(result, tuple) and len(result) == 2 and isinstance(result[1], int):
            if result[1] >= 400:
                return result
            raw = result[0]
        else:
            raw = result

        events = [
            TrackingEvent(
                timestamp=ev.get("timestamp", ""),
                status=ev.get("status", ""),
                description=ev.get("description", ""),
                location=ev.get("location"),
                terminal=ev.get("terminal"),
            )
            for ev in raw.get("events", [])
        ]

        eta_raw = raw.get("eta")
        eta = None
        if eta_raw:
            eta = EtaInfo(
                etaFrom=eta_raw.get("etaFrom"),
                etaTo=eta_raw.get("etaTo"),
                lastUpdated=eta_raw.get("lastUpdated"),
            )

        tracking = TrackingResponse(
            waybillNumber=waybill_number,
            status=_map_status(raw.get("status", "in_transit")),
            events=events,
            eta=eta,
            deliveredAt=raw.get("deliveredAt"),
        )
        return tracking.model_dump(by_alias=True, mode="json"), 200

    async def get_shipment_status(
        self,
        credentials: RabenCredentials,
        waybill_number: str,
    ) -> tuple[dict, int]:
        """Get current shipment status with ETA."""
        await self._ensure_token(credentials)
        result = await self._tracking.get_shipment_status(waybill_number, credentials)
        if isinstance(result, tuple) and len(result) == 2 and isinstance(result[1], int):
            if result[1] >= 400:
                return result
            raw = result[0]
        else:
            raw = result

        eta_raw = raw.get("eta")
        eta = None
        if eta_raw:
            eta = EtaInfo(
                etaFrom=eta_raw.get("etaFrom"),
                etaTo=eta_raw.get("etaTo"),
                lastUpdated=eta_raw.get("lastUpdated"),
            )

        last_event_raw = raw.get("lastEvent")
        last_event = None
        if last_event_raw:
            last_event = TrackingEvent(
                timestamp=last_event_raw.get("timestamp", ""),
                status=last_event_raw.get("status", ""),
                description=last_event_raw.get("description", ""),
                location=last_event_raw.get("location"),
                terminal=last_event_raw.get("terminal"),
            )

        status_resp = ShipmentStatusResponse(
            waybillNumber=waybill_number,
            status=_map_status(raw.get("status", "in_transit")),
            statusDescription=raw.get("statusDescription", ""),
            eta=eta,
            lastEvent=last_event,
        )
        return status_resp.model_dump(by_alias=True, mode="json"), 200

    async def get_eta(
        self,
        credentials: RabenCredentials,
        waybill_number: str,
    ) -> tuple[dict, int]:
        """Get ETA information for a shipment."""
        await self._ensure_token(credentials)
        result = await self._tracking.get_eta(waybill_number, credentials)
        if isinstance(result, tuple):
            return result
        return result, 200

    # -------------------------------------------------------------------
    # Label operations
    # -------------------------------------------------------------------

    async def get_label(
        self,
        credentials: RabenCredentials,
        waybill_number: str,
        label_format: str = "pdf",
    ) -> tuple[bytes | str, int]:
        """Get shipping label as PDF or ZPL."""
        await self._ensure_token(credentials)
        result = await self._labels.get_label(waybill_number, label_format, credentials)
        if isinstance(result, tuple):
            return result
        return result, 200

    # -------------------------------------------------------------------
    # Claims operations (myClaim)
    # -------------------------------------------------------------------

    async def create_claim(
        self,
        credentials: RabenCredentials,
        waybill_number: str,
        claim_type: ClaimType,
        description: str,
        contact_email: str,
        contact_phone: str | None = None,
    ) -> tuple[dict, int]:
        """Submit a complaint/claim via myClaim."""
        await self._ensure_token(credentials)

        claim_dto = CreateClaimRequest(
            waybillNumber=waybill_number,
            claimType=claim_type,
            description=description,
            contactEmail=contact_email,
            contactPhone=contact_phone,
        )

        result = await self._claims.create_claim(claim_dto, credentials)
        if isinstance(result, tuple):
            return result
        return result, 201

    # -------------------------------------------------------------------
    # PCD operations (Photo Confirming Delivery)
    # -------------------------------------------------------------------

    async def get_delivery_confirmation(
        self,
        credentials: RabenCredentials,
        waybill_number: str,
    ) -> tuple[dict, int]:
        """Get delivery confirmation with PCD photos."""
        await self._ensure_token(credentials)
        result = await self._pcd.get_delivery_confirmation(waybill_number, credentials)
        if isinstance(result, tuple):
            return result
        return result, 200
