"""UPS integrator configuration."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_env: str = "development"
    app_port: int = 8000
    log_level: str = "INFO"

    rest_timeout: int = 30

    ups_api_url: str = "https://wwwcie.ups.com"
    ups_prod_api_url: str = "https://onlinetools.ups.com"
    ups_api_version: str = "v2403"

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @property
    def base_url(self) -> str:
        return self.ups_prod_api_url if self.is_production else self.ups_api_url

    model_config = {"env_prefix": "", "env_file": ".env"}


settings = Settings()
