"""FX Couriers integrator configuration."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_env: str = "development"
    app_port: int = 8000
    log_level: str = "INFO"
    rest_timeout: int = 30

    fxcouriers_api_url: str = "https://fxcouriers.kuriersystem.pl/api/rest"

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    model_config = {"env_prefix": "", "env_file": ".env"}


settings = Settings()
