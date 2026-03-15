"""FastAPI dependency injection — provides shared services to route handlers."""

from pinquark_common.kafka import KafkaMessageProducer
from pinquark_common.monitoring.health import HealthChecker

from src.models.database import StateStore
from src.services.account_manager import AccountManager
from src.slack_client.integration import SlackIntegration
from src.slack_client.poller import MessagePoller


class AppState:
    """Holds initialized service instances shared across the application."""

    def __init__(self) -> None:
        self.state_store: StateStore | None = None
        self.account_manager: AccountManager | None = None
        self.integration: SlackIntegration | None = None
        self.poller: MessagePoller | None = None
        self.health_checker: HealthChecker | None = None
        self.kafka_producer: KafkaMessageProducer | None = None


app_state = AppState()
