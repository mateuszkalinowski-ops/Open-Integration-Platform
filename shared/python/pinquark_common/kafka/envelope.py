"""Standard Kafka event envelope for connector-to-platform communication.

Every connector wraps Kafka messages in this envelope so the platform's
Kafka Event Bridge can route them to the correct workflow / flow engine.
"""

from datetime import datetime, timezone
from typing import Any


def wrap_event(
    connector_name: str,
    event: str,
    data: dict[str, Any],
    account_name: str = "",
) -> dict[str, Any]:
    """Wrap payload in a standard event envelope.

    Parameters
    ----------
    connector_name:
        Connector identifier matching ``connector.yaml`` ``name`` field.
    event:
        Dot-separated event name, e.g. ``order.ready_for_processing``.
    data:
        Arbitrary event payload (serialisable to JSON).
    account_name:
        Optional account name for multi-account connectors.
    """
    return {
        "connector_name": connector_name,
        "event": event,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "account_name": account_name,
        "data": data,
    }
