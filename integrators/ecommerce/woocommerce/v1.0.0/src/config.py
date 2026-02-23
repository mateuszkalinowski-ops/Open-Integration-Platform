"""Configuration for WooCommerce integrator — loaded from environment variables."""

from pydantic import Field
from pydantic_settings import BaseSettings


class WooCommerceAccountConfig(BaseSettings):
    """Single WooCommerce store configuration.

    Populated at runtime from YAML config or environment variables.
    """

    name: str
    store_url: str
    consumer_key: str
    consumer_secret: str
    api_version: str = "wc/v3"
    verify_ssl: bool = True
    environment: str = "production"


class Settings(BaseSettings):
    model_config = {"env_prefix": "WOOCOMMERCE_", "env_nested_delimiter": "__"}

    app_name: str = "woocommerce-integrator"
    app_version: str = "1.0.0"
    debug: bool = False

    host: str = "0.0.0.0"
    port: int = 8000
    log_level: str = "INFO"

    # Database (async SQLite for state persistence)
    database_url: str = Field(
        default="sqlite+aiosqlite:///./woocommerce_integrator.db",
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
    kafka_consumer_group: str = Field(default="woocommerce_integrator", alias="KAFKA_CONSUMER_GROUP")

    # Kafka topics
    kafka_topic_orders_out: str = "output.ecommerce.orders.save"
    kafka_topic_products_out: str = "output.ecommerce.products.save"
    kafka_topic_orders_in: str = "input.ecommerce.orders.status"
    kafka_topic_stock_in: str = "input.ecommerce.stock.sync"

    # WooCommerce scraping
    scraping_enabled: bool = True
    scraping_interval_seconds: int = 60
    scraping_orders_enabled: bool = True
    scraping_products_enabled: bool = True

    # WooCommerce defaults
    default_carrier: str = "Kurier"
    default_order_type: str = "WZ"
    default_product_unit: str = "szt."
    default_warehouse_symbol: str = "ZAM"
    default_per_page: int = 100

    # Accounts loaded from YAML config file
    accounts_config_path: str = "/app/config/accounts.yaml"

    # Timeouts
    http_connect_timeout: float = 30.0
    http_read_timeout: float = 60.0

    # Retry
    max_retries: int = 3
    retry_backoff_factor: float = 0.5


settings = Settings()
