"""Configuration for Email Client integrator — loaded from environment variables."""

from pydantic import Field
from pydantic_settings import BaseSettings


class EmailAccountConfig(BaseSettings):
    """Single email account configuration.

    Populated at runtime from YAML config or environment variables.
    """

    name: str
    email_address: str
    username: str = ""
    password: str
    imap_host: str
    imap_port: int = 993
    smtp_host: str
    smtp_port: int = 587
    use_ssl: bool = True
    polling_folder: str = "INBOX"
    environment: str = "production"

    @property
    def login(self) -> str:
        """Username for IMAP/SMTP auth — falls back to email_address if not set."""
        return self.username or self.email_address


class Settings(BaseSettings):
    model_config = {"env_prefix": "EMAIL_", "env_nested_delimiter": "__"}

    app_name: str = "email-client-integrator"
    app_version: str = "1.0.0"
    debug: bool = False

    host: str = "0.0.0.0"
    port: int = 8000
    log_level: str = "INFO"

    database_url: str = Field(
        default="sqlite+aiosqlite:///./email_client_integrator.db",
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

    kafka_topic_emails_received: str = "email.output.other.emails.received"
    kafka_topic_emails_sent: str = "email.output.other.emails.sent"

    polling_enabled: bool = True
    polling_interval_seconds: int = 60
    polling_folder: str = "INBOX"
    polling_max_emails: int = 50

    imap_timeout: float = 30.0
    smtp_timeout: float = 30.0
    max_retries: int = 3
    retry_backoff_factor: float = 0.5

    max_attachment_size_mb: int = 25

    accounts_config_path: str = "/app/config/accounts.yaml"

    platform_api_url: str = Field(default="http://platform:8080", alias="PLATFORM_API_URL")
    platform_api_key: str = Field(default="", alias="PLATFORM_API_KEY")
    platform_internal_secret: str = Field(default="", alias="PLATFORM_INTERNAL_SECRET")
    platform_event_notify: bool = Field(default=True, alias="PLATFORM_EVENT_NOTIFY")


settings = Settings()
