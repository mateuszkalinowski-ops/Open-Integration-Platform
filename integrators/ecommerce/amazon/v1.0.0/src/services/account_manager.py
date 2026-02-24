"""Manages multiple Amazon seller account configurations loaded from YAML or environment."""

import logging
import os
from pathlib import Path

import yaml

from src.config import AmazonAccountConfig, settings

logger = logging.getLogger(__name__)


class AccountManager:
    """Loads and provides access to Amazon account configurations."""

    def __init__(self) -> None:
        self._accounts: dict[str, AmazonAccountConfig] = {}

    def load_from_yaml(self, path: str | None = None) -> None:
        config_path = Path(path or settings.accounts_config_path)
        if not config_path.exists():
            logger.warning("Accounts config not found at %s, trying environment", config_path)
            self._load_from_env()
            return

        with open(config_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)

        for account_data in data.get("accounts", []):
            account = AmazonAccountConfig(**account_data)
            self._accounts[account.name] = account
            logger.info("Loaded account: %s (region=%s, env=%s)", account.name, account.region, account.environment)

    def _load_from_env(self) -> None:
        idx = 0
        while True:
            prefix = f"AMAZON_ACCOUNT_{idx}_"
            name = os.getenv(f"{prefix}NAME")
            if not name:
                break
            account = AmazonAccountConfig(
                name=name,
                client_id=os.getenv(f"{prefix}CLIENT_ID", ""),
                client_secret=os.getenv(f"{prefix}CLIENT_SECRET", ""),
                refresh_token=os.getenv(f"{prefix}REFRESH_TOKEN", ""),
                marketplace_id=os.getenv(f"{prefix}MARKETPLACE_ID", ""),
                region=os.getenv(f"{prefix}REGION", "eu"),
                sandbox_mode=os.getenv(f"{prefix}SANDBOX_MODE", "false").lower() == "true",
                environment=os.getenv(f"{prefix}ENVIRONMENT", "production"),
            )
            self._accounts[name] = account
            logger.info("Loaded account from env: %s (region=%s)", name, account.region)
            idx += 1

        if not self._accounts:
            logger.warning("No Amazon accounts configured")

    def get_account(self, name: str) -> AmazonAccountConfig | None:
        return self._accounts.get(name)

    def list_accounts(self) -> list[AmazonAccountConfig]:
        return list(self._accounts.values())

    def add_account(self, account: AmazonAccountConfig) -> None:
        self._accounts[account.name] = account
        logger.info("Added account: %s (region=%s)", account.name, account.region)

    def remove_account(self, name: str) -> bool:
        removed = self._accounts.pop(name, None)
        if removed:
            logger.info("Removed account: %s", name)
        return removed is not None
