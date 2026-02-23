"""Configuration for IdoSell integrator — loaded from environment variables."""

from pydantic import Field
from pydantic_settings import BaseSettings


class IdoSellAccountConfig(BaseSettings):
    """Single IdoSell account configuration.

    Supports two authentication modes:
      - "api_key" (default): Modern X-API-KEY header, URL: /api/admin/{version}/
      - "legacy":  SHA-1 daily key in request body, URL: /admin/{version}/
    """

    name: str
    shop_url: str
    api_key: str = ""
    login: str = ""
    password: str = ""
    auth_mode: str = "api_key"
    api_version: str = "v6"
    default_stock_id: int = 1
    default_currency: str = "PLN"
    environment: str = "production"


class Settings(BaseSettings):
    model_config = {"env_prefix": "IDOSELL_", "env_nested_delimiter": "__"}

    app_name: str = "idosell-integrator"
    app_version: str = "1.0.0"
    debug: bool = False

    host: str = "0.0.0.0"
    port: int = 8000
    log_level: str = "INFO"

    database_url: str = Field(
        default="sqlite+aiosqlite:///./idosell_integrator.db",
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

    kafka_topic_orders_out: str = "idosell.output.ecommerce.orders.save"
    kafka_topic_products_out: str = "idosell.output.ecommerce.products.save"

    scraping_enabled: bool = True
    scraping_interval_seconds: int = 120

    scrape_orders: bool = True
    scrape_products: bool = True

    default_unit: str = "szt."
    default_order_type: str = "WZ"

    accounts_config_path: str = "/app/config/accounts.yaml"

    http_connect_timeout: float = 30.0
    http_read_timeout: float = 60.0
    max_retries: int = 3
    retry_backoff_factor: float = 0.5

    idosell_date_format: str = "%Y-%m-%d %H:%M:%S"
    results_limit: int = 100


settings = Settings()
