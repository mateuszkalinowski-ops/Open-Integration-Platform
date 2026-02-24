"""Tests for configuration and account settings."""

from src.config import FtpAccountConfig


def test_sftp_account_default_port():
    account = FtpAccountConfig(name="test", host="host.com", protocol="sftp")
    assert account.effective_port == 22


def test_ftp_account_default_port():
    account = FtpAccountConfig(name="test", host="host.com", protocol="ftp")
    assert account.effective_port == 21


def test_custom_port_overrides_default():
    account = FtpAccountConfig(name="test", host="host.com", protocol="sftp", port=2222)
    assert account.effective_port == 2222


def test_account_defaults():
    account = FtpAccountConfig(name="test", host="host.com")
    assert account.protocol == "sftp"
    assert account.passive_mode is True
    assert account.base_path == "/"
    assert account.environment == "production"
    assert account.username == ""
    assert account.password == ""
    assert account.private_key == ""
