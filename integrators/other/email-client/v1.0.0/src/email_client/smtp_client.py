"""SMTP client for sending emails — async wrapper around smtplib."""

import asyncio
import base64
import logging
import smtplib
import ssl
import time
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr, formatdate, make_msgid
from functools import partial

from src.email_client.schemas import (
    Attachment,
    EmailPriority,
    SendEmailRequest,
    SendEmailResponse,
)
from src.email_client.metrics import metrics

logger = logging.getLogger(__name__)

PRIORITY_HEADERS: dict[EmailPriority, tuple[str, str]] = {
    EmailPriority.HIGH: ("1", "High"),
    EmailPriority.NORMAL: ("3", "Normal"),
    EmailPriority.LOW: ("5", "Low"),
}


class SmtpConnectionError(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class SmtpClient:
    """Async wrapper around smtplib for sending emails via SMTP."""

    def __init__(
        self,
        host: str,
        port: int,
        email_address: str,
        login: str,
        password: str,
        use_ssl: bool = True,
        timeout: float = 30.0,
    ):
        self._host = host
        self._port = port
        self._email = email_address
        self._login = login
        self._password = password
        self._use_ssl = use_ssl
        self._timeout = timeout

    def _build_message(self, request: SendEmailRequest) -> MIMEMultipart:
        msg = MIMEMultipart("mixed")
        msg["From"] = self._email
        msg["To"] = ", ".join(request.to)
        msg["Subject"] = request.subject
        msg["Date"] = formatdate(localtime=True)
        msg["Message-ID"] = make_msgid()

        if request.cc:
            msg["Cc"] = ", ".join(request.cc)
        if request.reply_to:
            msg["Reply-To"] = request.reply_to

        x_priority, importance = PRIORITY_HEADERS.get(
            request.priority, ("3", "Normal"),
        )
        msg["X-Priority"] = x_priority
        msg["Importance"] = importance

        body_part = MIMEMultipart("alternative")
        if request.body_text:
            body_part.attach(MIMEText(request.body_text, "plain", "utf-8"))
        if request.body_html:
            body_part.attach(MIMEText(request.body_html, "html", "utf-8"))
        if not request.body_text and not request.body_html:
            body_part.attach(MIMEText("", "plain", "utf-8"))
        msg.attach(body_part)

        for attachment in request.attachments:
            self._attach_file(msg, attachment)

        return msg

    def _attach_file(self, msg: MIMEMultipart, attachment: Attachment) -> None:
        content = base64.b64decode(attachment.content_base64)
        part = MIMEApplication(content)
        part.add_header(
            "Content-Disposition",
            "attachment",
            filename=attachment.filename,
        )
        part.set_type(attachment.content_type)
        msg.attach(part)

    def _send_sync(self, mime_msg: MIMEMultipart, all_recipients: list[str]) -> None:
        ssl_ctx = ssl.create_default_context()
        if self._use_ssl and self._port == 465:
            server = smtplib.SMTP_SSL(self._host, self._port, timeout=self._timeout, context=ssl_ctx)
        else:
            server = smtplib.SMTP(self._host, self._port, timeout=self._timeout)
            server.ehlo()
            if self._use_ssl:
                server.starttls(context=ssl_ctx)
                server.ehlo()

        try:
            server.login(self._login, self._password)
            server.sendmail(self._email, all_recipients, mime_msg.as_string())
        finally:
            server.quit()

    async def send_email(
        self,
        request: SendEmailRequest,
        account_name: str,
    ) -> SendEmailResponse:
        """Build and send an email via SMTP."""
        mime_msg = self._build_message(request)
        all_recipients = list(request.to) + list(request.cc) + list(request.bcc)

        loop = asyncio.get_event_loop()
        start = time.monotonic()
        try:
            await loop.run_in_executor(
                None,
                partial(self._send_sync, mime_msg, all_recipients),
            )
            duration = time.monotonic() - start
            metrics["external_api_calls_total"].labels(
                system="email_smtp", operation="send", status="ok",
            ).inc()
            metrics["external_api_duration"].labels(
                system="email_smtp", operation="send",
            ).observe(duration)

            message_id = mime_msg["Message-ID"] or ""
            logger.info(
                "Email sent via %s, message_id=%s, recipients=%d",
                account_name, message_id, len(all_recipients),
            )
            return SendEmailResponse(
                status="sent",
                message_id=message_id,
                account_name=account_name,
            )
        except Exception as exc:
            duration = time.monotonic() - start
            metrics["external_api_calls_total"].labels(
                system="email_smtp", operation="send", status="error",
            ).inc()
            metrics["external_api_duration"].labels(
                system="email_smtp", operation="send",
            ).observe(duration)
            raise SmtpConnectionError(f"SMTP send failed: {exc}") from exc

    async def ping(self) -> bool:
        """Test SMTP connectivity by opening and closing a connection."""
        loop = asyncio.get_event_loop()
        try:
            def _test_connection() -> bool:
                ssl_ctx = ssl.create_default_context()
                if self._use_ssl and self._port == 465:
                    server = smtplib.SMTP_SSL(self._host, self._port, timeout=self._timeout, context=ssl_ctx)
                else:
                    server = smtplib.SMTP(self._host, self._port, timeout=self._timeout)
                    server.ehlo()
                    if self._use_ssl:
                        server.starttls(context=ssl_ctx)
                        server.ehlo()
                try:
                    server.login(self._login, self._password)
                finally:
                    try:
                        server.quit()
                    except Exception:
                        server.close()
                return True

            return await loop.run_in_executor(None, _test_connection)
        except Exception:
            return False
