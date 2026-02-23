"""DHL Express integrator configuration."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_env: str = "development"
    app_port: int = 8000
    log_level: str = "INFO"

    dhl_express_api_key: str = ""
    dhl_express_api_secret: str = ""

    # MyDHL Express API (shipments, rates, pickups — requires DHL Express customer account)
    dhl_express_base_url: str = "https://express.api.dhl.com/mydhlapi/test"
    dhl_express_prod_url: str = "https://express.api.dhl.com/mydhlapi"

    # DHL Unified APIs (tracking, locations — uses DHL-API-Key header)
    dhl_tracking_url: str = "https://api-eu.dhl.com/track/shipments"
    dhl_location_finder_url: str = "https://api.dhl.com/location-finder/v1"

    http_timeout: int = 30
    http_max_retries: int = 3

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @property
    def api_base_url(self) -> str:
        return self.dhl_express_prod_url if self.is_production else self.dhl_express_base_url

    model_config = {"env_prefix": "", "env_file": ".env"}


settings = Settings()
