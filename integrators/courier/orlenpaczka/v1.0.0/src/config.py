"""Orlen Paczka integrator configuration."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_env: str = "development"
    app_port: int = 8000
    log_level: str = "INFO"

    soap_timeout: int = 30

    orlen_paczka_wsdl_path: str = "wsdl/orlenpaczka.wsdl"
    orlen_paczka_cod_transfer_message: str = "Zamowienie {content}"

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    model_config = {"env_prefix": "", "env_file": ".env"}


settings = Settings()
