from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    sellasist_api_url: str = "https://login.sellasist.pl/api/v1"
    rest_integration_timeout: int = 30
    log_level: str = "INFO"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
