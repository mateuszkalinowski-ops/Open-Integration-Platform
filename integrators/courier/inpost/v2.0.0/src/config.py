"""InPost International 2024 integrator configuration."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_env: str = "development"
    app_port: int = 8000
    log_level: str = "INFO"
    default_currency: str = "EUR"
    rest_timeout: int = 30

    inpost_int_2024_api_url: str = "https://api.inpost-group.com"
    inpost_int_2024_sandbox_api_url: str = "https://sandbox-api.inpost-group.com"

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @property
    def api_url(self) -> str:
        return self.inpost_int_2024_api_url if self.is_production else self.inpost_int_2024_sandbox_api_url

    model_config = {"env_prefix": "", "env_file": ".env"}


settings = Settings()
