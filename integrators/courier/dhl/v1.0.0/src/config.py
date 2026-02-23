"""DHL integrator configuration."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_env: str = "development"
    app_port: int = 8000
    log_level: str = "INFO"

    soap_timeout: int = 30
    soap_operation_timeout: int = 600

    dhl_prod_wsdl: str = "wsdl/dhl_42.wsdl"
    dhl_sandbox_wsdl: str = "wsdl/sandbox_dhl_42.wsdl"
    dhl_prod_parcelshop_url: str = "https://dhl24.com.pl/servicepoint"
    dhl_sandbox_parcelshop_url: str = "https://sandbox.dhl24.com.pl/servicepoint"

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @property
    def wsdl_url(self) -> str:
        return self.dhl_prod_wsdl if self.is_production else self.dhl_sandbox_wsdl

    @property
    def parcelshop_url(self) -> str:
        return self.dhl_prod_parcelshop_url if self.is_production else self.dhl_sandbox_parcelshop_url

    model_config = {"env_prefix": "", "env_file": ".env"}


settings = Settings()
