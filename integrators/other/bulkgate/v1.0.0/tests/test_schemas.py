"""Tests for BulkGate SMS Gateway — Pydantic schemas."""

import pytest
from pydantic import ValidationError
from src.schemas import (
    BulkGateCredentials,
    BulkGateErrorResponse,
    BulkStatusSummary,
    ChannelCascade,
    CheckBalanceRequest,
    CreditBalanceResponse,
    DeliveryReportPayload,
    IncomingSmsPayload,
    SendAdvancedSmsRequest,
    SenderIdType,
    SendPromotionalSmsRequest,
    SendTransactionalSmsRequest,
    SmsChannelObject,
    SmsPartResponse,
    TransactionalSmsResponse,
    ViberChannelObject,
)


class TestBulkGateCredentials:
    def test_valid_credentials(self):
        creds = BulkGateCredentials(application_id="12345", application_token="tok-abc")
        assert creds.application_id == "12345"
        assert creds.application_token == "tok-abc"

    def test_missing_field_raises(self):
        with pytest.raises(ValidationError):
            BulkGateCredentials(application_id="12345")


class TestSenderIdType:
    def test_enum_values(self):
        assert SenderIdType.SYSTEM.value == "gSystem"
        assert SenderIdType.TEXT.value == "gText"
        assert SenderIdType.OWN.value == "gOwn"
        assert SenderIdType.PROFILE.value == "gProfile"
        assert SenderIdType.SHORT_CODE.value == "gShort"


class TestSendTransactionalSmsRequest:
    def test_minimal_request(self):
        req = SendTransactionalSmsRequest(
            credentials=BulkGateCredentials(application_id="1", application_token="t"),
            number="420777777777",
            text="Hello",
        )
        assert req.number == "420777777777"
        assert req.text == "Hello"
        assert req.unicode is False
        assert req.sender_id == SenderIdType.SYSTEM
        assert req.duplicates_check is False

    def test_full_request(self):
        req = SendTransactionalSmsRequest(
            credentials=BulkGateCredentials(application_id="1", application_token="t"),
            number="420777777777",
            text="Unicode test: ěščřžýáíé",
            unicode=True,
            sender_id=SenderIdType.TEXT,
            sender_id_value="MyApp",
            country="CZ",
            schedule="2026-03-01T10:00:00+01:00",
            duplicates_check=True,
            tag="order-123",
        )
        assert req.unicode is True
        assert req.sender_id == SenderIdType.TEXT
        assert req.sender_id_value == "MyApp"
        assert req.country == "CZ"
        assert req.tag == "order-123"


class TestSendPromotionalSmsRequest:
    def test_multiple_recipients(self):
        req = SendPromotionalSmsRequest(
            credentials=BulkGateCredentials(application_id="1", application_token="t"),
            number="420777777777;420888888888;420999999999",
            text="Promo offer!",
        )
        assert ";" in req.number


class TestSendAdvancedSmsRequest:
    def test_with_variables_and_channels(self):
        req = SendAdvancedSmsRequest(
            credentials=BulkGateCredentials(application_id="1", application_token="t"),
            number=["420777777777", "420888888888"],
            text="Hello <first_name>, your order <order_id> is ready.",
            variables={"first_name": "Jan", "order_id": "ORD-456"},
            channel=ChannelCascade(
                sms=SmsChannelObject(sender_id=SenderIdType.TEXT, sender_id_value="Shop", unicode=True),
                viber=ViberChannelObject(sender="MyShop", expiration=120),
            ),
            country="CZ",
        )
        assert len(req.number) == 2
        assert req.variables["first_name"] == "Jan"
        assert req.channel.sms.sender_id == SenderIdType.TEXT
        assert req.channel.viber.sender == "MyShop"

    def test_minimal_advanced(self):
        req = SendAdvancedSmsRequest(
            credentials=BulkGateCredentials(application_id="1", application_token="t"),
            number=["420777777777"],
            text="Simple notification",
        )
        assert req.variables is None
        assert req.channel is None


class TestCheckBalanceRequest:
    def test_request(self):
        req = CheckBalanceRequest(
            credentials=BulkGateCredentials(application_id="1", application_token="t"),
        )
        assert req.credentials.application_id == "1"


class TestResponseSchemas:
    def test_transactional_response(self):
        resp = TransactionalSmsResponse(
            status="accepted",
            sms_id="tmpde1bcd4b1d1",
            part_id=["tmpde1bcd4b1d1_1", "tmpde1bcd4b1d1_2", "tmpde1bcd4b1d1"],
            number="447700900000",
        )
        assert resp.status == "accepted"
        assert len(resp.part_id) == 3

    def test_bulk_status_summary(self):
        summary = BulkStatusSummary(sent=0, accepted=0, scheduled=2, error=1)
        assert summary.scheduled == 2
        assert summary.error == 1

    def test_sms_part_response_success(self):
        part = SmsPartResponse(
            status="scheduled",
            sms_id="idfkvqrp-0",
            part_id=["idfkvqrp-0_1", "idfkvqrp-0_2"],
            number="447700900000",
        )
        assert part.status == "scheduled"

    def test_sms_part_response_error(self):
        part = SmsPartResponse(
            status="error",
            code=9,
            error="Invalid phone number",
            number="44771447678",
        )
        assert part.status == "error"
        assert part.code == 9

    def test_credit_balance_response(self):
        resp = CreditBalanceResponse(
            wallet="bg1805151838000001",
            credit=215.8138,
            currency="credits",
            free_messages=51,
            datetime="2026-02-24T10:00:00+02:00",
        )
        assert resp.credit == 215.8138
        assert resp.free_messages == 51

    def test_error_response(self):
        err = BulkGateErrorResponse(
            type="unknown_identity",
            code=401,
            error="Unknown identity / unauthorized / empty application_id",
        )
        assert err.code == 401


class TestWebhookPayloads:
    def test_delivery_report(self):
        report = DeliveryReportPayload(
            sms_id="abc123",
            number="420777777777",
            status="delivered",
            timestamp="2026-02-24T12:00:00Z",
            price=0.05,
            country="CZ",
        )
        assert report.status == "delivered"

    def test_incoming_sms(self):
        incoming = IncomingSmsPayload(
            sender="420888888888",
            text="STOP",
            timestamp="2026-02-24T12:00:00Z",
            inbox_id="inbox-001",
        )
        assert incoming.text == "STOP"
