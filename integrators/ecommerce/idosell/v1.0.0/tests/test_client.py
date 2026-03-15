"""Tests for IdoSell client — covers both api_key and legacy auth modes."""

import hashlib
from datetime import date

from src.config import IdoSellAccountConfig
from src.idosell.auth import IdoSellAuthManager, _sha1
from src.idosell.client import IdoSellClient


class TestIdoSellClient:
    def test_base_url_construction_api_key(self, account_config: IdoSellAccountConfig) -> None:
        auth = IdoSellAuthManager()
        client = IdoSellClient(auth)
        http_client = client._get_http_client(account_config)
        assert str(http_client.base_url) == "https://test.idosell.com/api/admin/v6/"

    def test_base_url_with_trailing_slash(self) -> None:
        account = IdoSellAccountConfig(
            name="test",
            shop_url="https://test.idosell.com/",
            api_key="key",
            api_version="v7",
        )
        auth = IdoSellAuthManager()
        client = IdoSellClient(auth)
        http_client = client._get_http_client(account)
        assert str(http_client.base_url) == "https://test.idosell.com/api/admin/v7/"

    def test_base_url_legacy_mode(self) -> None:
        account = IdoSellAccountConfig(
            name="legacy",
            shop_url="https://test.idosell.com",
            login="admin",
            password="secret",
            auth_mode="legacy",
            api_version="v7",
        )
        auth = IdoSellAuthManager()
        client = IdoSellClient(auth)
        http_client = client._get_http_client(account)
        assert str(http_client.base_url) == "https://test.idosell.com/admin/v7/"


class TestIdoSellAuthManager:
    def test_get_headers_api_key(self, account_config: IdoSellAccountConfig) -> None:
        auth = IdoSellAuthManager()
        headers = auth.get_headers(account_config)
        assert headers["X-API-KEY"] == "test-api-key-12345"
        assert headers["Accept"] == "application/json"
        assert headers["Content-Type"] == "application/json"

    def test_get_headers_legacy_no_api_key(self) -> None:
        account = IdoSellAccountConfig(
            name="legacy",
            shop_url="https://test.idosell.com",
            login="admin",
            password="secret",
            auth_mode="legacy",
            api_version="v7",
        )
        auth = IdoSellAuthManager()
        headers = auth.get_headers(account)
        assert "X-API-KEY" not in headers
        assert headers["Accept"] == "application/json"

    def test_legacy_auth_body(self) -> None:
        account = IdoSellAccountConfig(
            name="legacy",
            shop_url="https://test.idosell.com",
            login="admin",
            password="secret",
            auth_mode="legacy",
            api_version="v7",
        )
        auth = IdoSellAuthManager()
        body = auth.get_legacy_auth_body(account)

        assert body["userLogin"] == "admin"
        assert body["system_login"] == "admin"

        today = date.today().strftime("%Y%m%d")
        expected_key = _sha1(today + _sha1("secret"))
        assert body["authenticateKey"] == expected_key
        assert body["system_key"] == expected_key

    def test_sha1_function(self) -> None:
        result = _sha1("test")
        expected = hashlib.sha1(b"test").hexdigest()
        assert result == expected

    def test_legacy_key_cached_same_day(self) -> None:
        account = IdoSellAccountConfig(
            name="cached",
            shop_url="https://test.idosell.com",
            login="admin",
            password="secret",
            auth_mode="legacy",
            api_version="v7",
        )
        auth = IdoSellAuthManager()
        key1 = auth.get_legacy_auth_body(account)["authenticateKey"]
        key2 = auth.get_legacy_auth_body(account)["authenticateKey"]
        assert key1 == key2

    def test_build_base_url_api_key(self) -> None:
        account = IdoSellAccountConfig(
            name="test",
            shop_url="https://shop.idosell.com",
            api_key="key",
            auth_mode="api_key",
            api_version="v6",
        )
        assert IdoSellAuthManager.build_base_url(account) == "https://shop.idosell.com/api/admin/v6/"

    def test_build_base_url_legacy(self) -> None:
        account = IdoSellAccountConfig(
            name="test",
            shop_url="https://shop.idosell.com/",
            login="admin",
            password="secret",
            auth_mode="legacy",
            api_version="v7",
        )
        assert IdoSellAuthManager.build_base_url(account) == "https://shop.idosell.com/admin/v7/"

    def test_initial_validation_state(self) -> None:
        auth = IdoSellAuthManager()
        assert auth.is_validated("nonexistent") is False

    def test_get_status(self) -> None:
        auth = IdoSellAuthManager()
        status = auth.get_status("test-shop", "v6")
        assert status.account_name == "test-shop"
        assert status.authenticated is False
        assert status.api_version == "v6"
