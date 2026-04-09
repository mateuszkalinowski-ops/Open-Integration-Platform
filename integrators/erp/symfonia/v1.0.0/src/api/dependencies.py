"""FastAPI dependency injection for the Symfonia ERP connector."""

from pinquark_common.monitoring.health import HealthChecker

from src.services.symfonia_client import SymfoniaClient


class AppState:
    def __init__(self) -> None:
        self.symfonia_client: SymfoniaClient | None = None
        self.health_checker: HealthChecker | None = None


app_state = AppState()
