"""Tests for BulkGate SMS Gateway — API client (mocked external calls)."""

from unittest.mock import AsyncMock, patch

import httpx
import pytest
from src.api import BulkGateApiClient
from src.schemas import (
    BulkGateCredentials,
    ChannelCascade,
    SenderIdType,
    SmsChannelObject,
    ViberChannelObject,
)


@pytest.fixture
def credentials():
    return BulkGateCredentials(application_id="test-app-id", application_token="test-token")


@pytest.fixture
def api_client():
    return BulkGateApiClient()


TRANSACTIONAL_SUCCESS = {
    "data": {
        "status": "accepted",
        "sms_id": "tmpde1bcd4b1d1",
        "part_id": ["tmpde1bcd4b1d1_1", "tmpde1bcd4b1d1"],
        "number": "420777777777",
    }
}

PROMOTIONAL_SUCCESS = {
    "data": {
        "total": {"status": {"sent": 0, "accepted": 0, "scheduled": 2, "error": 0}},
        "response": [
            {"status": "scheduled", "sms_id": "id-0", "part_id": ["id-0"], "number": "420777777777"},
            {"status": "scheduled", "sms_id": "id-1", "part_id": ["id-1"], "number": "420888888888"},
        ],
    }
}

ADVANCED_SUCCESS = {
    "data": {
        "total": {"status": {"sent": 0, "accepted": 0, "scheduled": 1, "error": 0}},
        "response": [
            {
                "status": "scheduled",
                "message_id": "transactional-abc-0",
                "part_id": ["transactional-abc-0"],
                "number": "420777777777",
                "channel": "sms",
            }
        ],
    }
}

BALANCE_SUCCESS = {
    "data": {
        "wallet": "bg1805151838000001",
        "credit": 215.8138,
        "currency": "credits",
        "free_messages": 51,
        "datetime": "2026-02-24T10:00:00+02:00",
    }
}

AUTH_ERROR = {"type": "unknown_identity", "code": 401, "error": "Unknown identity", "detail": None}


def _mock_response(json_data: dict, status_code: int = 200) -> httpx.Response:
    resp = httpx.Response(status_code=status_code, json=json_data, request=httpx.Request("POST", "https://test.com"))
    return resp


@pytest.mark.asyncio
class TestSendTransactionalSms:
    async def test_success(self, api_client, credentials):
        with patch.object(api_client._client, "post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = _mock_response(TRANSACTIONAL_SUCCESS)
            result, status = await api_client.send_transactional_sms(
                credentials,
                "420777777777",
                "Test message",
            )
            assert status == 200
            assert result["data"]["status"] == "accepted"
            mock_post.assert_called_once()

    async def test_with_all_options(self, api_client, credentials):
        with patch.object(api_client._client, "post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = _mock_response(TRANSACTIONAL_SUCCESS)
            _result, status = await api_client.send_transactional_sms(
                credentials,
                "420777777777",
                "Unicode: ěščřž",
                unicode=True,
                sender_id=SenderIdType.TEXT,
                sender_id_value="MyApp",
                country="CZ",
                schedule="2026-03-01T10:00:00+01:00",
                duplicates_check=True,
                tag="test-tag",
            )
            assert status == 200
            call_kwargs = mock_post.call_args
            payload = call_kwargs.kwargs.get("json") or call_kwargs[1].get("json")
            assert payload["unicode"] is True
            assert payload["sender_id"] == "gText"
            assert payload["duplicates_check"] == "on"
            assert payload["tag"] == "test-tag"

    async def test_auth_error(self, api_client, credentials):
        with patch.object(api_client._client, "post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = _mock_response(AUTH_ERROR, status_code=401)
            mock_post.return_value.raise_for_status = lambda: (_ for _ in ()).throw(
                httpx.HTTPStatusError(
                    "401",
                    request=httpx.Request("POST", "https://test.com"),
                    response=mock_post.return_value,
                )
            )
            _result, status = await api_client.send_transactional_sms(
                credentials,
                "420777777777",
                "Test",
            )
            assert status == 401

    async def test_timeout_handling(self, api_client, credentials):
        with patch.object(api_client._client, "post", new_callable=AsyncMock) as mock_post:
            mock_post.side_effect = httpx.TimeoutException("Connection timed out")
            result, status = await api_client.send_transactional_sms(
                credentials,
                "420777777777",
                "Test",
            )
            assert status == 504
            assert result["error"]["code"] == "TIMEOUT"


@pytest.mark.asyncio
class TestSendPromotionalSms:
    async def test_success(self, api_client, credentials):
        with patch.object(api_client._client, "post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = _mock_response(PROMOTIONAL_SUCCESS)
            result, status = await api_client.send_promotional_sms(
                credentials,
                "420777777777;420888888888",
                "Bulk promo!",
            )
            assert status == 200
            assert result["data"]["total"]["status"]["scheduled"] == 2


@pytest.mark.asyncio
class TestSendAdvancedTransactional:
    async def test_success_with_channels(self, api_client, credentials):
        with patch.object(api_client._client, "post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = _mock_response(ADVANCED_SUCCESS)
            channel = ChannelCascade(
                sms=SmsChannelObject(sender_id=SenderIdType.TEXT, sender_id_value="Shop"),
                viber=ViberChannelObject(sender="Shop", expiration=100),
            )
            _result, status = await api_client.send_advanced_transactional(
                credentials,
                ["420777777777"],
                "Hello <first_name>",
                variables={"first_name": "Jan"},
                channel=channel,
                country="CZ",
            )
            assert status == 200
            call_kwargs = mock_post.call_args
            payload = call_kwargs.kwargs.get("json") or call_kwargs[1].get("json")
            assert "channel" in payload
            assert payload["channel"]["sms"]["sender_id"] == "gText"
            assert payload["channel"]["viber"]["sender"] == "Shop"
            assert payload["variables"]["first_name"] == "Jan"


@pytest.mark.asyncio
class TestCheckCreditBalance:
    async def test_success(self, api_client, credentials):
        with patch.object(api_client._client, "post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = _mock_response(BALANCE_SUCCESS)
            result, status = await api_client.check_credit_balance(credentials)
            assert status == 200
            assert result["data"]["credit"] == 215.8138
            assert result["data"]["free_messages"] == 51
