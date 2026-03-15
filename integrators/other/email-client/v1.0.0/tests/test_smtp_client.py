"""Tests for SMTP client email sending."""

from src.email_client.schemas import Attachment, EmailPriority, SendEmailRequest
from src.email_client.smtp_client import PRIORITY_HEADERS, SmtpClient


class TestSmtpBuildMessage:
    def setup_method(self) -> None:
        self.smtp = SmtpClient(
            host="smtp.example.com",
            port=587,
            email_address="test@example.com",
            login="test@example.com",
            password="password",
        )

    def test_build_simple_message(self) -> None:
        request = SendEmailRequest(
            to=["recipient@example.com"],
            subject="Test Subject",
            body_text="Hello World",
        )
        msg = self.smtp._build_message(request)
        assert msg["From"] == "test@example.com"
        assert msg["To"] == "recipient@example.com"
        assert msg["Subject"] == "Test Subject"
        assert msg["Message-ID"] is not None
        assert msg["Date"] is not None

    def test_build_message_with_cc(self) -> None:
        request = SendEmailRequest(
            to=["to@example.com"],
            subject="CC Test",
            body_text="Hello",
            cc=["cc1@example.com", "cc2@example.com"],
        )
        msg = self.smtp._build_message(request)
        assert "cc1@example.com" in msg["Cc"]
        assert "cc2@example.com" in msg["Cc"]

    def test_build_message_with_reply_to(self) -> None:
        request = SendEmailRequest(
            to=["to@example.com"],
            subject="Reply Test",
            body_text="Hello",
            reply_to="reply@example.com",
        )
        msg = self.smtp._build_message(request)
        assert msg["Reply-To"] == "reply@example.com"

    def test_build_message_high_priority(self) -> None:
        request = SendEmailRequest(
            to=["to@example.com"],
            subject="Urgent",
            body_text="Important",
            priority=EmailPriority.HIGH,
        )
        msg = self.smtp._build_message(request)
        assert msg["X-Priority"] == "1"
        assert msg["Importance"] == "High"

    def test_build_message_low_priority(self) -> None:
        request = SendEmailRequest(
            to=["to@example.com"],
            subject="Low Priority",
            body_text="Not urgent",
            priority=EmailPriority.LOW,
        )
        msg = self.smtp._build_message(request)
        assert msg["X-Priority"] == "5"
        assert msg["Importance"] == "Low"

    def test_build_message_html_only(self) -> None:
        request = SendEmailRequest(
            to=["to@example.com"],
            subject="HTML Only",
            body_html="<h1>Hello</h1>",
        )
        msg = self.smtp._build_message(request)
        parts = list(msg.walk())
        html_parts = [p for p in parts if p.get_content_type() == "text/html"]
        assert html_parts, "Expected at least one text/html part"
        decoded = html_parts[0].get_payload(decode=True).decode()
        assert "<h1>Hello</h1>" in decoded

    def test_build_message_with_attachment(self) -> None:
        import base64

        content = base64.b64encode(b"test content").decode()
        request = SendEmailRequest(
            to=["to@example.com"],
            subject="Attachment Test",
            body_text="See attached",
            attachments=[
                Attachment(
                    filename="test.txt",
                    content_type="text/plain",
                    content_base64=content,
                    size_bytes=12,
                )
            ],
        )
        msg = self.smtp._build_message(request)
        parts = list(msg.walk())
        filenames = [p.get_filename() for p in parts if p.get_filename()]
        assert "test.txt" in filenames

    def test_build_message_multiple_recipients(self) -> None:
        request = SendEmailRequest(
            to=["a@example.com", "b@example.com"],
            subject="Multi",
            body_text="Hello all",
        )
        msg = self.smtp._build_message(request)
        assert "a@example.com" in msg["To"]
        assert "b@example.com" in msg["To"]

    def test_build_message_empty_body(self) -> None:
        request = SendEmailRequest(
            to=["to@example.com"],
            subject="Empty",
        )
        msg = self.smtp._build_message(request)
        assert msg["Subject"] == "Empty"


class TestPriorityHeaders:
    def test_all_priorities_have_headers(self) -> None:
        for priority in EmailPriority:
            assert priority in PRIORITY_HEADERS

    def test_high_priority_values(self) -> None:
        x_priority, importance = PRIORITY_HEADERS[EmailPriority.HIGH]
        assert x_priority == "1"
        assert importance == "High"

    def test_normal_priority_values(self) -> None:
        x_priority, importance = PRIORITY_HEADERS[EmailPriority.NORMAL]
        assert x_priority == "3"
        assert importance == "Normal"

    def test_low_priority_values(self) -> None:
        x_priority, importance = PRIORITY_HEADERS[EmailPriority.LOW]
        assert x_priority == "5"
        assert importance == "Low"
