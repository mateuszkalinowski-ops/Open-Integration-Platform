"""Shared application state for dependency injection."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class AppState:
    account_manager: Any = None
    health_checker: Any = None
    kafka_producer: Any = None


app_state = AppState()
