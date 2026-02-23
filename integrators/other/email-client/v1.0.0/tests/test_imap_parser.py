"""Tests for IMAP email parsing functions."""

import pytest

from src.email_client.imap_client import (
    _decode_header_value,
    _extract_attachments,
    _extract_body,
    _parse_address,
    _parse_address_list,
    _parse_email_message,
    _parse_priority,
)
from src.email_client.schemas import EmailPriority

import email


class TestDecodeHeaderValue:
    def test_plain_ascii(self) -> None:
        assert _decode_header_value("Hello World") == "Hello World"

    def test_none_returns_empty(self) -> None:
        assert _decode_header_value(None) == ""

    def test_empty_returns_empty(self) -> None:
        assert _decode_header_value("") == ""

    def test_encoded_utf8(self) -> None:
        encoded = "=?utf-8?B?xIZlxZvEhw==?="
        result = _decode_header_value(encoded)
        assert isinstance(result, str)
        assert len(result) > 0


class TestParseAddress:
    def test_full_address(self) -> None:
        result = _parse_address("Test User <test@example.com>")
        assert result is not None
        assert result.address == "test@example.com"
        assert result.name == "Test User"

    def test_bare_address(self) -> None:
        result = _parse_address("<test@example.com>")
        assert result is not None
        assert result.address == "test@example.com"

    def test_none_returns_none(self) -> None:
        assert _parse_address(None) is None

    def test_empty_returns_none(self) -> None:
        assert _parse_address("") is None


class TestParseAddressList:
    def test_multiple_addresses(self) -> None:
        result = _parse_address_list("a@test.com, b@test.com")
        assert len(result) >= 1

    def test_none_returns_empty(self) -> None:
        assert _parse_address_list(None) == []

    def test_empty_returns_empty(self) -> None:
        assert _parse_address_list("") == []


class TestParsePriority:
    def test_high_priority(self, sample_high_priority_email: bytes) -> None:
        msg = email.message_from_bytes(sample_high_priority_email)
        assert _parse_priority(msg) == EmailPriority.HIGH

    def test_normal_priority(self, sample_raw_email: bytes) -> None:
        msg = email.message_from_bytes(sample_raw_email)
        assert _parse_priority(msg) == EmailPriority.NORMAL

    def test_low_priority(self) -> None:
        raw = b"X-Priority: 5\r\nContent-Type: text/plain\r\n\r\ntest"
        msg = email.message_from_bytes(raw)
        assert _parse_priority(msg) == EmailPriority.LOW

    def test_missing_priority_defaults_normal(self) -> None:
        raw = b"Content-Type: text/plain\r\n\r\ntest"
        msg = email.message_from_bytes(raw)
        assert _parse_priority(msg) == EmailPriority.NORMAL


class TestExtractBody:
    def test_plain_text(self, sample_raw_email: bytes) -> None:
        msg = email.message_from_bytes(sample_raw_email)
        body_text, body_html = _extract_body(msg)
        assert "test email body" in body_text
        assert body_html == ""

    def test_multipart(self, sample_raw_email_html: bytes) -> None:
        msg = email.message_from_bytes(sample_raw_email_html)
        body_text, body_html = _extract_body(msg)
        assert "Plain text version" in body_text
        assert "<h1>HTML version</h1>" in body_html


class TestExtractAttachments:
    def test_no_attachments(self, sample_raw_email: bytes) -> None:
        msg = email.message_from_bytes(sample_raw_email)
        attachments = _extract_attachments(msg)
        assert len(attachments) == 0

    def test_with_attachment(self, sample_raw_email_with_attachment: bytes) -> None:
        msg = email.message_from_bytes(sample_raw_email_with_attachment)
        attachments = _extract_attachments(msg)
        assert len(attachments) == 1
        assert attachments[0].filename == "test.pdf"
        assert attachments[0].content_type == "application/pdf"
        assert attachments[0].size_bytes > 0


class TestParseEmailMessage:
    def test_basic_parsing(self, sample_raw_email: bytes) -> None:
        result = _parse_email_message(sample_raw_email, "INBOX", "test-account")
        assert result.message_id == "<test-msg-001@example.com>"
        assert result.subject == "Test Email Subject"
        assert result.account_name == "test-account"
        assert result.folder == "INBOX"
        assert result.sender is not None
        assert result.sender.address == "sender@example.com"
        assert result.sender.name == "Test Sender"
        assert len(result.recipients) >= 1
        assert result.date is not None
        assert result.priority == EmailPriority.NORMAL
        assert "test email body" in result.body_text

    def test_html_email_parsing(self, sample_raw_email_html: bytes) -> None:
        result = _parse_email_message(sample_raw_email_html, "INBOX", "test-account")
        assert result.subject == "HTML Email"
        assert "Plain text version" in result.body_text
        assert "<h1>HTML version</h1>" in result.body_html

    def test_attachment_parsing(self, sample_raw_email_with_attachment: bytes) -> None:
        result = _parse_email_message(sample_raw_email_with_attachment, "Sent", "test-account")
        assert result.subject == "Email with Attachment"
        assert result.folder == "Sent"
        assert len(result.attachments) == 1
        assert result.attachments[0].filename == "test.pdf"

    def test_high_priority_parsing(self, sample_high_priority_email: bytes) -> None:
        result = _parse_email_message(sample_high_priority_email, "INBOX", "test-account")
        assert result.priority == EmailPriority.HIGH
        assert result.subject == "Urgent Message"

    def test_cc_parsing(self, sample_raw_email: bytes) -> None:
        result = _parse_email_message(sample_raw_email, "INBOX", "test-account")
        assert len(result.cc) >= 1
