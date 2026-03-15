"""Tests for SkanujFakture account manager."""

import pytest
from src.config import SkanujFaktureAccountConfig
from src.services.account_manager import AccountManager


@pytest.fixture
def manager():
    return AccountManager()


@pytest.fixture
def sample_account():
    return SkanujFaktureAccountConfig(
        name="test-account",
        login="user@example.com",
        password="secret",
        api_url="https://skanujfakture.pl:8443/SFApi",
    )


class TestAccountManager:
    def test_add_account(self, manager: AccountManager, sample_account: SkanujFaktureAccountConfig) -> None:
        manager.add_account(sample_account)
        assert manager.get_account("test-account") is not None

    def test_list_accounts(self, manager: AccountManager, sample_account: SkanujFaktureAccountConfig) -> None:
        manager.add_account(sample_account)
        accounts = manager.list_accounts()
        assert len(accounts) == 1
        assert accounts[0].name == "test-account"

    def test_get_account_nonexistent(self, manager: AccountManager) -> None:
        assert manager.get_account("nonexistent") is None

    def test_remove_account(self, manager: AccountManager, sample_account: SkanujFaktureAccountConfig) -> None:
        manager.add_account(sample_account)
        assert manager.remove_account("test-account")
        assert manager.get_account("test-account") is None

    def test_remove_nonexistent_account(self, manager: AccountManager) -> None:
        assert not manager.remove_account("nonexistent")

    def test_add_multiple_accounts(self, manager: AccountManager) -> None:
        a1 = SkanujFaktureAccountConfig(name="acc-1", login="a@b.com", password="p1", api_url="https://example.com/api")
        a2 = SkanujFaktureAccountConfig(name="acc-2", login="c@d.com", password="p2", api_url="https://example.com/api")
        manager.add_account(a1)
        manager.add_account(a2)
        assert len(manager.list_accounts()) == 2

    def test_overwrite_account(self, manager: AccountManager) -> None:
        a1 = SkanujFaktureAccountConfig(name="dup", login="old@test.com", password="p1", api_url="https://example.com/api")
        a2 = SkanujFaktureAccountConfig(name="dup", login="new@test.com", password="p2", api_url="https://example.com/api")
        manager.add_account(a1)
        manager.add_account(a2)
        assert len(manager.list_accounts()) == 1
        assert manager.get_account("dup").login == "new@test.com"
