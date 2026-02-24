"""Configuration for FTP/SFTP integrator — loaded from environment variables."""

from pydantic import Field
from pydantic_settings import BaseSettings


class FtpAccountConfig(BaseSettings):
    """Single FTP/SFTP server configuration."""

    name: str
    host: str
    protocol: str = "sftp"
    port: int = 0
    username: str = ""
    password: str = ""
    private_key: str = ""
    passive_mode: bool = True
    base_path: str = "/"
    environment: str = "production"

    @property
    def effective_port(self) -> int:
        if self.port > 0:
            return self.port
        return 22 if self.protocol == "sftp" else 21


class Settings(BaseSettings):
    model_config = {"env_prefix": "FTP_", "env_nested_delimiter": "__"}

    app_name: str = "ftp-sftp-integrator"
    app_version: str = "1.0.0"
    debug: bool = False

    host: str = "0.0.0.0"
    port: int = 8000
    log_level: str = "INFO"

    database_url: str = Field(
        default="sqlite+aiosqlite:///./ftp_sftp_integrator.db",
        alias="DATABASE_URL",
    )

    # Kafka
    kafka_enabled: bool = Field(default=False, alias="KAFKA_ENABLED")
    kafka_bootstrap_servers: str = Field(default="localhost:9092", alias="KAFKA_BOOTSTRAP_SERVERS")
    kafka_security_protocol: str = Field(default="PLAINTEXT", alias="KAFKA_SECURITY_PROTOCOL")
    kafka_sasl_mechanism: str = Field(default="PLAIN", alias="KAFKA_SASL_MECHANISM")
    kafka_sasl_username: str = Field(default="", alias="KAFKA_SASL_USERNAME")
    kafka_sasl_password: str = Field(default="", alias="KAFKA_SASL_PASSWORD")

    kafka_topic_file_new: str = "ftp-sftp.output.other.files.new"
    kafka_topic_file_uploaded: str = "ftp-sftp.output.other.files.uploaded"
    kafka_topic_file_deleted: str = "ftp-sftp.output.other.files.deleted"

    # Polling
    polling_enabled: bool = False
    polling_interval_seconds: int = 300
    polling_path: str = "/"

    # Connection
    connect_timeout: float = 15.0
    operation_timeout: float = 60.0
    max_retries: int = 3
    retry_backoff_factor: float = 1.0

    accounts_config_path: str = "/app/config/accounts.yaml"

    platform_api_url: str = Field(default="http://platform:8080", alias="PLATFORM_API_URL")
    platform_api_key: str = Field(default="", alias="PLATFORM_API_KEY")
    platform_event_notify: bool = Field(default=True, alias="PLATFORM_EVENT_NOTIFY")


settings = Settings()
