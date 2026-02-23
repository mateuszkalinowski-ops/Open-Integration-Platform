"""Configuration for Shoper integrator — loaded from environment variables."""

from pydantic import Field
from pydantic_settings import BaseSettings


class ShoperAccountConfig(BaseSettings):
    """Single Shoper account configuration.

    Populated at runtime from YAML config or environment variables.
    """

    name: str
    shop_url: str
    login: str
    password: str
    language_id: str = "pl_PL"
    environment: str = "production"


class Settings(BaseSettings):
    model_config = {"env_prefix": "SHOPER_", "env_nested_delimiter": "__"}

    app_name: str = "shoper-integrator"
    app_version: str = "1.0.0"
    debug: bool = False

    host: str = "0.0.0.0"
    port: int = 8000
    log_level: str = "INFO"

    database_url: str = Field(
        default="sqlite+aiosqlite:///./shoper_integrator.db",
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

    kafka_topic_orders_out: str = "shoper.output.ecommerce.orders.save"
    kafka_topic_products_out: str = "shoper.output.ecommerce.products.save"
    kafka_topic_users_out: str = "shoper.output.ecommerce.users.save"

    scraping_enabled: bool = True
    scraping_interval_seconds: int = 300

    scrape_orders: bool = True
    scrape_products: bool = True
    scrape_users: bool = True

    default_unit: str = "szt."
    default_order_type: str = "WZ"
    default_warehouse_symbol: str = "ZAM"
    default_position_status: str = "OCZEKUJE"

    accounts_config_path: str = "/app/config/accounts.yaml"

    http_connect_timeout: float = 30.0
    http_read_timeout: float = 60.0
    max_retries: int = 3
    retry_backoff_factor: float = 0.5


settings = Settings()
