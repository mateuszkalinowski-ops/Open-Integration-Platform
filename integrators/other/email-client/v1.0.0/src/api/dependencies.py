"""FastAPI dependency injection — provides shared services to route handlers."""

from pinquark_common.kafka import KafkaMessageProducer
from pinquark_common.monitoring.health import HealthChecker

from src.email_client.integration import EmailIntegration
from src.email_client.poller import EmailPoller
from src.models.database import StateStore
from src.services.account_manager import AccountManager


class AppState:
    """Holds initialized service instances shared across the application."""

    def __init__(self) -> None:
        self.state_store: StateStore | None = None
        self.account_manager: AccountManager | None = None
        self.integration: EmailIntegration | None = None
        self.poller: EmailPoller | None = None
        self.health_checker: HealthChecker | None = None
        self.kafka_producer: KafkaMessageProducer | None = None


app_state = AppState()
