"""Tests for email account manager."""

import pytest

from src.config import EmailAccountConfig
from src.services.account_manager import AccountManager


class TestAccountManager:
    def setup_method(self) -> None:
        self.manager = AccountManager()

    def test_initially_empty(self) -> None:
        assert len(self.manager.list_accounts()) == 0

    def test_add_account(self) -> None:
        account = EmailAccountConfig(
            name="test",
            email_address="test@example.com",
            password="pass",
            imap_host="imap.example.com",
            smtp_host="smtp.example.com",
        )
        self.manager.add_account(account)
        assert len(self.manager.list_accounts()) == 1
        assert self.manager.get_account("test") is not None

    def test_get_nonexistent_account(self) -> None:
        assert self.manager.get_account("nonexistent") is None

    def test_remove_account(self) -> None:
        account = EmailAccountConfig(
            name="to-remove",
            email_address="remove@example.com",
            password="pass",
            imap_host="imap.example.com",
            smtp_host="smtp.example.com",
        )
        self.manager.add_account(account)
        assert self.manager.remove_account("to-remove")
        assert self.manager.get_account("to-remove") is None

    def test_remove_nonexistent_returns_false(self) -> None:
        assert not self.manager.remove_account("nonexistent")

    def test_list_accounts(self) -> None:
        for i in range(3):
            account = EmailAccountConfig(
                name=f"account-{i}",
                email_address=f"user{i}@example.com",
                password="pass",
                imap_host="imap.example.com",
                smtp_host="smtp.example.com",
            )
            self.manager.add_account(account)
        assert len(self.manager.list_accounts()) == 3

    def test_add_duplicate_overwrites(self) -> None:
        account1 = EmailAccountConfig(
            name="dup",
            email_address="old@example.com",
            password="pass",
            imap_host="imap.example.com",
            smtp_host="smtp.example.com",
        )
        account2 = EmailAccountConfig(
            name="dup",
            email_address="new@example.com",
            password="pass",
            imap_host="imap.example.com",
            smtp_host="smtp.example.com",
        )
        self.manager.add_account(account1)
        self.manager.add_account(account2)
        assert len(self.manager.list_accounts()) == 1
        assert self.manager.get_account("dup").email_address == "new@example.com"

    def test_account_default_values(self) -> None:
        account = EmailAccountConfig(
            name="defaults",
            email_address="test@example.com",
            password="pass",
            imap_host="imap.example.com",
            smtp_host="smtp.example.com",
        )
        assert account.imap_port == 993
        assert account.smtp_port == 587
        assert account.use_ssl is True
        assert account.polling_folder == "INBOX"
        assert account.environment == "production"
