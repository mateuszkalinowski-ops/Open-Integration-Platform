"""Configuration for SkanujFakture integrator — loaded from environment variables."""

from pydantic import Field
from pydantic_settings import BaseSettings


class SkanujFaktureAccountConfig(BaseSettings):
    """Single SkanujFakture account configuration.

    Populated at runtime from YAML config or environment variables.
    """

    name: str
    login: str
    password: str
    api_url: str = ""
    company_id: int | None = None
    environment: str = "production"


class Settings(BaseSettings):
    model_config = {"env_prefix": "SF_", "env_nested_delimiter": "__", "populate_by_name": True}

    app_name: str = "skanuj-fakture-integrator"
    app_version: str = "1.0.0"
    debug: bool = False

    host: str = "0.0.0.0"
    port: int = 8000
    log_level: str = "INFO"

    database_url: str = Field(
        default="sqlite+aiosqlite:///./skanuj_fakture_integrator.db",
        alias="DATABASE_URL",
    )
    encryption_key: str = Field(
        default="",
        alias="DATABASE_ENCRYPTION_KEY",
    )

    kafka_enabled: bool = Field(default=False, alias="KAFKA_ENABLED")
    kafka_bootstrap_servers: str = Field(default="localhost:9092", alias="KAFKA_BOOTSTRAP_SERVERS")
    kafka_security_protocol: str = Field(default="PLAINTEXT", alias="KAFKA_SECURITY_PROTOCOL")
    kafka_sasl_mechanism: str = Field(default="PLAIN", alias="KAFKA_SASL_MECHANISM")
    kafka_sasl_username: str = Field(default="", alias="KAFKA_SASL_USERNAME")
    kafka_sasl_password: str = Field(default="", alias="KAFKA_SASL_PASSWORD")

    kafka_topic_documents_scanned: str = "skanujfakture.output.other.documents.scanned"
    kafka_topic_documents_uploaded: str = "skanujfakture.output.other.documents.uploaded"

    polling_enabled: bool = Field(default=True, alias="POLLING_ENABLED")
    polling_interval_seconds: int = Field(default=300, alias="POLLING_INTERVAL_SECONDS")
    polling_status_filter: str = Field(default="zeskanowany", alias="POLLING_STATUS_FILTER")

    api_timeout: float = 60.0
    max_retries: int = 3
    retry_backoff_factor: float = 0.5
    max_upload_size_mb: int = 25

    accounts_config_path: str = "/app/config/accounts.yaml"

    platform_api_url: str = Field(default="http://platform:8080", alias="PLATFORM_API_URL")
    platform_api_key: str = Field(default="", alias="PLATFORM_API_KEY")
    platform_internal_secret: str = Field(default="", alias="PLATFORM_INTERNAL_SECRET")
    platform_event_notify: bool = Field(default=True, alias="PLATFORM_EVENT_NOTIFY")


settings = Settings()
