"""FastAPI dependency injection — provides shared services to route handlers."""

from pinquark_common.kafka import KafkaMessageProducer
from pinquark_common.monitoring.health import HealthChecker

from src.amazon.client import AmazonClient
from src.amazon.integration import AmazonIntegration
from src.amazon.scraper import AmazonScraper
from src.models.database import StateStore
from src.services.account_manager import AccountManager


class AppState:
    """Holds initialized service instances shared across the application."""

    def __init__(self) -> None:
        self.state_store: StateStore | None = None
        self.client: AmazonClient | None = None
        self.account_manager: AccountManager | None = None
        self.integration: AmazonIntegration | None = None
        self.scraper: AmazonScraper | None = None
        self.health_checker: HealthChecker | None = None
        self.kafka_producer: KafkaMessageProducer | None = None


app_state = AppState()
