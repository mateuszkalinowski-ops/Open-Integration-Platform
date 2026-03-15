"""Manages multiple WooCommerce store account configurations loaded from YAML or environment."""

import logging
import os
from pathlib import Path

import yaml

from src.config import WooCommerceAccountConfig, settings

logger = logging.getLogger(__name__)


class AccountManager:
    """Loads and provides access to WooCommerce store configurations."""

    def __init__(self) -> None:
        self._accounts: dict[str, WooCommerceAccountConfig] = {}

    def load_from_yaml(self, path: str | None = None) -> None:
        config_path = Path(path or settings.accounts_config_path)
        if not config_path.exists():
            logger.warning("Accounts config not found at %s, trying environment", config_path)
            self._load_from_env()
            return

        with open(config_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)

        for account_data in data.get("accounts", []):
            account = WooCommerceAccountConfig(**account_data)
            self._accounts[account.name] = account
            logger.info("Loaded account: %s (env=%s, url=%s)", account.name, account.environment, account.store_url)

    def _load_from_env(self) -> None:
        """Fallback: load accounts from WOOCOMMERCE_ACCOUNT_* environment variables."""
        idx = 0
        while True:
            prefix = f"WOOCOMMERCE_ACCOUNT_{idx}_"
            name = os.getenv(f"{prefix}NAME")
            if not name:
                break
            account = WooCommerceAccountConfig(
                name=name,
                store_url=os.getenv(f"{prefix}STORE_URL", ""),
                consumer_key=os.getenv(f"{prefix}CONSUMER_KEY", ""),
                consumer_secret=os.getenv(f"{prefix}CONSUMER_SECRET", ""),
                api_version=os.getenv(f"{prefix}API_VERSION", "wc/v3"),
                verify_ssl=os.getenv(f"{prefix}VERIFY_SSL", "true").lower() == "true",
                environment=os.getenv(f"{prefix}ENVIRONMENT", "production"),
            )
            self._accounts[name] = account
            logger.info("Loaded account from env: %s", name)
            idx += 1

        if not self._accounts:
            logger.warning("No WooCommerce accounts configured")

    def get_account(self, name: str) -> WooCommerceAccountConfig | None:
        return self._accounts.get(name)

    def list_accounts(self) -> list[WooCommerceAccountConfig]:
        return list(self._accounts.values())

    def add_account(self, account: WooCommerceAccountConfig) -> None:
        self._accounts[account.name] = account
        logger.info("Added account: %s", account.name)

    def remove_account(self, name: str) -> bool:
        removed = self._accounts.pop(name, None)
        if removed:
            logger.info("Removed account: %s", name)
        return removed is not None
