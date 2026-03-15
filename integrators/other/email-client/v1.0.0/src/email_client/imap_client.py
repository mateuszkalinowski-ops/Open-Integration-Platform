"""IMAP client for receiving emails — async wrapper around imaplib."""

import asyncio
import base64
import email
import email.header
import email.utils
import imaplib
import logging
import ssl
import time
from datetime import UTC, datetime
from email.message import Message
from functools import partial

from src.email_client.metrics import metrics
from src.email_client.schemas import (
    Attachment,
    EmailAddress,
    EmailMessage,
    EmailPriority,
    EmailsPage,
    FolderInfo,
)

logger = logging.getLogger(__name__)


def _decode_header_value(raw: str | None) -> str:
    if not raw:
        return ""
    decoded_parts: list[str] = []
    for part, charset in email.header.decode_header(raw):
        if isinstance(part, bytes):
            decoded_parts.append(part.decode(charset or "utf-8", errors="replace"))
        else:
            decoded_parts.append(part)
    return " ".join(decoded_parts)


def _parse_address(raw: str | None) -> EmailAddress | None:
    if not raw:
        return None
    name, addr = email.utils.parseaddr(raw)
    if not addr:
        return None
    return EmailAddress(name=_decode_header_value(name) if name else "", address=addr)


def _parse_address_list(raw: str | None) -> list[EmailAddress]:
    if not raw:
        return []
    result: list[EmailAddress] = []
    for _, addr in email.utils.getaddresses([raw]):
        if addr:
            parsed = _parse_address(f"<{addr}>")
            if parsed:
                result.append(parsed)
    return result


def _parse_priority(msg: Message) -> EmailPriority:
    priority_header = msg.get("X-Priority", "3")
    try:
        level = int(priority_header.strip()[0])
    except (ValueError, IndexError):
        return EmailPriority.NORMAL
    if level <= 2:
        return EmailPriority.HIGH
    if level >= 4:
        return EmailPriority.LOW
    return EmailPriority.NORMAL


def _extract_body(msg: Message) -> tuple[str, str]:
    """Extract plain text and HTML body from email message."""
    body_text = ""
    body_html = ""

    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            disposition = str(part.get("Content-Disposition", ""))
            if "attachment" in disposition:
                continue
            payload = part.get_payload(decode=True)
            if payload is None:
                continue
            charset = part.get_content_charset() or "utf-8"
            decoded = payload.decode(charset, errors="replace")
            if content_type == "text/plain" and not body_text:
                body_text = decoded
            elif content_type == "text/html" and not body_html:
                body_html = decoded
    else:
        payload = msg.get_payload(decode=True)
        if payload:
            charset = msg.get_content_charset() or "utf-8"
            decoded = payload.decode(charset, errors="replace")
            if msg.get_content_type() == "text/html":
                body_html = decoded
            else:
                body_text = decoded

    return body_text, body_html


def _extract_attachments(msg: Message) -> list[Attachment]:
    attachments: list[Attachment] = []
    if not msg.is_multipart():
        return attachments

    for part in msg.walk():
        disposition = str(part.get("Content-Disposition", ""))
        if "attachment" not in disposition and "inline" not in disposition:
            continue
        if part.get_content_maintype() == "multipart":
            continue

        filename = part.get_filename()
        filename = _decode_header_value(filename) if filename else f"attachment_{len(attachments)}"

        payload = part.get_payload(decode=True)
        if payload is None:
            continue

        attachments.append(
            Attachment(
                filename=filename,
                content_type=part.get_content_type(),
                content_base64=base64.b64encode(payload).decode("ascii"),
                size_bytes=len(payload),
            )
        )

    return attachments


