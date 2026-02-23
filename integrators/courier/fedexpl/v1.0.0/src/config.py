"""FedEx PL integrator configuration."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_env: str = "development"
    app_port: int = 8000
    log_level: str = "INFO"

    fedex_pl_wsdl: str = "https://poland.fedex.com/fdsWs/IklServicePort?wsdl"
    soap_timeout: int = 30
    soap_operation_timeout: int = 600

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    model_config = {"env_prefix": "", "env_file": ".env"}


settings = Settings()
