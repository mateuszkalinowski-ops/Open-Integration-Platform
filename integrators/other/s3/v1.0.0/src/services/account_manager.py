"""Manages multiple S3 account configurations loaded from YAML or environment."""

import logging
import os
from pathlib import Path

import yaml

from src.config import S3AccountConfig, settings

logger = logging.getLogger(__name__)


class AccountManager:
    """Loads and provides access to S3 account configurations."""

    def __init__(self) -> None:
        self._accounts: dict[str, S3AccountConfig] = {}

    def load_from_yaml(self, path: str | None = None) -> None:
        config_path = Path(path or settings.accounts_config_path)
        if not config_path.exists():
            logger.warning("Accounts config not found at %s, trying environment", config_path)
            self._load_from_env()
            return

        with open(config_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)

        for account_data in data.get("accounts", []):
            account = S3AccountConfig(**account_data)
            self._accounts[account.name] = account
            logger.info(
                "Loaded account: %s (region=%s, endpoint=%s, env=%s)",
                account.name,
                account.region,
                account.endpoint_url or "aws",
                account.environment,
            )

    def _load_from_env(self) -> None:
        idx = 0
        while True:
            prefix = f"S3_ACCOUNT_{idx}_"
            name = os.getenv(f"{prefix}NAME")
            if not name:
                break
            raw_poll_enabled = os.getenv(f"{prefix}POLLING_ENABLED")
            poll_enabled = raw_poll_enabled.lower() in ("true", "1", "yes") if raw_poll_enabled else None
            raw_poll_interval = os.getenv(f"{prefix}POLLING_INTERVAL_SECONDS")
            poll_interval = int(raw_poll_interval) if raw_poll_interval else None

            account = S3AccountConfig(
                name=name,
                aws_access_key_id=os.getenv(f"{prefix}AWS_ACCESS_KEY_ID", ""),
                aws_secret_access_key=os.getenv(f"{prefix}AWS_SECRET_ACCESS_KEY", ""),
                region=os.getenv(f"{prefix}REGION", "us-east-1"),
                endpoint_url=os.getenv(f"{prefix}ENDPOINT_URL", ""),
                default_bucket=os.getenv(f"{prefix}DEFAULT_BUCKET", ""),
                use_path_style=os.getenv(f"{prefix}USE_PATH_STYLE", "false").lower() in ("true", "1", "yes"),
                environment=os.getenv(f"{prefix}ENVIRONMENT", "production"),
                polling_enabled=poll_enabled,
                polling_bucket=os.getenv(f"{prefix}POLLING_BUCKET", ""),
                polling_prefix=os.getenv(f"{prefix}POLLING_PREFIX", ""),
                polling_interval_seconds=poll_interval,
            )
            self._accounts[name] = account
            logger.info(
                "Loaded account from env: %s (region=%s)",
                name,
                account.region,
            )
            idx += 1

        if not self._accounts:
            logger.warning("No S3 accounts configured")

    def get_account(self, name: str) -> S3AccountConfig | None:
        return self._accounts.get(name)

    def list_accounts(self) -> list[S3AccountConfig]:
        return list(self._accounts.values())

    def add_account(self, account: S3AccountConfig) -> None:
        self._accounts[account.name] = account
        logger.info(
            "Added account: %s (region=%s, endpoint=%s)",
            account.name,
            account.region,
            account.endpoint_url or "aws",
        )

    def remove_account(self, name: str) -> bool:
        removed = self._accounts.pop(name, None)
        if removed:
            logger.info("Removed account: %s", name)
        return removed is not None
