"""IdoSell authentication — supports both modern API key and legacy SHA-1 modes.

Modern (api_key mode):
  - X-API-KEY header, generated in IdoSell admin panel
  - URL pattern: /api/admin/{version}/
  - No refresh needed

Legacy (legacy mode):
  - SHA-1 daily key: sha1(YYYYMMDD + sha1(password))
  - Sent as 'authenticate' object in the JSON request body
  - URL pattern: /admin/{version}/
  - Key regenerated daily at midnight
  - Ported from Java IdoAuth.java
"""

import hashlib
import logging
from datetime import date

import httpx

from src.config import IdoSellAccountConfig, settings
from src.idosell.schemas import IdoSellAuthStatus

logger = logging.getLogger(__name__)


def _sha1(value: str) -> str:
    return hashlib.sha1(value.encode("utf-8")).hexdigest()


class IdoSellAuthManager:
    """Manages authentication for IdoSell accounts (api_key + legacy SHA-1)."""

    def __init__(self) -> None:
        self._validated: dict[str, bool] = {}
        self._legacy_keys: dict[str, tuple[str, str]] = {}

    # ------------------------------------------------------------------
    # Modern: X-API-KEY header
    # ------------------------------------------------------------------

    def get_headers(self, account: IdoSellAccountConfig) -> dict[str, str]:
        headers: dict[str, str] = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        if account.auth_mode == "api_key" and account.api_key:
            headers["X-API-KEY"] = account.api_key
        return headers

    # ------------------------------------------------------------------
    # Legacy: SHA-1 daily key (ported from Java IdoAuth.java)
    # ------------------------------------------------------------------

    def get_legacy_auth_body(self, account: IdoSellAccountConfig) -> dict[str, str]:
        """Build the 'authenticate' block for legacy request body auth.

        Key = sha1(YYYYMMDD + sha1(password)), regenerated daily.
        """
        key = self._get_or_generate_legacy_key(account)
        return {
            "userLogin": account.login,
            "system_login": account.login,
            "authenticateKey": key,
            "system_key": key,
        }

    def _get_or_generate_legacy_key(self, account: IdoSellAccountConfig) -> str:
        today = date.today().strftime("%Y%m%d")
        cached = self._legacy_keys.get(account.name)
        if cached and cached[0] == today:
            return cached[1]
        key = _sha1(today + _sha1(account.password))
        self._legacy_keys[account.name] = (today, key)
        logger.info("Generated legacy SHA-1 key for account=%s (date=%s)", account.name, today)
        return key

    # ------------------------------------------------------------------
    # URL pattern
    # ------------------------------------------------------------------

    @staticmethod
    def build_base_url(account: IdoSellAccountConfig) -> str:
        shop = account.shop_url.rstrip("/")
        if account.auth_mode == "legacy":
            return f"{shop}/admin/{account.api_version}/"
        return f"{shop}/api/admin/{account.api_version}/"

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    async def validate(self, account: IdoSellAccountConfig) -> bool:
        base_url = self.build_base_url(account)
        url = f"{base_url}system/shops"

        try:
            headers = self.get_headers(account)
            body = None
            if account.auth_mode == "legacy":
                body = {"authenticate": self.get_legacy_auth_body(account)}

            async with httpx.AsyncClient(timeout=settings.http_connect_timeout) as client:
                if body:
                    response = await client.post(url, headers=headers, json=body)
                else:
                    response = await client.get(url, headers=headers)

            if response.status_code == 200:
                data = response.json()
                errors = data.get("errors", {})
                if isinstance(errors, dict) and errors.get("faultCode", 0) == 0:
                    self._validated[account.name] = True
                    logger.info("Auth validated for account=%s (mode=%s)", account.name, account.auth_mode)
                    return True
                elif isinstance(errors, dict) and errors.get("faultCode") == 1:
                    logger.warning("Auth failed for account=%s: login error", account.name)
                    self._validated[account.name] = False
                    return False

                self._validated[account.name] = True
                return True

            logger.warning(
                "Auth validation failed for account=%s, status=%d",
                account.name,
                response.status_code,
            )
            self._validated[account.name] = False
            return False
        except httpx.HTTPError as exc:
            logger.error("Auth validation error for account=%s: %s", account.name, exc)
            self._validated[account.name] = False
            return False

    def is_validated(self, account_name: str) -> bool:
        return self._validated.get(account_name, False)

    def get_status(self, account_name: str, api_version: str = "") -> IdoSellAuthStatus:
        return IdoSellAuthStatus(
            account_name=account_name,
            authenticated=self.is_validated(account_name),
            api_version=api_version,
        )
