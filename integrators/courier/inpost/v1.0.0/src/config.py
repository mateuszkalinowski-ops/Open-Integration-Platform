"""InPost integrator configuration."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_env: str = "development"
    app_port: int = 8000
    log_level: str = "INFO"
    default_currency: str = "PLN"
    rest_timeout: int = 30

    inpost_prod_api_url: str = "https://api-shipx-pl.easypack24.net/"
    inpost_sandbox_api_url: str = "https://sandbox-api-shipx-pl.easypack24.net/"

    inpost_waybill_retry_count: int = 10
    inpost_waybill_retry_wait: float = 1.0

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @property
    def api_url(self) -> str:
        return self.inpost_prod_api_url if self.is_production else self.inpost_sandbox_api_url

    model_config = {"env_prefix": "", "env_file": ".env"}


settings = Settings()
