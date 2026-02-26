"""Manages on-premise agent account configurations."""

import logging
import os
from pathlib import Path

import yaml

from src.config import settings
from src.models.schemas import AgentAccount
from src.services.agent_proxy import AgentProxy

logger = logging.getLogger(__name__)


class AccountManager:
    def __init__(self) -> None:
        self._accounts: dict[str, AgentAccount] = {}
        self._proxies: dict[str, AgentProxy] = {}

    def load_from_yaml(self, path: str | None = None) -> None:
        config_path = Path(path or settings.accounts_config_path)
        if not config_path.exists():
            logger.warning("Accounts config not found at %s, trying environment", config_path)
            self._load_from_env()
            return

        with open(config_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)

        for account_data in data.get("accounts", []):
            account = AgentAccount(**account_data)
            self._accounts[account.name] = account
            self._proxies[account.name] = AgentProxy(
                agent_url=account.agent_url,
                agent_api_key=account.agent_api_key,
            )
            logger.info("Loaded agent account: %s (url=%s)", account.name, account.agent_url)

    def _load_from_env(self) -> None:
        idx = 0
        while True:
            prefix = f"NEXO_AGENT_{idx}_"
            name = os.getenv(f"{prefix}NAME")
            if not name:
                break
            account = AgentAccount(
                name=name,
                agent_url=os.getenv(f"{prefix}URL", ""),
                agent_api_key=os.getenv(f"{prefix}API_KEY", ""),
                environment=os.getenv(f"{prefix}ENVIRONMENT", "production"),
            )
            self._accounts[name] = account
            self._proxies[name] = AgentProxy(
                agent_url=account.agent_url,
                agent_api_key=account.agent_api_key,
            )
            logger.info("Loaded agent account from env: %s", name)
            idx += 1

    def get_account(self, name: str) -> AgentAccount | None:
        return self._accounts.get(name)

    def get_proxy(self, name: str) -> AgentProxy | None:
        return self._proxies.get(name)

    def list_accounts(self) -> list[AgentAccount]:
        return list(self._accounts.values())

    async def close_all(self) -> None:
        for proxy in self._proxies.values():
            await proxy.close()
