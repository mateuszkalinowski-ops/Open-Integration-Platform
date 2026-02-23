"""Manages multiple Shoper account configurations loaded from YAML or environment."""

import logging
import os
from pathlib import Path

import yaml

from src.config import ShoperAccountConfig, settings

logger = logging.getLogger(__name__)


class AccountManager:
    """Loads and provides access to Shoper account configurations."""

    def __init__(self) -> None:
        self._accounts: dict[str, ShoperAccountConfig] = {}

    def load_from_yaml(self, path: str | None = None) -> None:
        config_path = Path(path or settings.accounts_config_path)
        if not config_path.exists():
            logger.warning("Accounts config not found at %s, trying environment", config_path)
            self._load_from_env()
            return

        with open(config_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)

        for account_data in data.get("accounts", []):
            account = ShoperAccountConfig(**account_data)
            self._accounts[account.name] = account
            logger.info("Loaded account: %s (env=%s)", account.name, account.environment)

    def _load_from_env(self) -> None:
        idx = 0
        while True:
            prefix = f"SHOPER_ACCOUNT_{idx}_"
            name = os.getenv(f"{prefix}NAME")
            if not name:
                break
            account = ShoperAccountConfig(
                name=name,
                shop_url=os.getenv(f"{prefix}SHOP_URL", ""),
                login=os.getenv(f"{prefix}LOGIN", ""),
                password=os.getenv(f"{prefix}PASSWORD", ""),
                language_id=os.getenv(f"{prefix}LANGUAGE_ID", "pl_PL"),
                environment=os.getenv(f"{prefix}ENVIRONMENT", "production"),
            )
            self._accounts[name] = account
            logger.info("Loaded account from env: %s", name)
            idx += 1

        if not self._accounts:
            logger.warning("No Shoper accounts configured")

    def get_account(self, name: str) -> ShoperAccountConfig | None:
        return self._accounts.get(name)

    def list_accounts(self) -> list[ShoperAccountConfig]:
        return list(self._accounts.values())

    def add_account(self, account: ShoperAccountConfig) -> None:
        self._accounts[account.name] = account
        logger.info("Added account: %s", account.name)

    def remove_account(self, name: str) -> bool:
        removed = self._accounts.pop(name, None)
        if removed:
            logger.info("Removed account: %s", name)
        return removed is not None
