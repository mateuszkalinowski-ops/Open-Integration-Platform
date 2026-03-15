"""Shopify authentication management.

Shopify custom apps use a permanent Admin API access token provided in the
store configuration. This module manages tokens per-account and provides
a simple validation mechanism via a lightweight API call.
"""

import logging

import httpx

from src.config import ShopifyAccountConfig, settings
from src.models.database import TokenStore
from src.shopify.schemas import AuthStatusResponse

logger = logging.getLogger(__name__)


class ShopifyAuthManager:
    """Manages access tokens for multiple Shopify stores."""

    def __init__(self, token_store: TokenStore) -> None:
        self._token_store = token_store
        self._validated_accounts: set[str] = set()

    async def initialize(self) -> None:
        """Load previously validated accounts from database."""
        saved = await self._token_store.load_all_tokens()
        for account_name, data in saved.items():
            if data.get("validated"):
                self._validated_accounts.add(account_name)
                logger.info("Restored validated state for account=%s", account_name)

    def is_authenticated(self, account_name: str) -> bool:
        return account_name in self._validated_accounts

    async def validate_credentials(self, account: ShopifyAccountConfig) -> bool:
        """Validate access token by calling Shopify shop.json endpoint."""
        base_url = self._build_base_url(account).rstrip("/")
        url = f"{base_url}/shop.json"

        try:
            async with httpx.AsyncClient(timeout=settings.http_connect_timeout) as client:
                response = await client.get(
                    url,
                    headers={"X-Shopify-Access-Token": account.access_token},
                )
                if response.status_code == 200:
                    self._validated_accounts.add(account.name)
                    await self._token_store.save_token(account.name, {"validated": True, "shop_url": account.shop_url})
                    logger.info("Credentials validated for account=%s", account.name)
                    return True

                logger.warning(
                    "Credential validation failed for account=%s, status=%d",
                    account.name,
                    response.status_code,
                )
                return False
        except httpx.HTTPError:
            logger.exception("HTTP error validating credentials for account=%s", account.name)
            return False

    def mark_authenticated(self, account_name: str) -> None:
        """Mark account as authenticated without validation (used when token is from config)."""
        self._validated_accounts.add(account_name)

    def get_access_token(self, account: ShopifyAccountConfig) -> str:
        """Return access token from account config."""
        return account.access_token

    def get_status(self, account_name: str, account: ShopifyAccountConfig | None = None) -> AuthStatusResponse:
        return AuthStatusResponse(
            account_name=account_name,
            authenticated=self.is_authenticated(account_name),
            shop_url=account.shop_url if account else "",
            api_version=account.api_version if account else "",
        )

    @staticmethod
    def _build_base_url(account: ShopifyAccountConfig) -> str:
        shop_url = account.shop_url.rstrip("/")
        if not shop_url.startswith("https://"):
            shop_url = f"https://{shop_url}"
        return f"{shop_url}/admin/api/{account.api_version}/"
