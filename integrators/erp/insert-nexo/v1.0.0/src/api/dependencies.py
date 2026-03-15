"""FastAPI dependency injection for the cloud connector."""

from pinquark_common.monitoring.health import HealthChecker

from src.services.account_manager import AccountManager


class AppState:
    def __init__(self) -> None:
        self.account_manager: AccountManager | None = None
        self.health_checker: HealthChecker | None = None


app_state = AppState()
