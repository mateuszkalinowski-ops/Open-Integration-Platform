"""Tests for AccountManager."""

from src.config import S3AccountConfig
from src.services.account_manager import AccountManager


def test_add_and_get_account():
    manager = AccountManager()
    account = S3AccountConfig(
        name="test",
        aws_access_key_id="AKIAEXAMPLE",
        aws_secret_access_key="secretkey",
        region="eu-central-1",
    )
    manager.add_account(account)
    retrieved = manager.get_account("test")
    assert retrieved is not None
    assert retrieved.name == "test"
    assert retrieved.region == "eu-central-1"


def test_list_accounts():
    manager = AccountManager()
    manager.add_account(S3AccountConfig(
        name="a", aws_access_key_id="k1", aws_secret_access_key="s1",
    ))
    manager.add_account(S3AccountConfig(
        name="b", aws_access_key_id="k2", aws_secret_access_key="s2",
    ))
    assert len(manager.list_accounts()) == 2


def test_remove_account():
    manager = AccountManager()
    manager.add_account(S3AccountConfig(
        name="temp", aws_access_key_id="k", aws_secret_access_key="s",
    ))
    assert manager.remove_account("temp") is True
    assert manager.get_account("temp") is None


def test_remove_nonexistent_account():
    manager = AccountManager()
    assert manager.remove_account("ghost") is False


def test_get_nonexistent_account():
    manager = AccountManager()
    assert manager.get_account("nope") is None


def test_account_defaults():
    account = S3AccountConfig(
        name="defaults-test",
        aws_access_key_id="k",
        aws_secret_access_key="s",
    )
    assert account.region == "us-east-1"
    assert account.endpoint_url == ""
    assert account.default_bucket == ""
    assert account.use_path_style is False
    assert account.environment == "production"
