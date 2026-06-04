"""Configuration for REST API Gateway connector."""

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = {"env_prefix": "REST_API_", "env_nested_delimiter": "__", "populate_by_name": True}

    app_name: str = "rest-api-connector"
    app_version: str = "1.0.0"
    debug: bool = False

    host: str = "0.0.0.0"
    port: int = 8000
    log_level: str = "INFO"

    default_connect_timeout: float = Field(default=30.0, description="Default HTTP connect timeout (s)")
    default_read_timeout: float = Field(default=60.0, description="Default HTTP read timeout (s)")
    default_max_retries: int = Field(default=3, ge=0, le=10)

    accounts_config_path: str = "/app/config/accounts.yaml"
    profiles_dir: str = "/app/config/profiles"

    platform_api_url: str = Field(default="http://platform:8080", alias="PLATFORM_API_URL")
    platform_api_key: str = Field(default="", alias="PLATFORM_API_KEY")
    platform_internal_secret: str = Field(default="", alias="PLATFORM_INTERNAL_SECRET")


settings = Settings()
