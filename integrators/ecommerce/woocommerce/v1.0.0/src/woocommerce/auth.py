"""WooCommerce authentication — API key based (consumer_key / consumer_secret).

WooCommerce supports two authentication methods:
- HTTPS: Basic Auth with consumer_key:consumer_secret
- HTTP: OAuth 1.0a with HMAC-SHA256 signature

This module implements both, selecting automatically based on the store URL scheme.
The OAuth 1.0a implementation follows the reference Java code from the existing integration.
"""

import hashlib
import hmac
import logging
import time
import urllib.parse
import uuid

from src.woocommerce.schemas import AuthStatusResponse

logger = logging.getLogger(__name__)


class WooCommerceAuth:
    """Manages authentication for multiple WooCommerce stores."""

    def __init__(self) -> None:
        self._accounts: dict[str, dict[str, str]] = {}

    def register_account(
        self,
        account_name: str,
        store_url: str,
        consumer_key: str,
        consumer_secret: str,
        api_version: str = "wc/v3",
    ) -> None:
        self._accounts[account_name] = {
            "store_url": store_url.rstrip("/"),
            "consumer_key": consumer_key,
            "consumer_secret": consumer_secret,
            "api_version": api_version,
        }
        logger.info("Registered auth for account=%s, store=%s", account_name, store_url)

    def remove_account(self, account_name: str) -> None:
        self._accounts.pop(account_name, None)

    def is_authenticated(self, account_name: str) -> bool:
        return account_name in self._accounts

    def get_base_url(self, account_name: str) -> str:
        account = self._accounts[account_name]
        return f"{account['store_url']}/wp-json/{account['api_version']}"

    def get_auth_params(self, account_name: str, method: str, url: str) -> dict[str, str] | None:
        """Get query parameters for OAuth 1.0a (HTTP only). Returns None for HTTPS (uses basic auth)."""
        account = self._accounts[account_name]
        if url.startswith("https"):
            return None
        return self._build_oauth_params(
            method, url, account["consumer_key"], account["consumer_secret"],
        )

    def get_basic_auth(self, account_name: str) -> tuple[str, str] | None:
        """Get basic auth tuple for HTTPS connections."""
        account = self._accounts[account_name]
        store_url = account["store_url"]
        if store_url.startswith("https"):
            return (account["consumer_key"], account["consumer_secret"])
        return None

    def get_status(self, account_name: str) -> AuthStatusResponse:
        account = self._accounts.get(account_name)
        return AuthStatusResponse(
            account_name=account_name,
            authenticated=account is not None,
            store_url=account["store_url"] if account else "",
            api_version=account["api_version"] if account else "",
        )

    @staticmethod
    def _build_oauth_params(
        method: str,
        url: str,
        consumer_key: str,
        consumer_secret: str,
    ) -> dict[str, str]:
        """Build OAuth 1.0a query parameters with HMAC-SHA256 signature."""
        timestamp = str(int(time.time()))
        nonce = uuid.uuid4().hex

        oauth_params: dict[str, str] = {
            "oauth_consumer_key": consumer_key,
            "oauth_nonce": nonce,
            "oauth_signature_method": "HMAC-SHA256",
            "oauth_timestamp": timestamp,
        }

        parsed = urllib.parse.urlparse(url)
        existing_params = urllib.parse.parse_qs(parsed.query, keep_blank_values=True)

        all_params: dict[str, str] = {}
        for k, v_list in existing_params.items():
            all_params[k] = v_list[0] if v_list else ""
        all_params.update(oauth_params)

        sorted_params = sorted(all_params.items())
        param_string = "&".join(
            f"{_percent_encode(k)}={_percent_encode(v)}" for k, v in sorted_params
        )

        base_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        signature_base = f"{method.upper()}&{_percent_encode(base_url)}&{_percent_encode(param_string)}"

        signing_key = f"{_percent_encode(consumer_secret)}&"
        signature = hmac.new(
            signing_key.encode("utf-8"),
            signature_base.encode("utf-8"),
            hashlib.sha256,
        ).digest()

        import base64
        oauth_params["oauth_signature"] = base64.b64encode(signature).decode("utf-8")
        return oauth_params


def _percent_encode(value: str) -> str:
    """RFC 5849 percent-encoding."""
    return urllib.parse.quote(str(value), safe="")
