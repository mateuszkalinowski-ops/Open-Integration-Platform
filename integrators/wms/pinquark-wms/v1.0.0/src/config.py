"""Configuration for the Pinquark WMS connector."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    api_url: str = "http://localhost:8090"
    username: str = ""
    password: str = ""

    http_connect_timeout: float = 30.0
    http_read_timeout: float = 60.0

    feedback_poll_interval: float = 2.0
    feedback_poll_max_attempts: int = 15
    feedback_poll_backoff: float = 1.3

    event_polling_enabled: bool = True
    event_polling_interval_seconds: int = 120
    event_polling_initial_delay: int = 15

    platform_api_url: str = "http://platform:8080"
    platform_event_notify: bool = True

    log_level: str = "INFO"

    model_config = {"env_prefix": "PINQUARK_WMS_"}


settings = Settings()
