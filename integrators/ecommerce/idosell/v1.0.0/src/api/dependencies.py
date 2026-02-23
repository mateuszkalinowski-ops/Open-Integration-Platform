"""FastAPI dependency injection — provides shared services to route handlers."""

from src.models.database import StateStore
from src.services.account_manager import AccountManager
from src.idosell.client import IdoSellClient
from src.idosell.integration import IdoSellIntegration
from src.idosell.scraper import OrderScraper
from pinquark_common.monitoring.health import HealthChecker
from pinquark_common.kafka import KafkaMessageProducer


class AppState:
    """Holds initialized service instances shared across the application."""

    def __init__(self) -> None:
        self.state_store: StateStore | None = None
        self.client: IdoSellClient | None = None
        self.account_manager: AccountManager | None = None
        self.integration: IdoSellIntegration | None = None
        self.scraper: OrderScraper | None = None
        self.health_checker: HealthChecker | None = None
        self.kafka_producer: KafkaMessageProducer | None = None


app_state = AppState()
