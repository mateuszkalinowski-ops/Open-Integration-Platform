"""Schenker integrator configuration."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_env: str = "development"
    app_port: int = 8000
    log_level: str = "INFO"

    soap_timeout: int = 30
    soap_operation_timeout: int = 600

    schenker_transport_api_url: str = (
        "https://www.dbschenker.com/api/TransportOrders?wsdl"
    )

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    model_config = {"env_prefix": "", "env_file": ".env"}


settings = Settings()
