"""Tests for BulkGate SMS Gateway — FastAPI endpoints (integration tests with mocked API)."""

from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from src.app import app

TRANSACTIONAL_SUCCESS = {
    "data": {
        "status": "accepted",
        "sms_id": "tmpde1bcd4b1d1",
        "part_id": ["tmpde1bcd4b1d1_1", "tmpde1bcd4b1d1"],
        "number": "420777777777",
    }
}

BALANCE_SUCCESS = {
    "data": {
        "wallet": "bg001",
        "credit": 100.0,
        "currency": "credits",
        "free_messages": 10,
        "datetime": "2026-02-24T10:00:00+02:00",
    }
}


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
class TestHealthEndpoints:
    async def test_health(self, client):
        resp = await client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"
        assert data["version"] == "1.0.0"
        assert data["system"] == "bulkgate-sms-gateway"

    async def test_readiness(self, client):
        resp = await client.get("/readiness")
        assert resp.status_code == 200


@pytest.mark.asyncio
class TestSmsEndpoints:
    @patch("src.app._get_client")
    async def test_send_transactional(self, mock_get_client, client):
        mock_api = AsyncMock()
        mock_api.send_transactional_sms.return_value = (TRANSACTIONAL_SUCCESS, 200)
        mock_get_client.return_value = mock_api

        resp = await client.post(
            "/sms/transactional",
            json={
                "credentials": {"application_id": "1", "application_token": "t"},
                "number": "420777777777",
                "text": "Hello from tests",
            },
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["status"] == "accepted"

    @patch("src.app._get_client")
    async def test_send_promotional(self, mock_get_client, client):
        mock_api = AsyncMock()
        mock_api.send_promotional_sms.return_value = ({"data": {"total": {"status": {"scheduled": 2}}}}, 200)
        mock_get_client.return_value = mock_api

        resp = await client.post(
            "/sms/promotional",
            json={
                "credentials": {"application_id": "1", "application_token": "t"},
                "number": "420777777777;420888888888",
                "text": "Promo offer",
            },
        )
        assert resp.status_code == 200

    @patch("src.app._get_client")
    async def test_send_advanced(self, mock_get_client, client):
        mock_api = AsyncMock()
        mock_api.send_advanced_transactional.return_value = ({"data": {"total": {"status": {"scheduled": 1}}}}, 200)
        mock_get_client.return_value = mock_api

        resp = await client.post(
            "/sms/advanced",
            json={
                "credentials": {"application_id": "1", "application_token": "t"},
                "number": ["420777777777"],
                "text": "Hello <name>",
                "variables": {"name": "Jan"},
            },
        )
        assert resp.status_code == 200

    @patch("src.app._get_client")
    async def test_send_transactional_api_error(self, mock_get_client, client):
        mock_api = AsyncMock()
        mock_api.send_transactional_sms.return_value = (
            {"type": "invalid_phone_number", "code": 400, "error": "Invalid phone number"},
            400,
        )
        mock_get_client.return_value = mock_api

        resp = await client.post(
            "/sms/transactional",
            json={
                "credentials": {"application_id": "1", "application_token": "t"},
                "number": "invalid",
                "text": "Test",
            },
        )
        assert resp.status_code == 400

    async def test_send_transactional_missing_fields(self, client):
        resp = await client.post(
            "/sms/transactional",
            json={
                "credentials": {"application_id": "1", "application_token": "t"},
            },
        )
        assert resp.status_code == 422


@pytest.mark.asyncio
class TestAccountEndpoints:
    @patch("src.app._get_client")
    async def test_check_balance(self, mock_get_client, client):
        mock_api = AsyncMock()
        mock_api.check_credit_balance.return_value = (BALANCE_SUCCESS, 200)
        mock_get_client.return_value = mock_api

        resp = await client.post(
            "/account/balance",
            json={
                "credentials": {"application_id": "1", "application_token": "t"},
            },
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["credit"] == 100.0


@pytest.mark.asyncio
class TestWebhookEndpoints:
    async def test_delivery_report_webhook(self, client):
        resp = await client.post(
            "/webhooks/delivery-report",
            json={
                "sms_id": "abc123",
                "number": "420777777777",
                "status": "delivered",
                "timestamp": "2026-02-24T12:00:00Z",
            },
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "received"

    async def test_incoming_sms_webhook(self, client):
        resp = await client.post(
            "/webhooks/incoming-sms",
            json={
                "sender": "420888888888",
                "text": "Reply message",
                "timestamp": "2026-02-24T12:00:00Z",
            },
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "received"
