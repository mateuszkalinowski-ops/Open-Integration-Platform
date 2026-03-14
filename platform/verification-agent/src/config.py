"""Configuration for the Verification Agent service."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "verification-agent"
    app_version: str = "1.0.0"
    host: str = "0.0.0.0"
    port: int = 8000
    log_level: str = "INFO"

    database_url: str = ""
    encryption_key: str = ""

    verification_interval_days: int = 7
    verification_timeout_seconds: float = 60.0
    connector_discovery_path: str = "/app/integrators"
    default_connector_port: int = 8000

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
