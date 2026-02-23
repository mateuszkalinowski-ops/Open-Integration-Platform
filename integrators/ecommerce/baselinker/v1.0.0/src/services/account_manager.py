"""Manages multiple BaseLinker account configurations loaded from YAML or environment."""

import logging
import os
from pathlib import Path

import yaml

from src.config import BaseLinkerAccountConfig, settings

logger = logging.getLogger(__name__)


class AccountManager:
    """Loads and provides access to BaseLinker account configurations."""

    def __init__(self) -> None:
        self._accounts: dict[str, BaseLinkerAccountConfig] = {}

    def load_from_yaml(self, path: str | None = None) -> None:
        config_path = Path(path or settings.accounts_config_path)
        if not config_path.exists():
            logger.warning("Accounts config not found at %s, trying environment", config_path)
            self._load_from_env()
            return

        with open(config_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)

        for account_data in data.get("accounts", []):
            account = BaseLinkerAccountConfig(**account_data)
            self._accounts[account.name] = account
            logger.info("Loaded account: %s (env=%s)", account.name, account.environment)

    def _load_from_env(self) -> None:
        idx = 0
        while True:
            prefix = f"BASELINKER_ACCOUNT_{idx}_"
            name = os.getenv(f"{prefix}NAME")
            if not name:
                break
            account = BaseLinkerAccountConfig(
                name=name,
                api_token=os.getenv(f"{prefix}API_TOKEN", ""),
                inventory_id=int(os.getenv(f"{prefix}INVENTORY_ID", "0")),
                warehouse_id=int(os.getenv(f"{prefix}WAREHOUSE_ID", "0")),
                environment=os.getenv(f"{prefix}ENVIRONMENT", "production"),
            )
            self._accounts[name] = account
            logger.info("Loaded account from env: %s", name)
            idx += 1

        if not self._accounts:
            logger.warning("No BaseLinker accounts configured")

    def get_account(self, name: str) -> BaseLinkerAccountConfig | None:
        return self._accounts.get(name)

    def list_accounts(self) -> list[BaseLinkerAccountConfig]:
        return list(self._accounts.values())

    def add_account(self, account: BaseLinkerAccountConfig) -> None:
        self._accounts[account.name] = account
        logger.info("Added account: %s", account.name)

    def remove_account(self, name: str) -> bool:
        removed = self._accounts.pop(name, None)
        if removed:
            logger.info("Removed account: %s", name)
        return removed is not None
