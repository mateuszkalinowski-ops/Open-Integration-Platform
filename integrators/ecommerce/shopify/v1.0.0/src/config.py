"""Configuration for Shopify integrator — loaded from environment variables."""

from pydantic import Field
from pydantic_settings import BaseSettings


class ShopifyAccountConfig(BaseSettings):
    """Single Shopify store configuration.

    Populated at runtime from YAML config or environment variables.
    """

    name: str
    shop_url: str
    access_token: str
    api_version: str = "2024-07"
    default_location_id: str = ""
    default_carrier: str = "Kurier"


class Settings(BaseSettings):
    model_config = {"env_prefix": "SHOPIFY_", "env_nested_delimiter": "__"}

    app_name: str = "shopify-integrator"
    app_version: str = "1.0.0"
    debug: bool = False

    host: str = "0.0.0.0"
    port: int = 8000
    log_level: str = "INFO"

    # Database (async SQLite for token/state persistence)
    database_url: str = Field(
        default="sqlite+aiosqlite:///./shopify_integrator.db",
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
    kafka_consumer_group: str = Field(default="shopify_integrator", alias="KAFKA_CONSUMER_GROUP")

    # Kafka topics
    kafka_topic_orders_out: str = "shopify.output.ecommerce.orders.save"
    kafka_topic_orders_in: str = "shopify.input.ecommerce.orders.status"
    kafka_topic_stock_in: str = "shopify.input.ecommerce.stock.sync"

    # Shopify scraping
    scraping_enabled: bool = True
    scraping_interval_seconds: int = 60

    # Shopify defaults
    default_api_version: str = "2024-07"
    default_carrier: str = "Kurier"
    default_order_type: str = "WZ"
    default_product_unit: str = "szt."
    default_warehouse_symbol: str = "ZAM"
    guest_customer_erp_id: str = "0"

    # Accounts loaded from YAML config file
    accounts_config_path: str = "/app/config/accounts.yaml"

    # WMS callback
    wms_callback_url: str = Field(default="", alias="WMS_CALLBACK_URL")
    wms_callback_token: str = Field(default="", alias="WMS_CALLBACK_TOKEN")

    # Timeouts
    http_connect_timeout: float = 30.0
    http_read_timeout: float = 60.0

    # Retry
    max_retries: int = 3
    retry_backoff_factor: float = 0.5


settings = Settings()
