"""Configuration for InsERT Nexo cloud connector."""

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = {"env_prefix": "NEXO_CONNECTOR_", "env_nested_delimiter": "__"}

    app_name: str = "insert-nexo-connector"
    app_version: str = "1.0.0"
    debug: bool = False

    host: str = "0.0.0.0"
    port: int = 8000
    log_level: str = "INFO"

    database_url: str = Field(
        default="sqlite+aiosqlite:///./nexo_connector.db",
        alias="DATABASE_URL",
    )

    accounts_config_path: str = "/app/config/accounts.yaml"

    http_connect_timeout: float = 30.0
    http_read_timeout: float = 60.0
    max_retries: int = 3
    retry_backoff_factor: float = 1.0


settings = Settings()
