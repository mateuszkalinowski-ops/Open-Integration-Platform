"""Configuration for Amazon SP-API integrator — loaded from environment variables."""

from pydantic import Field
from pydantic_settings import BaseSettings

REGION_ENDPOINTS = {
    "na": "https://sellingpartnerapi-na.amazon.com",
    "eu": "https://sellingpartnerapi-eu.amazon.com",
    "fe": "https://sellingpartnerapi-fe.amazon.com",
}

SANDBOX_ENDPOINTS = {
    "na": "https://sandbox.sellingpartnerapi-na.amazon.com",
    "eu": "https://sandbox.sellingpartnerapi-eu.amazon.com",
    "fe": "https://sandbox.sellingpartnerapi-fe.amazon.com",
}

LWA_TOKEN_URL = "https://api.amazon.com/auth/o2/token"


class AmazonAccountConfig(BaseSettings):
    """Single Amazon seller account configuration."""

    name: str
    client_id: str
    client_secret: str
    refresh_token: str
    marketplace_id: str
    region: str = "eu"
    sandbox_mode: bool = False
    environment: str = "production"

    @property
    def base_url(self) -> str:
        endpoints = SANDBOX_ENDPOINTS if self.sandbox_mode else REGION_ENDPOINTS
        return endpoints.get(self.region, REGION_ENDPOINTS["eu"])


class Settings(BaseSettings):
    model_config = {"env_prefix": "AMAZON_", "env_nested_delimiter": "__"}

    app_name: str = "amazon-integrator"
    app_version: str = "1.0.0"
    debug: bool = False

    host: str = "0.0.0.0"
    port: int = 8000
    log_level: str = "INFO"

    database_url: str = Field(
        default="sqlite+aiosqlite:///./amazon_integrator.db",
        alias="DATABASE_URL",
    )
    encryption_key: str = Field(default="", alias="DATABASE_ENCRYPTION_KEY")

    kafka_enabled: bool = Field(default=False, alias="KAFKA_ENABLED")
    kafka_bootstrap_servers: str = Field(default="localhost:9092", alias="KAFKA_BOOTSTRAP_SERVERS")
    kafka_security_protocol: str = Field(default="PLAINTEXT", alias="KAFKA_SECURITY_PROTOCOL")
    kafka_sasl_mechanism: str = Field(default="PLAIN", alias="KAFKA_SASL_MECHANISM")
    kafka_sasl_username: str = Field(default="", alias="KAFKA_SASL_USERNAME")
    kafka_sasl_password: str = Field(default="", alias="KAFKA_SASL_PASSWORD")

    kafka_topic_orders_out: str = "amazon.output.ecommerce.orders.save"
    kafka_topic_products_out: str = "amazon.output.ecommerce.products.save"

    scraping_enabled: bool = True
    scraping_interval_seconds: int = 300

    scrape_orders: bool = True

    accounts_config_path: str = "/app/config/accounts.yaml"

    http_connect_timeout: float = 30.0
    http_read_timeout: float = 60.0
    max_retries: int = 3
    retry_backoff_factor: float = 1.0


settings = Settings()
