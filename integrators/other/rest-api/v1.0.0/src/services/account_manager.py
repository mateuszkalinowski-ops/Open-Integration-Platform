"""Account manager — manages REST API accounts and their clients."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import yaml

from src.config import settings
from src.schemas.account import AccountConfig, ActionDefinition
from src.services.auth_provider import AuthProvider
from src.services.response_parser import ResponseParser
from src.services.rest_client import RestClient

logger = logging.getLogger(__name__)


class AccountManager:
    """Manages REST API accounts and their HTTP clients."""

    def __init__(self) -> None:
        self._accounts: dict[str, AccountConfig] = {}
        self._clients: dict[str, RestClient] = {}

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
        action_registry_raw = account_data.pop("action_registry", {})
        action_registry: dict[str, ActionDefinition] = {}
        for alias, defn in action_registry_raw.items():
            if isinstance(defn, str):
                action_registry[alias] = ActionDefinition(endpoint=defn)
            elif isinstance(defn, dict):
                action_registry[alias] = ActionDefinition(**defn)

        account_data["action_registry"] = action_registry
        account = AccountConfig(**account_data)
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

    def get_account(self, name: str) -> AccountConfig:
        if name not in self._accounts:
            raise KeyError(f"Account '{name}' not found")
        return self._accounts[name]

    def get_client(self, name: str) -> RestClient:
        if name not in self._accounts:
            raise KeyError(f"Account '{name}' not found")

        if name not in self._clients:
            account = self._accounts[name]
            auth_provider = AuthProvider(account)
            response_parser = ResponseParser(account)
            self._clients[name] = RestClient(
                account=account,
                auth_provider=auth_provider,
                response_parser=response_parser,
            )
        return self._clients[name]

    def update_action_registry(
        self,
        account_name: str,
        actions: dict[str, ActionDefinition],
        *,
        merge: bool = True,
    ) -> None:
        account = self.get_account(account_name)
        if merge:
            account.action_registry.update(actions)
        else:
            account.action_registry = actions

        if account_name in self._clients:
            del self._clients[account_name]

        logger.info(
            "Updated action registry for '%s': %d actions",
            account_name,
            len(account.action_registry),
        )

    def list_accounts(self) -> list[dict[str, Any]]:
        return [
            {
                "name": a.name,
                "description": a.description,
                "base_url": a.base_url,
                "profile": a.profile,
                "actions_count": len(a.action_registry),
                "has_discovery": bool(a.discovery.openapi_url),
            }
            for a in self._accounts.values()
        ]

    def get_account_actions(self, name: str) -> dict[str, dict[str, Any]]:
        account = self.get_account(name)
        return {
            alias: {
                "endpoint": defn.endpoint,
                "method": defn.method or account.default_method,
                "description": defn.description,
                "source": defn.source,
            }
            for alias, defn in account.action_registry.items()
        }

    async def close_all(self) -> None:
        for client in self._clients.values():
            await client.close()
        self._clients.clear()
