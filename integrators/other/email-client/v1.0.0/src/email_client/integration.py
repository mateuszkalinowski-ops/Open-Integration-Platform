"""Email integration layer — orchestrates IMAP and SMTP operations per account."""

import contextlib
import logging
from datetime import datetime

from src.config import EmailAccountConfig
from src.email_client.imap_client import ImapClient
from src.email_client.schemas import (
    AuthStatusResponse,
    ConnectionStatus,
    EmailMessage,
    EmailsPage,
    FolderInfo,
    SendEmailRequest,
    SendEmailResponse,
)
from src.email_client.smtp_client import SmtpClient
from src.services.account_manager import AccountManager

logger = logging.getLogger(__name__)


class EmailIntegration:
    """Facade over IMAP/SMTP operations with multi-account support."""

    def __init__(self, account_manager: AccountManager):
        self._accounts = account_manager
        self._imap_clients: dict[str, ImapClient] = {}
        self._smtp_clients: dict[str, SmtpClient] = {}

    def _get_imap_client(self, account: EmailAccountConfig) -> ImapClient:
        if account.name not in self._imap_clients:
            self._imap_clients[account.name] = ImapClient(
                host=account.imap_host,
                port=account.imap_port,
                login=account.login,
                password=account.password,
                use_ssl=account.use_ssl,
            )
        return self._imap_clients[account.name]

    def _get_smtp_client(self, account: EmailAccountConfig) -> SmtpClient:
        if account.name not in self._smtp_clients:
            self._smtp_clients[account.name] = SmtpClient(
                host=account.smtp_host,
                port=account.smtp_port,
                email_address=account.email_address,
                login=account.login,
                password=account.password,
                use_ssl=account.use_ssl,
            )
        return self._smtp_clients[account.name]

    async def invalidate_clients(self, account_name: str) -> None:
        """Drop cached IMAP/SMTP clients so next call reconnects with fresh credentials."""
        imap = self._imap_clients.pop(account_name, None)
        if imap:
            with contextlib.suppress(Exception):
                await imap.disconnect()
        self._smtp_clients.pop(account_name, None)

    def _require_account(self, account_name: str) -> EmailAccountConfig:
        account = self._accounts.get_account(account_name)
        if not account:
            raise ValueError(f"Account '{account_name}' not found")
        return account

    async def fetch_emails(
        self,
        account_name: str,
        folder: str = "INBOX",
        since: datetime | None = None,
        max_count: int = 50,
        unseen_only: bool = False,
    ) -> EmailsPage:
        account = self._require_account(account_name)
        imap = self._get_imap_client(account)
        return await imap.fetch_emails(folder, account_name, since, max_count, unseen_only)

    async def get_email(
        self,
        account_name: str,
        message_uid: str,
        folder: str = "INBOX",
    ) -> EmailMessage | None:
        account = self._require_account(account_name)
        imap = self._get_imap_client(account)
        return await imap.get_email(folder, message_uid, account_name)

    async def list_folders(self, account_name: str) -> list[FolderInfo]:
        account = self._require_account(account_name)
        imap = self._get_imap_client(account)
        return await imap.list_folders(account_name)

    async def mark_as_read(
        self,
        account_name: str,
        message_uid: str,
        folder: str = "INBOX",
    ) -> bool:
        account = self._require_account(account_name)
        imap = self._get_imap_client(account)
        return await imap.mark_as_read(folder, message_uid)

    async def delete_email(
        self,
        account_name: str,
        message_uid: str,
        folder: str = "INBOX",
    ) -> bool:
        account = self._require_account(account_name)
        imap = self._get_imap_client(account)
        return await imap.delete_email(folder, message_uid)

    async def send_email(
        self,
        account_name: str,
        request: SendEmailRequest,
    ) -> SendEmailResponse:
        account = self._require_account(account_name)
        smtp = self._get_smtp_client(account)
        return await smtp.send_email(request, account_name)

    async def get_connection_status(self, account_name: str) -> ConnectionStatus:
        account = self._require_account(account_name)
        imap = self._get_imap_client(account)
        smtp = self._get_smtp_client(account)

        imap_ok = await imap.ping()
        smtp_ok = await smtp.ping()

        return ConnectionStatus(
            account_name=account_name,
            imap_connected=imap_ok,
            smtp_connected=smtp_ok,
        )

    def get_auth_status(self, account_name: str) -> AuthStatusResponse:
        imap = self._imap_clients.get(account_name)
        _smtp = self._smtp_clients.get(account_name)
        return AuthStatusResponse(
            account_name=account_name,
            imap_connected=imap.is_connected() if imap else False,
            smtp_connected=bool(_smtp),
        )

    async def close(self) -> None:
        for imap in self._imap_clients.values():
            await imap.disconnect()
        self._imap_clients.clear()
        self._smtp_clients.clear()
