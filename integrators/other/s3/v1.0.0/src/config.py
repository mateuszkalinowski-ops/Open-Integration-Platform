"""Configuration for S3 integrator — loaded from environment variables."""

from pydantic import Field
from pydantic_settings import BaseSettings


class S3AccountConfig(BaseSettings):
    """Single S3 account configuration."""

    name: str
    aws_access_key_id: str
    aws_secret_access_key: str
    region: str = "us-east-1"
    endpoint_url: str = ""
    default_bucket: str = ""
    use_path_style: bool = False
    environment: str = "production"

    polling_enabled: bool | None = None
    polling_bucket: str = ""
    polling_prefix: str = ""
    polling_interval_seconds: int | None = None


class Settings(BaseSettings):
    model_config = {"env_prefix": "S3_", "env_nested_delimiter": "__"}

    app_name: str = "s3-integrator"
    app_version: str = "1.0.0"
    debug: bool = False

    host: str = "0.0.0.0"
    port: int = 8000
    log_level: str = "INFO"

    database_url: str = Field(
        default="sqlite+aiosqlite:///./s3_integrator.db",
        alias="DATABASE_URL",
    )

    # Kafka
    kafka_enabled: bool = Field(default=False, alias="KAFKA_ENABLED")
    kafka_bootstrap_servers: str = Field(default="localhost:9092", alias="KAFKA_BOOTSTRAP_SERVERS")
    kafka_security_protocol: str = Field(default="PLAINTEXT", alias="KAFKA_SECURITY_PROTOCOL")
    kafka_sasl_mechanism: str = Field(default="PLAIN", alias="KAFKA_SASL_MECHANISM")
    kafka_sasl_username: str = Field(default="", alias="KAFKA_SASL_USERNAME")
    kafka_sasl_password: str = Field(default="", alias="KAFKA_SASL_PASSWORD")

    kafka_topic_object_new: str = "s3.output.other.objects.new"
    kafka_topic_object_uploaded: str = "s3.output.other.objects.uploaded"
    kafka_topic_object_deleted: str = "s3.output.other.objects.deleted"

    # Polling
    polling_enabled: bool = False
    polling_interval_seconds: int = 300
    polling_bucket: str = ""
    polling_prefix: str = ""

    # Connection
    connect_timeout: float = 15.0
    operation_timeout: float = 60.0
    max_retries: int = 3
    retry_backoff_factor: float = 1.0

    accounts_config_path: str = "/app/config/accounts.yaml"

    platform_api_url: str = Field(default="http://platform:8080", alias="PLATFORM_API_URL")
    platform_api_key: str = Field(default="", alias="PLATFORM_API_KEY")
    platform_internal_secret: str = Field(default="", alias="PLATFORM_INTERNAL_SECRET")
    platform_event_notify: bool = Field(default=True, alias="PLATFORM_EVENT_NOTIFY")


settings = Settings()
