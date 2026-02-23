"""Unified Connector Interface for the any-to-any integration platform.

Every connector is an equal peer that can act as both:
- Source: emits events (e.g., order.created, shipment.status_changed)
- Destination: receives actions (e.g., shipment.create, stock.sync)

Category-specific interfaces (CourierIntegration, EcommerceIntegration) remain
as specialized subclasses. This base provides the event/action contract that
the Flow Engine uses for any-to-any routing.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Callable, Coroutine


EventCallback = Callable[[str, dict[str, Any]], Coroutine[Any, Any, None]]


@dataclass
class EventDescriptor:
    name: str
    description: str = ""
    payload_schema: dict[str, Any] = field(default_factory=dict)


@dataclass
class ActionDescriptor:
    name: str
    description: str = ""
    payload_schema: dict[str, Any] = field(default_factory=dict)
    response_schema: dict[str, Any] = field(default_factory=dict)


@dataclass
class ActionResult:
    success: bool
    data: dict[str, Any] = field(default_factory=dict)
    error: str | None = None


class Connector(ABC):
    """Base interface for all connectors in the integration platform.

    Every system (courier, e-commerce, ERP, WMS, etc.) implements this
    interface. The Flow Engine uses get_supported_events() and
    get_supported_actions() to know what connections are possible.
    """

    @abstractmethod
    def get_connector_name(self) -> str:
        """Unique connector identifier (e.g., 'inpost', 'allegro')."""
        ...

    @abstractmethod
    def get_connector_version(self) -> str:
        """Connector version (semver, e.g., '3.0.0')."""
        ...

    @abstractmethod
    def get_supported_events(self) -> list[EventDescriptor]:
        """Events this connector can emit (source role).

        Examples:
            - EventDescriptor("order.created", "New order placed")
            - EventDescriptor("shipment.status_changed", "Shipment status update")
        """
        ...

    @abstractmethod
    def get_supported_actions(self) -> list[ActionDescriptor]:
        """Actions this connector can execute (destination role).

        Examples:
            - ActionDescriptor("shipment.create", "Create a new shipment")
            - ActionDescriptor("stock.sync", "Synchronize stock levels")
        """
        ...

    async def execute_action(self, action: str, payload: dict[str, Any]) -> ActionResult:
        """Execute an action on this connector.

        The Flow Engine calls this when a flow routes an event to this
        connector. Override to handle specific actions.
        """
        raise NotImplementedError(f"Action '{action}' not supported by {self.get_connector_name()}")

    async def subscribe_events(self, callback: EventCallback) -> None:
        """Subscribe to events from this connector.

        The platform calls this to register a callback that receives events.
        Implementations may use webhooks, polling, or push mechanisms.
        """
        raise NotImplementedError(f"Event subscription not supported by {self.get_connector_name()}")

    async def health_check(self) -> dict[str, Any]:
        """Check connector health and connectivity."""
        return {"status": "ok", "connector": self.get_connector_name()}
