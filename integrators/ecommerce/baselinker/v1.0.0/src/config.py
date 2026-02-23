"""Configuration for BaseLinker integrator — loaded from environment variables."""

from pydantic import Field
from pydantic_settings import BaseSettings


class BaseLinkerAccountConfig(BaseSettings):
    """Single BaseLinker account configuration."""

    name: str
    api_token: str
    inventory_id: int = 0
    warehouse_id: int = 0
    environment: str = "production"


class Settings(BaseSettings):
    model_config = {"env_prefix": "BASELINKER_", "env_nested_delimiter": "__"}

    app_name: str = "baselinker-integrator"
    app_version: str = "1.0.0"
    debug: bool = False

    host: str = "0.0.0.0"
    port: int = 8000
    log_level: str = "INFO"

    database_url: str = Field(
        default="sqlite+aiosqlite:///./baselinker_integrator.db",
        alias="DATABASE_URL",
    )
    encryption_key: str = Field(default="", alias="DATABASE_ENCRYPTION_KEY")

    kafka_enabled: bool = Field(default=False, alias="KAFKA_ENABLED")
    kafka_bootstrap_servers: str = Field(default="localhost:9092", alias="KAFKA_BOOTSTRAP_SERVERS")
    kafka_security_protocol: str = Field(default="PLAINTEXT", alias="KAFKA_SECURITY_PROTOCOL")
    kafka_sasl_mechanism: str = Field(default="PLAIN", alias="KAFKA_SASL_MECHANISM")
    kafka_sasl_username: str = Field(default="", alias="KAFKA_SASL_USERNAME")
    kafka_sasl_password: str = Field(default="", alias="KAFKA_SASL_PASSWORD")

    kafka_topic_orders_out: str = "baselinker.output.ecommerce.orders.save"
    kafka_topic_products_out: str = "baselinker.output.ecommerce.products.save"

    scraping_enabled: bool = True
    scraping_interval_seconds: int = 120

    scrape_orders: bool = True
    scrape_products: bool = True

    accounts_config_path: str = "/app/config/accounts.yaml"

    http_connect_timeout: float = 30.0
    http_read_timeout: float = 60.0
    max_retries: int = 3
    retry_backoff_factor: float = 1.0

    baselinker_api_url: str = "https://api.baselinker.com/connector.php"


settings = Settings()
