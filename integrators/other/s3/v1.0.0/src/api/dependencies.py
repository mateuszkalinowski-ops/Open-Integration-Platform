"""FastAPI dependency injection — provides shared services to route handlers."""

from src.s3_client.integration import S3Integration
from src.s3_client.poller import ObjectPoller
from src.models.database import StateStore
from src.services.account_manager import AccountManager
from pinquark_common.monitoring.health import HealthChecker
from pinquark_common.kafka import KafkaMessageProducer


class AppState:
    """Holds initialized service instances shared across the application."""

    def __init__(self) -> None:
        self.state_store: StateStore | None = None
        self.account_manager: AccountManager | None = None
        self.integration: S3Integration | None = None
        self.poller: ObjectPoller | None = None
        self.health_checker: HealthChecker | None = None
        self.kafka_producer: KafkaMessageProducer | None = None


app_state = AppState()
