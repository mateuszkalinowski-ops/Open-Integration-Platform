"""Account manager for EDIFACT connector — manages multiple terminal accounts."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import yaml

from src.config import settings
from src.services.edifact_client import EdifactClient

logger = logging.getLogger(__name__)


class AccountConfig:
    """Single terminal account configuration."""

    def __init__(
        self,
        name: str,
        base_url: str,
        api_key: str = "",
        description: str = "",
    ) -> None:
        self.name = name
        self.base_url = base_url
        self.api_key = api_key
        self.description = description


class AccountManager:
    """Manages external terminal accounts and their HTTP clients."""

    def __init__(self) -> None:
        self._accounts: dict[str, AccountConfig] = {}
        self._clients: dict[str, EdifactClient] = {}

    def load_from_yaml(self) -> None:
        config_path = Path(settings.accounts_config_path)
        if not config_path.exists():
            logger.warning("Accounts config not found at %s", config_path)
            return

        with open(config_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)

        if not data or "accounts" not in data:
            logger.warning("No accounts found in config")
            return

        for account_data in data["accounts"]:
            self.add_account(account_data)

        logger.info("Loaded %d account(s) from %s", len(self._accounts), config_path)

    def add_account(self, account_data: dict[str, Any]) -> AccountConfig:
        account = AccountConfig(
            name=account_data["name"],
            base_url=account_data.get("base_url", settings.base_url),
            api_key=account_data.get("api_key", settings.api_key),
            description=account_data.get("description", ""),
        )
        self._accounts[account.name] = account

        if account.name in self._clients:
            del self._clients[account.name]

        logger.info("Account added: %s -> %s", account.name, account.base_url)
        return account

    def remove_account(self, name: str) -> None:
        if name not in self._accounts:
            raise KeyError(f"Account '{name}' not found")
        del self._accounts[name]
        self._clients.pop(name, None)
        logger.info("Account removed: %s", name)

    def get_client(self, name: str) -> EdifactClient:
        if name not in self._accounts:
            raise KeyError(f"Account '{name}' not found")

        if name not in self._clients:
            account = self._accounts[name]
            self._clients[name] = EdifactClient(
                base_url=account.base_url,
                api_key=account.api_key,
                name=name,
            )
        return self._clients[name]

    def list_accounts(self) -> list[dict[str, str]]:
        return [
            {
                "name": a.name,
                "base_url": a.base_url,
                "description": a.description,
                "has_api_key": bool(a.api_key),
            }
            for a in self._accounts.values()
        ]

    async def close_all(self) -> None:
        for client in self._clients.values():
            await client.close()
        self._clients.clear()
