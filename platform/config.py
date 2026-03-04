from pydantic import Field
from pydantic_settings import BaseSettings

KAFKA_DEFAULT_TOPICS: list[str] = [
    "allegro.output.ecommerce.orders.save",
    "baselinker.output.ecommerce.orders.save",
    "shopify.output.ecommerce.orders.save",
    "email.output.other.emails.received",
    "skanujfakture.output.other.documents.scanned",
    "ftp-sftp.output.other.files.new",
    "slack.output.other.messages.received",
    "wms.output.wms.documents.synced",
    "wms.output.wms.articles.synced",
    "wms.output.wms.contractors.synced",
]


class Settings(BaseSettings):
    app_env: str = "development"
    app_port: int = 8080
    log_level: str = "INFO"

    # PostgreSQL
    database_url: str = "postgresql+asyncpg://pinquark:pinquark@localhost:5432/pinquark_platform"
    db_pool_size: int = 20
    db_max_overflow: int = 30
    db_pool_timeout: int = 30
    db_pool_recycle: int = 1800

    # Redis
    redis_url: str = "redis://localhost:6379/0"
    redis_max_connections: int = 50
    redis_socket_timeout: float = 5.0
    redis_cache_ttl: int = 300

    # Rate limiting (per-tenant, requests per window)
    rate_limit_requests: int = 1000
    rate_limit_window_seconds: int = 60

    encryption_key: str = ""
    jwt_secret_key: str = ""
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30

    connector_discovery_path: str = "../integrators"

    demo_mode: bool = False

    # Kafka
    kafka_enabled: bool = Field(default=False, alias="KAFKA_ENABLED")
    kafka_bootstrap_servers: str = Field(
        default="kafka:9092", alias="KAFKA_BOOTSTRAP_SERVERS"
    )
    kafka_security_protocol: str = Field(
        default="PLAINTEXT", alias="KAFKA_SECURITY_PROTOCOL"
    )
    kafka_consumer_group: str = Field(
        default="platform-event-bridge", alias="KAFKA_CONSUMER_GROUP"
    )
    kafka_event_topics: list[str] = Field(default_factory=lambda: list(KAFKA_DEFAULT_TOPICS))

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
