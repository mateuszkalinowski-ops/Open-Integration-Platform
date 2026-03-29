"""Shared application state for dependency injection."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from src.services.account_manager import AccountManager

    from pinquark_common.monitoring.health import HealthChecker


@dataclass
class AppState:
    account_manager: Any = None
    health_checker: Any = None
    kafka_producer: Any = None


app_state = AppState()
