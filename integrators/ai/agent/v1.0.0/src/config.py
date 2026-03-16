"""Configuration for AI Agent connector."""

from __future__ import annotations

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    log_level: str = "INFO"

    gemini_api_key: str = ""
    model_name: str = "gemini-2.5-flash"
    default_temperature: float = 0.1
    max_tokens: int = 2048

    risk_threshold_high: int = 60
    risk_threshold_critical: int = 85

    available_couriers: str = "inpost,dhl,dpd,gls,fedex,ups,pocztapolska,orlenpaczka"

    http_connect_timeout: float = 30.0
    http_read_timeout: float = 120.0
    gemini_request_timeout: float = 120.0

    model_config = {"env_prefix": "AI_", "env_file": ".env"}

    @property
    def courier_list(self) -> list[str]:
        return [c.strip() for c in self.available_couriers.split(",") if c.strip()]


settings = Settings()
