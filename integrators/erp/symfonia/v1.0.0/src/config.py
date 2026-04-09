"""Configuration for Symfonia ERP WebAPI connector."""

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = {"env_prefix": "SYMFONIA_CONNECTOR_", "env_nested_delimiter": "__"}

    app_name: str = "symfonia-connector"
    app_version: str = "1.0.0"
    debug: bool = False

    host: str = "0.0.0.0"
    port: int = 8000
    log_level: str = "INFO"

    webapi_url: str = Field(
        default="http://localhost:8080",
        description="Base URL of the Symfonia WebAPI service",
    )
    application_guid: str = Field(
        default="",
        description="Application GUID from Symfonia configurator for authentication",
    )
    device_name: str = Field(
        default="pinquark-oip",
        description="Device name used when opening WebAPI sessions",
    )

    session_timeout_minutes: int = 30
    sync_interval_seconds: int = 300

    http_connect_timeout: float = 30.0
    http_read_timeout: float = 60.0
    max_retries: int = 3
    retry_backoff_factor: float = 1.0


settings = Settings()
