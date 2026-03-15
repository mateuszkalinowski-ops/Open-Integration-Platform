"""FastAPI dependency injection — provides shared services to route handlers."""

from pinquark_common.kafka import KafkaMessageProducer
from pinquark_common.monitoring.health import HealthChecker

from src.models.database import StateStore
from src.services.account_manager import AccountManager
from src.woocommerce.auth import WooCommerceAuth
from src.woocommerce.client import WooCommerceClient
from src.woocommerce.integration import WooCommerceIntegration
from src.woocommerce.scraper import OrderScraper


class AppState:
    """Holds initialized service instances shared across the application."""

    def __init__(self) -> None:
        self.state_store: StateStore | None = None
        self.auth: WooCommerceAuth | None = None
        self.client: WooCommerceClient | None = None
        self.account_manager: AccountManager | None = None
        self.integration: WooCommerceIntegration | None = None
        self.scraper: OrderScraper | None = None
        self.health_checker: HealthChecker | None = None
        self.kafka_producer: KafkaMessageProducer | None = None


app_state = AppState()
