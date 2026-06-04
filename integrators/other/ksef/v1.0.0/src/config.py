"""Configuration for KSeF integrator — loaded from environment variables."""

from enum import Enum

from pydantic import Field
from pydantic_settings import BaseSettings


class KSeFEnvironment(str, Enum):
    TEST = "test"
    DEMO = "demo"
    PRODUCTION = "production"


KSEF_API_URLS = {
    KSeFEnvironment.TEST: "https://api-test.ksef.mf.gov.pl/api/v2",
    KSeFEnvironment.DEMO: "https://api-demo.ksef.mf.gov.pl/api/v2",
    KSeFEnvironment.PRODUCTION: "https://api.ksef.mf.gov.pl/api/v2",
}


class KSeFAccountConfig(BaseSettings):
    """Single KSeF account configuration."""

    name: str
    nip: str
    ksef_token: str = ""
    environment: KSeFEnvironment = KSeFEnvironment.DEMO
    certificate_path: str = ""
    certificate_password: str = ""
    company_name: str = ""

    @property
    def api_url(self) -> str:
        return KSEF_API_URLS[self.environment]


class Settings(BaseSettings):
    model_config = {"env_prefix": "KSEF_", "env_nested_delimiter": "__", "populate_by_name": True}

    app_name: str = "ksef-integrator"
    app_version: str = "1.0.0"
    debug: bool = False

    host: str = "0.0.0.0"
    port: int = 8000
    log_level: str = "INFO"

    default_environment: KSeFEnvironment = Field(
        default=KSeFEnvironment.DEMO,
        alias="KSEF_DEFAULT_ENVIRONMENT",
    )

    kafka_enabled: bool = Field(default=False, alias="KAFKA_ENABLED")
    kafka_bootstrap_servers: str = Field(default="localhost:9092", alias="KAFKA_BOOTSTRAP_SERVERS")
    kafka_security_protocol: str = Field(default="PLAINTEXT", alias="KAFKA_SECURITY_PROTOCOL")
    kafka_sasl_mechanism: str = Field(default="PLAIN", alias="KAFKA_SASL_MECHANISM")
    kafka_sasl_username: str = Field(default="", alias="KAFKA_SASL_USERNAME")
    kafka_sasl_password: str = Field(default="", alias="KAFKA_SASL_PASSWORD")

    kafka_topic_invoice_sent: str = "ksef.output.other.invoices.sent"
    kafka_topic_invoice_accepted: str = "ksef.output.other.invoices.accepted"

    api_timeout: float = 60.0
    auth_poll_interval: float = 2.0
    auth_poll_max_attempts: int = 30

    accounts_config_path: str = "/app/config/accounts.yaml"

    platform_api_url: str = Field(default="http://platform:8080", alias="PLATFORM_API_URL")
    platform_api_key: str = Field(default="", alias="PLATFORM_API_KEY")
    platform_internal_secret: str = Field(default="", alias="PLATFORM_INTERNAL_SECRET")
    platform_event_notify: bool = Field(default=True, alias="PLATFORM_EVENT_NOTIFY")


settings = Settings()
