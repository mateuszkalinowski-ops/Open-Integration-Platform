"""Decorators for declaring connector actions, triggers, and webhooks.

Each decorator stores metadata on the function via a `_connector_meta`
attribute so the ConnectorApp can discover them at init time.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ActionMeta:
    kind: str = "action"
    name: str = ""
    input_schema: dict[str, Any] | None = None
    output_schema: dict[str, Any] | None = None


@dataclass(frozen=True)
class TriggerMeta:
    kind: str = "trigger"
    name: str = ""
    interval_seconds: int = 60


@dataclass(frozen=True)
class WebhookMeta:
    kind: str = "webhook"
    name: str = ""
    topic: str | None = None
    signature_header: str | None = None
    signature_algorithm: str = "hmac-sha256"


type ConnectorMeta = ActionMeta | TriggerMeta | WebhookMeta


def action(
    name: str,
    *,
    input_schema: dict[str, Any] | None = None,
    output_schema: dict[str, Any] | None = None,
) -> Any:
    """Mark a method as a connector action handler.

    The platform dispatches action requests to the decorated method.
    The method receives the action payload dict and must return a result dict.
    """

    def decorator(fn: Any) -> Any:
        fn._connector_meta = ActionMeta(
            name=name,
            input_schema=input_schema,
            output_schema=output_schema,
        )
        return fn

    return decorator


def trigger(name: str, *, interval_seconds: int = 60) -> Any:
    """Mark a method as a polling trigger.

    The SDK will call this method on the given interval. The method should
    return a list of event dicts to emit, or an empty list.
    """

    def decorator(fn: Any) -> Any:
        fn._connector_meta = TriggerMeta(
            name=name,
            interval_seconds=interval_seconds,
        )
        return fn

    return decorator


def webhook(
    name: str,
    *,
    topic: str | None = None,
    signature_header: str | None = None,
    signature_algorithm: str = "hmac-sha256",
) -> Any:
    """Mark a method as a webhook handler.

    The SDK creates a POST endpoint at /webhooks/{name} and routes
    incoming webhook payloads to the decorated method.
    """

    def decorator(fn: Any) -> Any:
        fn._connector_meta = WebhookMeta(
            name=name,
            topic=topic,
            signature_header=signature_header,
            signature_algorithm=signature_algorithm,
        )
        return fn

    return decorator
