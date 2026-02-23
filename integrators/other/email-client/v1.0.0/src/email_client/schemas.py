"""Pydantic models for email connector — API request/response schemas."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, EmailStr, Field


class EmailPriority(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"


class Attachment(BaseModel):
    filename: str
    content_type: str = "application/octet-stream"
    content_base64: str = ""
    size_bytes: int = 0


class EmailAddress(BaseModel):
    name: str = ""
    address: str


class EmailMessage(BaseModel):
    message_id: str = ""
    account_name: str = ""
    folder: str = "INBOX"
    subject: str = ""
    sender: EmailAddress | None = None
    recipients: list[EmailAddress] = Field(default_factory=list)
    cc: list[EmailAddress] = Field(default_factory=list)
    bcc: list[EmailAddress] = Field(default_factory=list)
    body_text: str = ""
    body_html: str = ""
    date: datetime | None = None
    is_read: bool = False
    priority: EmailPriority = EmailPriority.NORMAL
    attachments: list[Attachment] = Field(default_factory=list)
    headers: dict[str, str] = Field(default_factory=dict)


class EmailsPage(BaseModel):
    emails: list[EmailMessage] = Field(default_factory=list)
    total: int = 0
    page: int = 1
    page_size: int = 50
    folder: str = "INBOX"


class FolderInfo(BaseModel):
    name: str
    delimiter: str = "/"
    flags: list[str] = Field(default_factory=list)
    message_count: int = 0
    unseen_count: int = 0


class SendEmailRequest(BaseModel):
    to: list[str]
    subject: str
    body_text: str = ""
    body_html: str = ""
    cc: list[str] = Field(default_factory=list)
    bcc: list[str] = Field(default_factory=list)
    priority: EmailPriority = EmailPriority.NORMAL
    attachments: list[Attachment] = Field(default_factory=list)
    reply_to: str | None = None


class SendEmailResponse(BaseModel):
    status: str = "sent"
    message_id: str = ""
    account_name: str = ""


class ConnectionStatus(BaseModel):
    account_name: str
    imap_connected: bool = False
    smtp_connected: bool = False
    last_poll_at: datetime | None = None
    error: str | None = None


class AuthStatusResponse(BaseModel):
    account_name: str
    imap_connected: bool = False
    smtp_connected: bool = False
    last_checked: datetime | None = None
