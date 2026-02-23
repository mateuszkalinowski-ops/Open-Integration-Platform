"""DPD integrator configuration."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_env: str = "development"
    app_port: int = 8000
    log_level: str = "INFO"

    soap_timeout: int = 30
    soap_operation_timeout: int = 600

    dpd_wsdl_path: str = "https://dpdservices.dpd.com.pl/DPDPackageObjServicesService/DPDPackageObjServices?WSDL"
    dpd_info_wsdl_path: str = "https://dpdservices.dpd.com.pl/DPDInfoServicesObjEventsService/DPDInfoServicesObjEvents?WSDL"

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    model_config = {"env_prefix": "", "env_file": ".env"}


settings = Settings()
