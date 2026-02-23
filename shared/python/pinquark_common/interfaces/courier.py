"""Base interface for all courier integrations.

Every courier integrator MUST implement the abstract methods.
Optional methods have default implementations that raise NotImplementedError.
"""

from abc import ABC, abstractmethod

from pinquark_common.schemas.courier import (
    CreateShipmentCommand,
    PickupPoint,
    ShipmentResponse,
    ShipmentStatus,
    ShipmentStatusUpdate,
)


class CourierIntegration(ABC):

    @abstractmethod
    async def create_shipment(
        self,
        command: CreateShipmentCommand,
    ) -> ShipmentResponse:
        """Create a shipment with the courier."""
        ...

    @abstractmethod
    async def get_label(
        self,
        waybill_number: str,
        label_format: str = "PDF",
    ) -> bytes:
        """Retrieve the shipment label as bytes (PDF)."""
        ...

    @abstractmethod
    async def get_shipment_status(
        self,
        waybill_number: str,
    ) -> ShipmentStatusUpdate:
        """Get current shipment status."""
        ...

    async def cancel_shipment(
        self,
        waybill_number: str,
    ) -> bool:
        """Cancel an existing shipment. Returns True on success."""
        raise NotImplementedError("cancel_shipment not supported")

    async def get_tracking_url(
        self,
        waybill_number: str,
    ) -> str:
        """Get the public tracking URL for a shipment."""
        raise NotImplementedError("get_tracking_url not supported")

    async def get_pickup_points(
        self,
        city: str = "",
        postal_code: str = "",
        country_code: str = "PL",
        **filters: object,
    ) -> list[PickupPoint]:
        """Search for pickup/drop-off points."""
        raise NotImplementedError("get_pickup_points not supported")

    async def generate_protocol(
        self,
        waybill_numbers: list[str],
    ) -> bytes:
        """Generate a pickup protocol (PDF) for given waybill numbers."""
        raise NotImplementedError("generate_protocol not supported")

    async def get_shipment(
        self,
        waybill_number: str,
    ) -> dict:
        """Get full shipment details."""
        raise NotImplementedError("get_shipment not supported")

    def map_status(self, raw_status: str) -> ShipmentStatus:
        """Map courier-specific status string to normalized ShipmentStatus."""
        mapping: dict[str, ShipmentStatus] = {}
        return mapping.get(raw_status, ShipmentStatus.CREATED)
