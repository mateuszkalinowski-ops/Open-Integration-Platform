"""Tests for AccountManager."""

import pytest

from src.config import FtpAccountConfig
from src.services.account_manager import AccountManager


@pytest.fixture
def manager() -> AccountManager:
    return AccountManager()


def test_add_and_get_account(manager: AccountManager):
    account = FtpAccountConfig(name="my-server", host="sftp.example.com")
    manager.add_account(account)

    result = manager.get_account("my-server")
    assert result is not None
    assert result.host == "sftp.example.com"


def test_get_nonexistent_account_returns_none(manager: AccountManager):
    assert manager.get_account("nonexistent") is None


def test_list_accounts(manager: AccountManager):
    manager.add_account(FtpAccountConfig(name="a", host="a.com"))
    manager.add_account(FtpAccountConfig(name="b", host="b.com"))
    assert len(manager.list_accounts()) == 2


def test_remove_account(manager: AccountManager):
    manager.add_account(FtpAccountConfig(name="removable", host="r.com"))
    assert manager.remove_account("removable") is True
    assert manager.get_account("removable") is None


def test_remove_nonexistent_account_returns_false(manager: AccountManager):
    assert manager.remove_account("ghost") is False


def test_add_account_replaces_existing(manager: AccountManager):
    manager.add_account(FtpAccountConfig(name="dup", host="old.com"))
    manager.add_account(FtpAccountConfig(name="dup", host="new.com"))
    result = manager.get_account("dup")
    assert result is not None
    assert result.host == "new.com"
    assert len(manager.list_accounts()) == 1
