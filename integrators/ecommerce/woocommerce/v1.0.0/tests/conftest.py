import os

import pytest
from unittest.mock import AsyncMock, MagicMock

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./test_woocommerce.db")
os.environ.setdefault("DATABASE_ENCRYPTION_KEY", "")
os.environ.setdefault("WOOCOMMERCE_SCRAPING_ENABLED", "false")

from src.woocommerce.auth import WooCommerceAuth
from src.woocommerce.client import WooCommerceClient
from src.woocommerce.integration import WooCommerceIntegration
from src.config import WooCommerceAccountConfig
from src.models.database import StateStore
from src.services.account_manager import AccountManager


SANDBOX_ACCOUNT = WooCommerceAccountConfig(
    name="test-store",
    store_url="https://test-store.example.com",
    consumer_key="ck_test_key",
    consumer_secret="cs_test_secret",
    api_version="wc/v3",
    verify_ssl=True,
    environment="sandbox",
)


@pytest.fixture
def account_manager():
    manager = AccountManager()
    manager.add_account(SANDBOX_ACCOUNT)
    return manager


@pytest.fixture
def mock_state_store():
    store = AsyncMock(spec=StateStore)
    store.get_all_states.return_value = {}
    store.get_last_scraped.return_value = None
    return store


@pytest.fixture
def auth():
    woo_auth = WooCommerceAuth()
    woo_auth.register_account(
        SANDBOX_ACCOUNT.name,
        SANDBOX_ACCOUNT.store_url,
        SANDBOX_ACCOUNT.consumer_key,
        SANDBOX_ACCOUNT.consumer_secret,
        SANDBOX_ACCOUNT.api_version,
    )
    return woo_auth


@pytest.fixture
def woo_client(auth):
    return WooCommerceClient(auth)


@pytest.fixture
def integration(woo_client, account_manager):
    return WooCommerceIntegration(woo_client, account_manager)
