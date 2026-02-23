"""FastAPI dependency injection — provides shared services to route handlers."""

from src.allegro.auth import AllegroAuthManager
from src.allegro.client import AllegroClient
from src.allegro.integration import AllegroIntegration
from src.allegro.scraper import OrderScraper
from src.models.database import TokenStore
from src.services.account_manager import AccountManager
from pinquark_common.monitoring.health import HealthChecker
from pinquark_common.kafka import KafkaMessageProducer


class AppState:
    """Holds initialized service instances shared across the application."""

    def __init__(self):
        self.token_store: TokenStore | None = None
        self.auth_manager: AllegroAuthManager | None = None
        self.client: AllegroClient | None = None
        self.account_manager: AccountManager | None = None
        self.integration: AllegroIntegration | None = None
        self.scraper: OrderScraper | None = None
        self.health_checker: HealthChecker | None = None
        self.kafka_producer: KafkaMessageProducer | None = None


app_state = AppState()
