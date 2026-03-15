"""FastAPI dependency injection — provides shared services to route handlers."""

from pinquark_common.kafka import KafkaMessageProducer
from pinquark_common.monitoring.health import HealthChecker

from src.models.database import StateStore
from src.services.account_manager import AccountManager
from src.shoper.auth import ShoperAuthManager
from src.shoper.client import ShoperClient
from src.shoper.integration import ShoperIntegration
from src.shoper.scraper import ShoperScraper


class AppState:
    """Holds initialized service instances shared across the application."""

    def __init__(self) -> None:
        self.state_store: StateStore | None = None
        self.auth_manager: ShoperAuthManager | None = None
        self.client: ShoperClient | None = None
        self.account_manager: AccountManager | None = None
        self.integration: ShoperIntegration | None = None
        self.scraper: ShoperScraper | None = None
        self.health_checker: HealthChecker | None = None
        self.kafka_producer: KafkaMessageProducer | None = None


app_state = AppState()
