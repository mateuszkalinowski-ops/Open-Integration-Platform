"""BulkGate SMS Gateway — request/response schemas.

BulkGate HTTP APIs:
- Simple API v1.0: transactional + promotional SMS (GET/POST)
- Advanced API v2.0: transactional SMS with multi-channel cascade
- Credit balance: POST /api/2.0/advanced/info

Authentication: application_id + application_token per request.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Credentials
# ---------------------------------------------------------------------------


class BulkGateCredentials(BaseModel):
    application_id: str = Field(description="BulkGate Application ID")
    application_token: str = Field(description="BulkGate Application Token")


# ---------------------------------------------------------------------------
# Sender ID
# ---------------------------------------------------------------------------


class SenderIdType(str, Enum):
    SYSTEM = "gSystem"
    SHORT_CODE = "gShort"
    TEXT = "gText"
    MOBILE_CONNECT = "gMobile"
    PUSH = "gPush"
    OWN = "gOwn"
    PROFILE = "gProfile"


# ---------------------------------------------------------------------------
# Simple API — Transactional SMS request
# ---------------------------------------------------------------------------


class SendTransactionalSmsRequest(BaseModel):
    credentials: BulkGateCredentials
    number: str = Field(description="Recipient phone number")
    text: str = Field(description="SMS text (max 612 chars, 268 if unicode)")
    unicode: bool = Field(default=False, description="Send as Unicode SMS")
    sender_id: SenderIdType = Field(default=SenderIdType.SYSTEM, description="Sender ID type")
    sender_id_value: str | None = Field(default=None, description="Sender value for gOwn/gText/gProfile")
    country: str | None = Field(default=None, description="ISO 3166-1 alpha-2 country code")
    schedule: str | None = Field(default=None, description="Scheduled time (unix timestamp or ISO 8601)")
    duplicates_check: bool = Field(default=False, description="Prevent duplicate messages within 5 min")
    tag: str | None = Field(default=None, description="Message label for retrieval")


# ---------------------------------------------------------------------------
# Simple API — Promotional (Bulk) SMS request
# ---------------------------------------------------------------------------


class SendPromotionalSmsRequest(BaseModel):
    credentials: BulkGateCredentials
    number: str = Field(description="Recipient numbers separated by semicolon")
    text: str = Field(description="SMS text (max 612 chars, 268 if unicode)")
    unicode: bool = Field(default=False, description="Send as Unicode SMS")
    sender_id: SenderIdType = Field(default=SenderIdType.SYSTEM, description="Sender ID type")
    sender_id_value: str | None = Field(default=None, description="Sender value")
    country: str | None = Field(default=None, description="ISO 3166-1 alpha-2 country code")
    schedule: str | None = Field(default=None, description="Scheduled time (unix timestamp or ISO 8601)")
    duplicates_check: bool = Field(default=False, description="Prevent duplicate messages")
    tag: str | None = Field(default=None, description="Message label for retrieval")


# ---------------------------------------------------------------------------
# Advanced API v2.0 — SMS channel object
# ---------------------------------------------------------------------------


class SmsChannelObject(BaseModel):
    text: str | None = Field(default=None, description="SMS text override")
    sender_id: SenderIdType = Field(default=SenderIdType.SYSTEM, description="Sender ID type")
    sender_id_value: str | None = Field(default=None, description="Sender value")
    unicode: bool = Field(default=False, description="Unicode SMS")


class ViberChannelObject(BaseModel):
    text: str | None = Field(default=None, description="Viber message text override")
    sender: str = Field(description="Viber sender name")
    expiration: int = Field(default=120, description="Fallback timeout in seconds")


class ChannelCascade(BaseModel):
    sms: SmsChannelObject | None = None
    viber: ViberChannelObject | None = None


# ---------------------------------------------------------------------------
# Advanced API v2.0 — Transactional SMS request
# ---------------------------------------------------------------------------


class SendAdvancedSmsRequest(BaseModel):
    credentials: BulkGateCredentials
    number: list[str] = Field(description="Recipient number(s)")
    text: str = Field(description="SMS text with optional <variable> placeholders")
    variables: dict[str, str] | None = Field(default=None, description="Template variables")
    channel: ChannelCascade | None = Field(default=None, description="Multi-channel cascade config")
    country: str | None = Field(default=None, description="ISO 3166-1 alpha-2 country code")
    schedule: str | None = Field(default=None, description="Scheduled time (unix timestamp or ISO 8601)")
    duplicates_check: bool = Field(default=False, description="Prevent duplicate messages")
    tag: str | None = Field(default=None, description="Message label for retrieval")


# ---------------------------------------------------------------------------
# Credit balance request
# ---------------------------------------------------------------------------


class CheckBalanceRequest(BaseModel):
    credentials: BulkGateCredentials


# ---------------------------------------------------------------------------
# BulkGate API responses
# ---------------------------------------------------------------------------


class SmsPartResponse(BaseModel):
    status: str
    sms_id: str | None = Field(default=None)
    message_id: str | None = Field(default=None)
    part_id: list[str] | None = Field(default=None)
    number: str | None = Field(default=None)
    channel: str | None = Field(default=None)
    code: int | None = Field(default=None)
    error: str | None = Field(default=None)


class BulkStatusSummary(BaseModel):
    sent: int = 0
    accepted: int = 0
    scheduled: int = 0
    error: int = 0
    blacklisted: int = 0
    invalid_number: int = 0
    invalid_sender: int = 0
    duplicity_message: int = 0


class TransactionalSmsResponse(BaseModel):
    status: str
    sms_id: str | None = Field(default=None)
    part_id: list[str] | None = Field(default=None)
    number: str | None = Field(default=None)


class BulkSmsResponse(BaseModel):
    total: dict[str, BulkStatusSummary]
    response: list[SmsPartResponse]


class CreditBalanceResponse(BaseModel):
    wallet: str
    credit: float
    currency: str
    free_messages: int = 0
    datetime: str


class BulkGateErrorResponse(BaseModel):
    type: str
    code: int
    error: str
    detail: str | None = None


# ---------------------------------------------------------------------------
# Webhook payload — delivery reports
# ---------------------------------------------------------------------------


class DeliveryReportPayload(BaseModel):
    sms_id: str | None = Field(default=None)
    number: str | None = Field(default=None)
    status: str | None = Field(default=None)
    timestamp: str | None = Field(default=None)
    price: float | None = Field(default=None)
    country: str | None = Field(default=None)


class IncomingSmsPayload(BaseModel):
    sender: str | None = Field(default=None)
    text: str | None = Field(default=None)
    timestamp: str | None = Field(default=None)
    inbox_id: str | None = Field(default=None)