def _parse_email_message(raw_data: bytes, folder: str, account_name: str) -> EmailMessage:
    """Parse raw email bytes into an EmailMessage model."""
    msg = email.message_from_bytes(raw_data)

    date_str = msg.get("Date")
    date_parsed: datetime | None = None
    if date_str:
        date_tuple = email.utils.parsedate_to_datetime(date_str)
        date_parsed = date_tuple.astimezone(UTC) if date_tuple else None

    body_text, body_html = _extract_body(msg)
    attachments = _extract_attachments(msg)

    return EmailMessage(
        message_id=msg.get("Message-ID", ""),
        account_name=account_name,
        folder=folder,
        subject=_decode_header_value(msg.get("Subject")),
        sender=_parse_address(msg.get("From")),
        recipients=_parse_address_list(msg.get("To")),
        cc=_parse_address_list(msg.get("Cc")),
        body_text=body_text,
        body_html=body_html,
        date=date_parsed,
        is_read=False,
        priority=_parse_priority(msg),
        attachments=attachments,
        headers={k: _decode_header_value(v) for k, v in msg.items()[:20]},
    )


class ImapConnectionError(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class ImapClient:
    """Async wrapper around imaplib.IMAP4_SSL for email retrieval."""

    def __init__(
        self,
        host: str,
        port: int,
        login: str,
        password: str,
        use_ssl: bool = True,
        timeout: float = 30.0,
    ):
        self._host = host
        self._port = port
        self._login = login
        self._password = password
        self._use_ssl = use_ssl
        self._timeout = timeout
        self._connection: imaplib.IMAP4_SSL | imaplib.IMAP4 | None = None

    async def connect(self) -> None:
        loop = asyncio.get_event_loop()
        start = time.monotonic()
        try:
            if self._use_ssl:
                ssl_ctx = ssl.create_default_context()
                self._connection = await loop.run_in_executor(
                    None,
                    partial(imaplib.IMAP4_SSL, self._host, self._port, timeout=self._timeout, ssl_context=ssl_ctx),
                )
            else:
                self._connection = await loop.run_in_executor(
                    None,
                    partial(imaplib.IMAP4, self._host, self._port, timeout=self._timeout),
                )
            await loop.run_in_executor(
                None,
                partial(self._connection.login, self._login, self._password),
            )
            duration = time.monotonic() - start
            metrics["external_api_calls_total"].labels(
                system="email_imap",
                operation="connect",
                status="ok",
            ).inc()
            metrics["external_api_duration"].labels(
                system="email_imap",
                operation="connect",
            ).observe(duration)
            logger.info("IMAP connected to %s:%d", self._host, self._port)
        except Exception as exc:
            duration = time.monotonic() - start
            metrics["external_api_calls_total"].labels(
                system="email_imap",
                operation="connect",
                status="error",
            ).inc()
            metrics["external_api_duration"].labels(
                system="email_imap",
                operation="connect",
            ).observe(duration)
            raise ImapConnectionError(f"IMAP connection failed: {exc}") from exc

    async def disconnect(self) -> None:
        if self._connection:
            loop = asyncio.get_event_loop()
            try:
                await loop.run_in_executor(None, self._connection.logout)
            except Exception:
                logger.debug("IMAP logout error (ignored)")
            finally:
                self._connection = None

    def is_connected(self) -> bool:
        return self._connection is not None

    async def _ensure_connected(self) -> None:
        if not self._connection:
            await self.connect()

    async def list_folders(self, account_name: str) -> list[FolderInfo]:
        await self._ensure_connected()
        assert self._connection is not None
        loop = asyncio.get_event_loop()

        start = time.monotonic()
        _status, folder_data = await loop.run_in_executor(None, self._connection.list)
        duration = time.monotonic() - start
        metrics["external_api_calls_total"].labels(
            system="email_imap",
            operation="list_folders",
            status="ok",
        ).inc()
        metrics["external_api_duration"].labels(
            system="email_imap",
            operation="list_folders",
        ).observe(duration)

        folders: list[FolderInfo] = []
        if not folder_data:
            return folders

        for item in folder_data:
            if isinstance(item, bytes):
                decoded = item.decode("utf-8", errors="replace")
                parts = decoded.split(' "/" ')
                if len(parts) == 2:
                    flags_part = parts[0].strip("()")
                    name = parts[1].strip().strip('"')
                    flags = [f.strip() for f in flags_part.split() if f.strip()]
                    folders.append(FolderInfo(name=name, delimiter="/", flags=flags))

        return folders

    async def fetch_emails(
        self,
        folder: str,
        account_name: str,
        since: datetime | None = None,
        max_count: int = 50,
        unseen_only: bool = False,
    ) -> EmailsPage:
        await self._ensure_connected()
        assert self._connection is not None
        loop = asyncio.get_event_loop()

        await loop.run_in_executor(None, partial(self._connection.select, folder))

        search_criteria = "UNSEEN" if unseen_only else "ALL"
        if since:
            date_str = since.strftime("%d-%b-%Y")
            search_criteria = f"(SINCE {date_str}{' UNSEEN' if unseen_only else ''})"

        start = time.monotonic()
        status, msg_ids_raw = await loop.run_in_executor(
            None,
            partial(self._connection.search, None, search_criteria),
        )
        duration = time.monotonic() - start
        metrics["external_api_calls_total"].labels(
            system="email_imap",
            operation="search",
            status=status,
        ).inc()
        metrics["external_api_duration"].labels(
            system="email_imap",
            operation="search",
        ).observe(duration)

        if status != "OK" or not msg_ids_raw or not msg_ids_raw[0]:
            return EmailsPage(folder=folder, total=0)

        msg_ids = msg_ids_raw[0].split()
        total = len(msg_ids)
        msg_ids = msg_ids[-max_count:]

        emails: list[EmailMessage] = []
        for msg_id in msg_ids:
            try:
                fetch_start = time.monotonic()
                status, data = await loop.run_in_executor(
                    None,
                    partial(self._connection.fetch, msg_id, "(RFC822)"),
                )
                fetch_duration = time.monotonic() - fetch_start
                metrics["external_api_calls_total"].labels(
                    system="email_imap",
                    operation="fetch",
                    status=status,
                ).inc()
                metrics["external_api_duration"].labels(
                    system="email_imap",
                    operation="fetch",
                ).observe(fetch_duration)

                if status == "OK" and data and data[0] and isinstance(data[0], tuple):
                    raw_email = data[0][1]
                    parsed = _parse_email_message(raw_email, folder, account_name)
                    emails.append(parsed)
            except Exception:
                logger.exception("Error fetching email uid=%s", msg_id)

        return EmailsPage(
            emails=emails,
            total=total,
            page=1,
            page_size=max_count,
            folder=folder,
        )

    async def get_email(self, folder: str, message_uid: str, account_name: str) -> EmailMessage | None:
        await self._ensure_connected()
        assert self._connection is not None
        loop = asyncio.get_event_loop()

        await loop.run_in_executor(None, partial(self._connection.select, folder))

        status, data = await loop.run_in_executor(
            None,
            partial(self._connection.fetch, message_uid.encode(), "(RFC822)"),
        )

        if status != "OK" or not data or not data[0] or not isinstance(data[0], tuple):
            return None

        return _parse_email_message(data[0][1], folder, account_name)

    async def mark_as_read(self, folder: str, message_uid: str) -> bool:
        await self._ensure_connected()
        assert self._connection is not None
        loop = asyncio.get_event_loop()

        await loop.run_in_executor(None, partial(self._connection.select, folder))
        status, _ = await loop.run_in_executor(
            None,
            partial(self._connection.store, message_uid.encode(), "+FLAGS", "\\Seen"),
        )
        return status == "OK"

    async def delete_email(self, folder: str, message_uid: str) -> bool:
        await self._ensure_connected()
        assert self._connection is not None
        loop = asyncio.get_event_loop()

        await loop.run_in_executor(None, partial(self._connection.select, folder))
        status, _ = await loop.run_in_executor(
            None,
            partial(self._connection.store, message_uid.encode(), "+FLAGS", "\\Deleted"),
        )
        if status == "OK":
            await loop.run_in_executor(None, self._connection.expunge)
            return True
        return False

    async def ping(self) -> bool:
        """Check IMAP connection health with a NOOP command."""
        if not self._connection:
            return False
        try:
            loop = asyncio.get_event_loop()
            status, _ = await loop.run_in_executor(None, self._connection.noop)
            return status == "OK"
        except Exception:
            return False
