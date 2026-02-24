"""Manages multiple Slack workspace/bot configurations loaded from YAML or environment."""

import logging
import os
from pathlib import Path

import yaml

from src.config import SlackAccountConfig, settings

logger = logging.getLogger(__name__)


class AccountManager:
    """Loads and provides access to Slack account configurations."""

    def __init__(self) -> None:
        self._accounts: dict[str, SlackAccountConfig] = {}

    def load_from_yaml(self, path: str | None = None) -> None:
        config_path = Path(path or settings.accounts_config_path)
        if not config_path.exists():
            logger.warning("Accounts config not found at %s, trying environment", config_path)
            self._load_from_env()
            return

        with open(config_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)

        for account_data in data.get("accounts", []):
            account = SlackAccountConfig(**account_data)
            self._accounts[account.name] = account
            logger.info("Loaded account: %s (env=%s)", account.name, account.environment)

    def _load_from_env(self) -> None:
        idx = 0
        while True:
            prefix = f"SLACK_ACCOUNT_{idx}_"
            name = os.getenv(f"{prefix}NAME")
            if not name:
                break
            account = SlackAccountConfig(
                name=name,
                bot_token=os.getenv(f"{prefix}BOT_TOKEN", ""),
                app_token=os.getenv(f"{prefix}APP_TOKEN", ""),
                default_channel=os.getenv(f"{prefix}DEFAULT_CHANNEL", "general"),
                environment=os.getenv(f"{prefix}ENVIRONMENT", "production"),
            )
            self._accounts[name] = account
            logger.info("Loaded account from env: %s", name)
            idx += 1

        if not self._accounts:
            logger.warning("No Slack accounts configured")

    def get_account(self, name: str) -> SlackAccountConfig | None:
        return self._accounts.get(name)

    def list_accounts(self) -> list[SlackAccountConfig]:
        return list(self._accounts.values())

    def add_account(self, account: SlackAccountConfig) -> None:
        self._accounts[account.name] = account
        logger.info("Added account: %s", account.name)

    def remove_account(self, name: str) -> bool:
        removed = self._accounts.pop(name, None)
        if removed:
            logger.info("Removed account: %s", name)
        return removed is not None
