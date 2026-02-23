"""Configuration for Allegro integrator — loaded from environment variables."""

from pydantic import Field
from pydantic_settings import BaseSettings


class AllegroAccountConfig(BaseSettings):
    """Single Allegro account configuration.

    Populated at runtime from YAML config or environment variables.
    """
    name: str
    client_id: str
    client_secret: str
    api_url: str = "https://api.allegro.pl"
    auth_url: str = "https://allegro.pl/auth/oauth"
    environment: str = "production"


class Settings(BaseSettings):
    model_config = {"env_prefix": "ALLEGRO_", "env_nested_delimiter": "__"}

    app_name: str = "allegro-integrator"
    app_version: str = "1.0.0"
    debug: bool = False

    host: str = "0.0.0.0"
    port: int = 8000
    log_level: str = "INFO"

    # Database (async PostgreSQL for token/state persistence)
    database_url: str = Field(
        default="sqlite+aiosqlite:///./allegro_integrator.db",
        alias="DATABASE_URL",
    )
    encryption_key: str = Field(
        default="",
        alias="DATABASE_ENCRYPTION_KEY",
        description="Base64-encoded 32-byte AES key for credential encryption",
    )

    # Kafka
    kafka_enabled: bool = Field(default=False, alias="KAFKA_ENABLED")
    kafka_bootstrap_servers: str = Field(default="localhost:9092", alias="KAFKA_BOOTSTRAP_SERVERS")
    kafka_security_protocol: str = Field(default="PLAINTEXT", alias="KAFKA_SECURITY_PROTOCOL")
    kafka_sasl_mechanism: str = Field(default="PLAIN", alias="KAFKA_SASL_MECHANISM")
    kafka_sasl_username: str = Field(default="", alias="KAFKA_SASL_USERNAME")
    kafka_sasl_password: str = Field(default="", alias="KAFKA_SASL_PASSWORD")
    kafka_consumer_group: str = Field(default="allegro_integrator", alias="KAFKA_CONSUMER_GROUP")

    # Kafka topics
    kafka_topic_orders_out: str = "output.ecommerce.orders.save"
    kafka_topic_orders_in: str = "input.ecommerce.orders.status"
    kafka_topic_stock_in: str = "input.ecommerce.stock.sync"

    # Allegro scraping
    scraping_enabled: bool = True
    scraping_interval_seconds: int = 60

    # Allegro defaults
    default_carrier: str = "Kurier"
    default_order_type: str = "WZ"
    default_product_unit: str = "szt."
    default_warehouse_symbol: str = "ZAM"
    guest_customer_erp_id: str = "1"

    # Accounts loaded from YAML config file
    accounts_config_path: str = "/app/config/accounts.yaml"

    # WMS callback (CRT)
    wms_callback_url: str = Field(default="", alias="WMS_CALLBACK_URL")
    wms_callback_token: str = Field(default="", alias="WMS_CALLBACK_TOKEN")

    # Timeouts
    http_connect_timeout: float = 30.0
    http_read_timeout: float = 60.0

    # Retry
    max_retries: int = 3
    retry_backoff_factor: float = 0.5


settings = Settings()
