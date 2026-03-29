"""Account manager for KSeF connector — manages multiple NIP accounts."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import yaml

from src.config import KSeFAccountConfig, KSeFEnvironment, settings
from src.ksef.client import KSeFClient

logger = logging.getLogger(__name__)


class AccountManager:
    """Manages KSeF accounts and their API clients."""

    def __init__(self) -> None:
        self._accounts: dict[str, KSeFAccountConfig] = {}
        self._clients: dict[str, KSeFClient] = {}
        self._background_tasks: set[object] = set()

    def load_from_yaml(self) -> None:
        """Load accounts from YAML configuration file."""
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

    def add_account(self, account_data: dict[str, Any]) -> KSeFAccountConfig:
        """Add or update an account from a dict."""
        env_str = account_data.get("environment", settings.default_environment.value)
        if isinstance(env_str, str):
            env_str = env_str.lower()

        account = KSeFAccountConfig(
            name=account_data["name"],
            nip=account_data["nip"],
            ksef_token=account_data.get("ksef_token", ""),
            environment=KSeFEnvironment(env_str),
            certificate_path=account_data.get("certificate_path", ""),
            certificate_password=account_data.get("certificate_password", ""),
            company_name=account_data.get("company_name", ""),
        )
        self._accounts[account.name] = account

        if account.name in self._clients:
            old_client = self._clients.pop(account.name)
            import asyncio

            try:
                loop = asyncio.get_running_loop()
                task = loop.create_task(old_client.close())
                self._background_tasks.add(task)
                task.add_done_callback(self._background_tasks.discard)
            except RuntimeError:
                pass

        logger.info(
            "Account '%s' added (NIP=%s***, env=%s)",
            account.name,
            account.nip[:6],
            account.environment.value,
        )
        return account

    def get_account(self, name: str) -> KSeFAccountConfig:
        if name not in self._accounts:
            raise KeyError(f"Account '{name}' not found")
        return self._accounts[name]

    def get_client(self, name: str) -> KSeFClient:
        if name not in self._clients:
            account = self.get_account(name)
            self._clients[name] = KSeFClient(account)
        return self._clients[name]

    def list_accounts(self) -> list[KSeFAccountConfig]:
        return list(self._accounts.values())

    def remove_account(self, name: str) -> None:
        self._accounts.pop(name, None)
        client = self._clients.pop(name, None)
        if client:
            import asyncio

            try:
                loop = asyncio.get_running_loop()
                task = loop.create_task(client.close())
                self._background_tasks.add(task)
                task.add_done_callback(self._background_tasks.discard)
            except RuntimeError:
                pass

    async def close_all(self) -> None:
        for client in self._clients.values():
            await client.close()
        self._clients.clear()
