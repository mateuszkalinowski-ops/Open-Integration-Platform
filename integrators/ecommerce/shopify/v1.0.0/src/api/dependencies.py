"""FastAPI dependency injection — provides shared services to route handlers."""

from pinquark_common.kafka import KafkaMessageProducer
from pinquark_common.monitoring.health import HealthChecker

from src.models.database import TokenStore
from src.services.account_manager import AccountManager
from src.shopify.auth import ShopifyAuthManager
from src.shopify.client import ShopifyClient
from src.shopify.integration import ShopifyIntegration
from src.shopify.scraper import OrderScraper


class AppState:
    """Holds initialized service instances shared across the application."""

    def __init__(self) -> None:
        self.token_store: TokenStore | None = None
        self.auth_manager: ShopifyAuthManager | None = None
        self.client: ShopifyClient | None = None
        self.account_manager: AccountManager | None = None
        self.integration: ShopifyIntegration | None = None
        self.scraper: OrderScraper | None = None
        self.health_checker: HealthChecker | None = None
        self.kafka_producer: KafkaMessageProducer | None = None


app_state = AppState()
