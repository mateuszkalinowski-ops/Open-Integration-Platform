"""Geis integrator configuration."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_env: str = "development"
    app_port: int = 8000
    log_level: str = "INFO"

    soap_timeout: int = 30

    geis_api_url: str = "https://geis-api-url/service.svc?wsdl"
    default_language: str = "PL"

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    model_config = {"env_prefix": "", "env_file": ".env"}


settings = Settings()
