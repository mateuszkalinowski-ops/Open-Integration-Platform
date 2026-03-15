"""FastAPI dependency injection — provides shared services to route handlers."""

from pinquark_common.kafka import KafkaMessageProducer
from pinquark_common.monitoring.health import HealthChecker

from src.baselinker.client import BaseLinkerClient
from src.baselinker.integration import BaseLinkerIntegration
from src.baselinker.scraper import BaseLinkerScraper
from src.models.database import StateStore
from src.services.account_manager import AccountManager


class AppState:
    """Holds initialized service instances shared across the application."""

    def __init__(self) -> None:
        self.state_store: StateStore | None = None
        self.client: BaseLinkerClient | None = None
        self.account_manager: AccountManager | None = None
        self.integration: BaseLinkerIntegration | None = None
        self.scraper: BaseLinkerScraper | None = None
        self.health_checker: HealthChecker | None = None
        self.kafka_producer: KafkaMessageProducer | None = None


app_state = AppState()
