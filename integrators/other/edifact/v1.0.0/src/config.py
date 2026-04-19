"""Configuration for EDIFACT connector — loaded from environment variables."""

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = {"env_prefix": "EDIFACT_", "env_nested_delimiter": "__", "populate_by_name": True}

    app_name: str = "edifact-connector"
    app_version: str = "1.0.0"
    debug: bool = False

    host: str = "0.0.0.0"
    port: int = 8000
    log_level: str = "INFO"

    base_url: str = Field(
        default="http://localhost:9000",
        alias="EDIFACT_BASE_URL",
        description="Base URL of the external terminal/TOS/PCS system",
    )
    api_key: str = Field(default="", alias="EDIFACT_API_KEY")
    api_timeout_connect: float = Field(default=30.0, description="HTTP connect timeout in seconds")
    api_timeout_read: float = Field(default=60.0, description="HTTP read timeout in seconds")
    max_retries: int = Field(default=3, ge=0, le=10)

    kafka_enabled: bool = Field(default=False, alias="KAFKA_ENABLED")
    kafka_bootstrap_servers: str = Field(default="localhost:9092", alias="KAFKA_BOOTSTRAP_SERVERS")
    kafka_security_protocol: str = Field(default="PLAINTEXT", alias="KAFKA_SECURITY_PROTOCOL")
    kafka_sasl_mechanism: str = Field(default="PLAIN", alias="KAFKA_SASL_MECHANISM")
    kafka_sasl_username: str = Field(default="", alias="KAFKA_SASL_USERNAME")
    kafka_sasl_password: str = Field(default="", alias="KAFKA_SASL_PASSWORD")

    kafka_topic_codeco: str = "edifact.output.other.codeco.notify"
    kafka_topic_baplie: str = "edifact.output.other.baplie.notify"
    kafka_topic_iftmin: str = "edifact.output.other.iftmin.notify"

    accounts_config_path: str = "/app/config/accounts.yaml"

    platform_api_url: str = Field(default="http://platform:8080", alias="PLATFORM_API_URL")
    platform_api_key: str = Field(default="", alias="PLATFORM_API_KEY")
    platform_internal_secret: str = Field(default="", alias="PLATFORM_INTERNAL_SECRET")
    platform_event_notify: bool = Field(default=True, alias="PLATFORM_EVENT_NOTIFY")


settings = Settings()
