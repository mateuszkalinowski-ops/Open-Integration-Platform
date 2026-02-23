"""Manages multiple email account configurations loaded from YAML or environment."""

import logging
import os
from pathlib import Path

import yaml

from src.config import EmailAccountConfig, settings

logger = logging.getLogger(__name__)


class AccountManager:
    """Loads and provides access to email account configurations."""

    def __init__(self) -> None:
        self._accounts: dict[str, EmailAccountConfig] = {}

    def load_from_yaml(self, path: str | None = None) -> None:
        config_path = Path(path or settings.accounts_config_path)
        if not config_path.exists():
            logger.warning("Accounts config not found at %s, trying environment", config_path)
            self._load_from_env()
            return

        with open(config_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)

        for account_data in data.get("accounts", []):
            account = EmailAccountConfig(**account_data)
            self._accounts[account.name] = account
            logger.info("Loaded account: %s (env=%s)", account.name, account.environment)

    def _load_from_env(self) -> None:
        idx = 0
        while True:
            prefix = f"EMAIL_ACCOUNT_{idx}_"
            name = os.getenv(f"{prefix}NAME")
            if not name:
                break
            account = EmailAccountConfig(
                name=name,
                email_address=os.getenv(f"{prefix}EMAIL_ADDRESS", ""),
                username=os.getenv(f"{prefix}USERNAME", ""),
                password=os.getenv(f"{prefix}PASSWORD", ""),
                imap_host=os.getenv(f"{prefix}IMAP_HOST", ""),
                imap_port=int(os.getenv(f"{prefix}IMAP_PORT", "993")),
                smtp_host=os.getenv(f"{prefix}SMTP_HOST", ""),
                smtp_port=int(os.getenv(f"{prefix}SMTP_PORT", "587")),
                use_ssl=os.getenv(f"{prefix}USE_SSL", "true").lower() == "true",
                polling_folder=os.getenv(f"{prefix}POLLING_FOLDER", "INBOX"),
                environment=os.getenv(f"{prefix}ENVIRONMENT", "production"),
            )
            self._accounts[name] = account
            logger.info("Loaded account from env: %s", name)
            idx += 1

        if not self._accounts:
            logger.warning("No email accounts configured")

    def get_account(self, name: str) -> EmailAccountConfig | None:
        return self._accounts.get(name)

    def list_accounts(self) -> list[EmailAccountConfig]:
        return list(self._accounts.values())

    def add_account(self, account: EmailAccountConfig) -> None:
        self._accounts[account.name] = account
        logger.info("Added account: %s", account.name)

    def remove_account(self, name: str) -> bool:
        removed = self._accounts.pop(name, None)
        if removed:
            logger.info("Removed account: %s", name)
        return removed is not None
