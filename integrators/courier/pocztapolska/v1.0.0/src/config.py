"""Poczta Polska integrator configuration."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_env: str = "development"
    app_port: int = 8000
    log_level: str = "INFO"

    soap_timeout: int = 30
    soap_operation_timeout: int = 600

    poczta_polska_tracking_wsdl: str = "https://tt.poczta-polska.pl/Sledzenie/services/Sledzenie?wsdl"
    poczta_polska_posting_wsdl: str = "https://e-nadawca.poczta-polska.pl/websrv/en.php?wsdl"
    use_pocztapolska_guid: bool = True

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    model_config = {"env_prefix": "", "env_file": ".env"}


settings = Settings()
