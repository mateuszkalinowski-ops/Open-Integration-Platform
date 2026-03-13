"""Configuration for the Pinquark WMS connector."""

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    api_url: str = "http://localhost:8090"
    username: str = ""
    password: str = ""

    http_connect_timeout: float = 10.0
    http_read_timeout: float = 30.0

    feedback_poll_interval: float = 2.0
    feedback_poll_max_attempts: int = 15
    feedback_poll_backoff: float = 1.3

    event_polling_enabled: bool = True
    event_polling_interval_seconds: int = 120
    event_polling_initial_delay: int = 15

    platform_api_url: str = "http://platform:8080"
    platform_internal_secret: str = ""
    platform_event_notify: bool = True

    kafka_enabled: bool = Field(default=False, alias="KAFKA_ENABLED")
    kafka_bootstrap_servers: str = Field(default="kafka:9092", alias="KAFKA_BOOTSTRAP_SERVERS")
    kafka_security_protocol: str = Field(default="PLAINTEXT", alias="KAFKA_SECURITY_PROTOCOL")
    kafka_topic_documents: str = "wms.output.wms.documents.synced"
    kafka_topic_articles: str = "wms.output.wms.articles.synced"
    kafka_topic_contractors: str = "wms.output.wms.contractors.synced"
    kafka_topic_positions: str = "wms.output.wms.positions.synced"
    kafka_topic_feedbacks: str = "wms.output.wms.feedbacks.received"

    log_level: str = "INFO"

    model_config = {"env_prefix": "PINQUARK_WMS_"}


settings = Settings()
