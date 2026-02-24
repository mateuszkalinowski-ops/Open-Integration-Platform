"""Manages multiple FTP/SFTP server configurations loaded from YAML or environment."""

import logging
import os
from pathlib import Path

import yaml

from src.config import FtpAccountConfig, settings

logger = logging.getLogger(__name__)


class AccountManager:
    """Loads and provides access to FTP/SFTP account configurations."""

    def __init__(self) -> None:
        self._accounts: dict[str, FtpAccountConfig] = {}

    def load_from_yaml(self, path: str | None = None) -> None:
        config_path = Path(path or settings.accounts_config_path)
        if not config_path.exists():
            logger.warning("Accounts config not found at %s, trying environment", config_path)
            self._load_from_env()
            return

        with open(config_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)

        for account_data in data.get("accounts", []):
            account = FtpAccountConfig(**account_data)
            self._accounts[account.name] = account
            logger.info("Loaded account: %s (%s://%s, env=%s)", account.name, account.protocol, account.host, account.environment)

    def _load_from_env(self) -> None:
        idx = 0
        while True:
            prefix = f"FTP_ACCOUNT_{idx}_"
            name = os.getenv(f"{prefix}NAME")
            if not name:
                break
            account = FtpAccountConfig(
                name=name,
                host=os.getenv(f"{prefix}HOST", ""),
                protocol=os.getenv(f"{prefix}PROTOCOL", "sftp"),
                port=int(os.getenv(f"{prefix}PORT", "0")),
                username=os.getenv(f"{prefix}USERNAME", ""),
                password=os.getenv(f"{prefix}PASSWORD", ""),
                private_key=os.getenv(f"{prefix}PRIVATE_KEY", ""),
                passive_mode=os.getenv(f"{prefix}PASSIVE_MODE", "true").lower() in ("true", "1", "yes"),
                base_path=os.getenv(f"{prefix}BASE_PATH", "/"),
                environment=os.getenv(f"{prefix}ENVIRONMENT", "production"),
            )
            self._accounts[name] = account
            logger.info("Loaded account from env: %s (%s://%s)", name, account.protocol, account.host)
            idx += 1

        if not self._accounts:
            logger.warning("No FTP/SFTP accounts configured")

    def get_account(self, name: str) -> FtpAccountConfig | None:
        return self._accounts.get(name)

    def list_accounts(self) -> list[FtpAccountConfig]:
        return list(self._accounts.values())

    def add_account(self, account: FtpAccountConfig) -> None:
        self._accounts[account.name] = account
        logger.info("Added account: %s (%s://%s)", account.name, account.protocol, account.host)

    def remove_account(self, name: str) -> bool:
        removed = self._accounts.pop(name, None)
        if removed:
            logger.info("Removed account: %s", name)
        return removed is not None
