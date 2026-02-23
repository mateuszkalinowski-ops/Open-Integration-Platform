"""Manages multiple IdoSell account configurations loaded from YAML or environment."""

import logging
import os
from pathlib import Path

import yaml

from src.config import IdoSellAccountConfig, settings

logger = logging.getLogger(__name__)


class AccountManager:
    """Loads and provides access to IdoSell account configurations."""

    def __init__(self) -> None:
        self._accounts: dict[str, IdoSellAccountConfig] = {}

    def load_from_yaml(self, path: str | None = None) -> None:
        config_path = Path(path or settings.accounts_config_path)
        if not config_path.exists():
            logger.warning("Accounts config not found at %s, trying environment", config_path)
            self._load_from_env()
            return

        with open(config_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)

        for account_data in data.get("accounts", []):
            account = IdoSellAccountConfig(**account_data)
            self._accounts[account.name] = account
            logger.info("Loaded account: %s (env=%s)", account.name, account.environment)

    def _load_from_env(self) -> None:
        idx = 0
        while True:
            prefix = f"IDOSELL_ACCOUNT_{idx}_"
            name = os.getenv(f"{prefix}NAME")
            if not name:
                break
            account = IdoSellAccountConfig(
                name=name,
                shop_url=os.getenv(f"{prefix}SHOP_URL", ""),
                api_key=os.getenv(f"{prefix}API_KEY", ""),
                api_version=os.getenv(f"{prefix}API_VERSION", "v6"),
                default_stock_id=int(os.getenv(f"{prefix}DEFAULT_STOCK_ID", "1")),
                default_currency=os.getenv(f"{prefix}DEFAULT_CURRENCY", "PLN"),
                environment=os.getenv(f"{prefix}ENVIRONMENT", "production"),
            )
            self._accounts[name] = account
            logger.info("Loaded account from env: %s", name)
            idx += 1

        if not self._accounts:
            logger.warning("No IdoSell accounts configured")

    def get_account(self, name: str) -> IdoSellAccountConfig | None:
        return self._accounts.get(name)

    def list_accounts(self) -> list[IdoSellAccountConfig]:
        return list(self._accounts.values())

    def add_account(self, account: IdoSellAccountConfig) -> None:
        self._accounts[account.name] = account
        logger.info("Added account: %s", account.name)

    def remove_account(self, name: str) -> bool:
        removed = self._accounts.pop(name, None)
        if removed:
            logger.info("Removed account: %s", name)
        return removed is not None
