"""Manages multiple Shopify store configurations loaded from YAML or environment."""

import logging
import os
from pathlib import Path

import yaml

from src.config import ShopifyAccountConfig, settings

logger = logging.getLogger(__name__)


class AccountManager:
    """Loads and provides access to Shopify account configurations."""

    def __init__(self) -> None:
        self._accounts: dict[str, ShopifyAccountConfig] = {}

    def load_from_yaml(self, path: str | None = None) -> None:
        config_path = Path(path or settings.accounts_config_path)
        if not config_path.exists():
            logger.warning("Accounts config not found at %s, trying environment", config_path)
            self._load_from_env()
            return

        with open(config_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)

        if not data:
            logger.warning("Empty accounts config at %s, trying environment", config_path)
            self._load_from_env()
            return

        for account_data in data.get("accounts") or []:
            if not account_data or not account_data.get("name"):
                continue
            account = ShopifyAccountConfig(**account_data)
            self._accounts[account.name] = account
            logger.info("Loaded account: %s (shop=%s)", account.name, account.shop_url)

    def _load_from_env(self) -> None:
        """Fallback: load accounts from SHOPIFY_ACCOUNT_* environment variables."""
        idx = 0
        while True:
            prefix = f"SHOPIFY_ACCOUNT_{idx}_"
            name = os.getenv(f"{prefix}NAME")
            if not name:
                break
            account = ShopifyAccountConfig(
                name=name,
                shop_url=os.getenv(f"{prefix}SHOP_URL", ""),
                access_token=os.getenv(f"{prefix}ACCESS_TOKEN", ""),
                api_version=os.getenv(f"{prefix}API_VERSION", settings.default_api_version),
                default_location_id=os.getenv(f"{prefix}DEFAULT_LOCATION_ID", ""),
                default_carrier=os.getenv(f"{prefix}DEFAULT_CARRIER", settings.default_carrier),
            )
            self._accounts[name] = account
            logger.info("Loaded account from env: %s", name)
            idx += 1

        if not self._accounts:
            logger.warning("No Shopify accounts configured")

    def get_account(self, name: str) -> ShopifyAccountConfig | None:
        return self._accounts.get(name)

    def list_accounts(self) -> list[ShopifyAccountConfig]:
        return list(self._accounts.values())

    def add_account(self, account: ShopifyAccountConfig) -> None:
        self._accounts[account.name] = account
        logger.info("Added account: %s", account.name)

    def remove_account(self, name: str) -> bool:
        removed = self._accounts.pop(name, None)
        if removed:
            logger.info("Removed account: %s", name)
        return removed is not None
