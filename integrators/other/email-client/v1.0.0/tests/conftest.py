"""Shared test fixtures for Email Client integrator tests."""

import os

import pytest

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./test.db")
os.environ.setdefault("EMAIL_POLLING_ENABLED", "false")
os.environ.setdefault("KAFKA_ENABLED", "false")


@pytest.fixture
def sample_raw_email() -> bytes:
    return (
        b"From: Test Sender <sender@example.com>\r\n"
        b"To: recipient@example.com\r\n"
        b"Cc: cc@example.com\r\n"
        b"Subject: Test Email Subject\r\n"
        b"Date: Thu, 20 Feb 2026 10:30:00 +0000\r\n"
        b"Message-ID: <test-msg-001@example.com>\r\n"
        b"X-Priority: 3\r\n"
        b"MIME-Version: 1.0\r\n"
        b"Content-Type: text/plain; charset=utf-8\r\n"
        b"\r\n"
        b"Hello, this is a test email body.\r\n"
    )


@pytest.fixture
def sample_raw_email_html() -> bytes:
    return (
        b"From: HTML Sender <html@example.com>\r\n"
        b"To: recipient@example.com\r\n"
        b"Subject: HTML Email\r\n"
        b"Date: Thu, 20 Feb 2026 11:00:00 +0000\r\n"
        b"Message-ID: <test-msg-002@example.com>\r\n"
        b"MIME-Version: 1.0\r\n"
        b'Content-Type: multipart/alternative; boundary="boundary123"\r\n'
        b"\r\n"
        b"--boundary123\r\n"
        b"Content-Type: text/plain; charset=utf-8\r\n"
        b"\r\n"
        b"Plain text version\r\n"
        b"--boundary123\r\n"
        b"Content-Type: text/html; charset=utf-8\r\n"
        b"\r\n"
        b"<html><body><h1>HTML version</h1></body></html>\r\n"
        b"--boundary123--\r\n"
    )


@pytest.fixture
def sample_raw_email_with_attachment() -> bytes:
    return (
        b"From: Attach Sender <attach@example.com>\r\n"
        b"To: recipient@example.com\r\n"
        b"Subject: Email with Attachment\r\n"
        b"Date: Thu, 20 Feb 2026 12:00:00 +0000\r\n"
        b"Message-ID: <test-msg-003@example.com>\r\n"
        b"MIME-Version: 1.0\r\n"
        b'Content-Type: multipart/mixed; boundary="mixbound"\r\n'
        b"\r\n"
        b"--mixbound\r\n"
        b"Content-Type: text/plain; charset=utf-8\r\n"
        b"\r\n"
        b"Email with attachment\r\n"
        b"--mixbound\r\n"
        b"Content-Type: application/pdf\r\n"
        b'Content-Disposition: attachment; filename="test.pdf"\r\n'
        b"Content-Transfer-Encoding: base64\r\n"
        b"\r\n"
        b"dGVzdCBwZGYgY29udGVudA==\r\n"
        b"--mixbound--\r\n"
    )


@pytest.fixture
def sample_high_priority_email() -> bytes:
    return (
        b"From: urgent@example.com\r\n"
        b"To: recipient@example.com\r\n"
        b"Subject: Urgent Message\r\n"
        b"Date: Thu, 20 Feb 2026 14:00:00 +0000\r\n"
        b"Message-ID: <test-msg-004@example.com>\r\n"
        b"X-Priority: 1\r\n"
        b"Content-Type: text/plain; charset=utf-8\r\n"
        b"\r\n"
        b"This is urgent!\r\n"
    )
