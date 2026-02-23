"""Raben Group integrator configuration."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_env: str = "development"
    app_port: int = 8000
    log_level: str = "INFO"
    rest_timeout: int = 30

    raben_api_url: str = "https://myraben.com/api/v1"
    raben_sandbox_api_url: str = "https://sandbox.myraben.com/api/v1"

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @property
    def api_url(self) -> str:
        return self.raben_api_url if self.is_production else self.raben_sandbox_api_url

    model_config = {"env_prefix": "", "env_file": ".env"}


settings = Settings()
