"""Configuration for Slack integrator — loaded from environment variables."""

from pydantic import Field
from pydantic_settings import BaseSettings


class SlackAccountConfig(BaseSettings):
    """Single Slack workspace/bot configuration."""

    name: str
    bot_token: str
    app_token: str = ""
    default_channel: str = "general"
    environment: str = "production"


class Settings(BaseSettings):
    model_config = {"env_prefix": "SLACK_", "env_nested_delimiter": "__"}

    app_name: str = "slack-integrator"
    app_version: str = "1.0.0"
    debug: bool = False

    host: str = "0.0.0.0"
    port: int = 8000
    log_level: str = "INFO"

    database_url: str = Field(
        default="sqlite+aiosqlite:///./slack_integrator.db",
        alias="DATABASE_URL",
    )
    encryption_key: str = Field(default="", alias="DATABASE_ENCRYPTION_KEY")

    # Kafka
    kafka_enabled: bool = Field(default=False, alias="KAFKA_ENABLED")
    kafka_bootstrap_servers: str = Field(default="localhost:9092", alias="KAFKA_BOOTSTRAP_SERVERS")
    kafka_security_protocol: str = Field(default="PLAINTEXT", alias="KAFKA_SECURITY_PROTOCOL")
    kafka_sasl_mechanism: str = Field(default="PLAIN", alias="KAFKA_SASL_MECHANISM")
    kafka_sasl_username: str = Field(default="", alias="KAFKA_SASL_USERNAME")
    kafka_sasl_password: str = Field(default="", alias="KAFKA_SASL_PASSWORD")

    kafka_topic_messages_received: str = "slack.output.other.messages.received"
    kafka_topic_messages_sent: str = "slack.output.other.messages.sent"

    # Polling
    polling_enabled: bool = True
    polling_interval_seconds: int = 30

    # Timeouts
    http_connect_timeout: float = 10.0
    http_read_timeout: float = 30.0
    max_retries: int = 3
    retry_backoff_factor: float = 0.5

    accounts_config_path: str = "/app/config/accounts.yaml"

    platform_api_url: str = Field(default="http://platform:8080", alias="PLATFORM_API_URL")
    platform_api_key: str = Field(default="", alias="PLATFORM_API_KEY")
    platform_event_notify: bool = Field(default=True, alias="PLATFORM_EVENT_NOTIFY")


settings = Settings()
