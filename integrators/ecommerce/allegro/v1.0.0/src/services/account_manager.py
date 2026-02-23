"""Manages multiple Allegro account configurations loaded from YAML or environment."""

import logging
import os
from pathlib import Path

import yaml

from src.config import AllegroAccountConfig, settings

logger = logging.getLogger(__name__)


class AccountManager:
    """Loads and provides access to Allegro account configurations."""

    def __init__(self):
        self._accounts: dict[str, AllegroAccountConfig] = {}

    def load_from_yaml(self, path: str | None = None) -> None:
        config_path = Path(path or settings.accounts_config_path)
        if not config_path.exists():
            logger.warning("Accounts config not found at %s, trying environment", config_path)
            self._load_from_env()
            return

        with open(config_path) as f:
            data = yaml.safe_load(f)

        for account_data in data.get("accounts", []):
            account = AllegroAccountConfig(**account_data)
            self._accounts[account.name] = account
            logger.info("Loaded account: %s (env=%s)", account.name, account.environment)

    def _load_from_env(self) -> None:
        """Fallback: load accounts from ALLEGRO_ACCOUNT_* environment variables."""
        idx = 0
        while True:
            prefix = f"ALLEGRO_ACCOUNT_{idx}_"
            name = os.getenv(f"{prefix}NAME")
            if not name:
                break
            account = AllegroAccountConfig(
                name=name,
                client_id=os.getenv(f"{prefix}CLIENT_ID", ""),
                client_secret=os.getenv(f"{prefix}CLIENT_SECRET", ""),
                api_url=os.getenv(f"{prefix}API_URL", "https://api.allegro.pl"),
                auth_url=os.getenv(f"{prefix}AUTH_URL", "https://allegro.pl/auth/oauth"),
                environment=os.getenv(f"{prefix}ENVIRONMENT", "production"),
            )
            self._accounts[name] = account
            logger.info("Loaded account from env: %s", name)
            idx += 1

        if not self._accounts:
            logger.warning("No Allegro accounts configured")

    def get_account(self, name: str) -> AllegroAccountConfig | None:
        return self._accounts.get(name)

    def list_accounts(self) -> list[AllegroAccountConfig]:
        return list(self._accounts.values())

    def add_account(self, account: AllegroAccountConfig) -> None:
        self._accounts[account.name] = account
        logger.info("Added account: %s", account.name)

    def remove_account(self, name: str) -> bool:
        removed = self._accounts.pop(name, None)
        if removed:
            logger.info("Removed account: %s", name)
        return removed is not None
