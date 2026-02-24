"""Manages multiple Apilo account configurations loaded from YAML or environment."""

import logging
import os
from pathlib import Path

import yaml

from src.config import ApiloAccountConfig, settings

logger = logging.getLogger(__name__)


class AccountManager:
    """Loads and provides access to Apilo account configurations."""

    def __init__(self) -> None:
        self._accounts: dict[str, ApiloAccountConfig] = {}

    def load_from_yaml(self, path: str | None = None) -> None:
        config_path = Path(path or settings.accounts_config_path)
        if not config_path.exists():
            logger.warning("Accounts config not found at %s, trying environment", config_path)
            self._load_from_env()
            return

        with open(config_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)

        for account_data in data.get("accounts", []):
            account = ApiloAccountConfig(**account_data)
            self._accounts[account.name] = account
            logger.info("Loaded account: %s (url=%s, env=%s)", account.name, account.base_url, account.environment)

    def _load_from_env(self) -> None:
        idx = 0
        while True:
            prefix = f"APILO_ACCOUNT_{idx}_"
            name = os.getenv(f"{prefix}NAME")
            if not name:
                break
            account = ApiloAccountConfig(
                name=name,
                client_id=os.getenv(f"{prefix}CLIENT_ID", ""),
                client_secret=os.getenv(f"{prefix}CLIENT_SECRET", ""),
                authorization_code=os.getenv(f"{prefix}AUTHORIZATION_CODE", ""),
                refresh_token=os.getenv(f"{prefix}REFRESH_TOKEN", ""),
                base_url=os.getenv(f"{prefix}BASE_URL", "https://app.apilo.com"),
                environment=os.getenv(f"{prefix}ENVIRONMENT", "production"),
            )
            self._accounts[name] = account
            logger.info("Loaded account from env: %s (url=%s)", name, account.base_url)
            idx += 1

        if not self._accounts:
            logger.warning("No Apilo accounts configured")

    def get_account(self, name: str) -> ApiloAccountConfig | None:
        return self._accounts.get(name)

    def list_accounts(self) -> list[ApiloAccountConfig]:
        return list(self._accounts.values())

    def add_account(self, account: ApiloAccountConfig) -> None:
        self._accounts[account.name] = account
        logger.info("Added account: %s (url=%s)", account.name, account.base_url)

    def remove_account(self, name: str) -> bool:
        removed = self._accounts.pop(name, None)
        if removed:
            logger.info("Removed account: %s", name)
        return removed is not None
