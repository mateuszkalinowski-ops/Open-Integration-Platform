import os
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./test_allegro.db")
os.environ.setdefault("DATABASE_ENCRYPTION_KEY", "")
os.environ.setdefault("ALLEGRO_SCRAPING_ENABLED", "false")

from src.allegro.auth import AllegroAuthManager
from src.allegro.client import AllegroClient
from src.allegro.integration import AllegroIntegration
from src.config import AllegroAccountConfig
from src.models.database import TokenStore
from src.services.account_manager import AccountManager


SANDBOX_ACCOUNT = AllegroAccountConfig(
    name="test-sandbox",
    client_id="test-client-id",
    client_secret="test-client-secret",
    api_url="https://api.allegro.pl.allegrosandbox.pl",
    auth_url="https://allegro.pl.allegrosandbox.pl/auth/oauth",
    environment="sandbox",
)


@pytest.fixture
def account_manager():
    manager = AccountManager()
    manager.add_account(SANDBOX_ACCOUNT)
    return manager


@pytest.fixture
def mock_token_store():
    store = AsyncMock(spec=TokenStore)
    store.load_all_tokens.return_value = {}
    store.load_all_last_event_ids.return_value = {}
    return store


@pytest.fixture
def auth_manager(mock_token_store):
    return AllegroAuthManager(mock_token_store)


@pytest.fixture
def allegro_client(auth_manager):
    return AllegroClient(auth_manager)


@pytest.fixture
def integration(allegro_client, account_manager):
    return AllegroIntegration(allegro_client, account_manager)
