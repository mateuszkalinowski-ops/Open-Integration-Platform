"""BulkGate SMS Gateway integrator configuration."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_env: str = "development"
    app_port: int = 8000
    log_level: str = "INFO"
    rest_timeout: int = 30

    bulkgate_api_url: str = "https://portal.bulkgate.com"

    @property
    def simple_transactional_url(self) -> str:
        return f"{self.bulkgate_api_url}/api/1.0/simple/transactional"

    @property
    def simple_promotional_url(self) -> str:
        return f"{self.bulkgate_api_url}/api/1.0/simple/promotional"

    @property
    def advanced_transactional_url(self) -> str:
        return f"{self.bulkgate_api_url}/api/2.0/advanced/transactional"

    @property
    def credit_balance_url(self) -> str:
        return f"{self.bulkgate_api_url}/api/2.0/advanced/info"

    model_config = {"env_prefix": "", "env_file": ".env"}


settings = Settings()
