"""FedEx integrator configuration."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_env: str = "development"
    app_port: int = 8000
    log_level: str = "INFO"

    fedex_api_url: str = "https://apis-sandbox.fedex.com/"
    rest_timeout: int = 30
    default_currency: str = "PLN"

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    model_config = {"env_prefix": "", "env_file": ".env"}


settings = Settings()
