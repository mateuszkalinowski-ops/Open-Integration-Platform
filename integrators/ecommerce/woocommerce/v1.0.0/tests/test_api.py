"""Integration tests for the FastAPI endpoints."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from httpx import AsyncClient, ASGITransport

from src.api.dependencies import app_state
from src.woocommerce.auth import WooCommerceAuth
from src.woocommerce.schemas import AuthStatusResponse
from src.services.account_manager import AccountManager
from src.config import WooCommerceAccountConfig
from pinquark_common.monitoring.health import HealthChecker
from pinquark_common.schemas.common import HealthResponse


@pytest.fixture
def mock_app_state():
    """Prepare a minimal app_state for testing routes without full lifespan."""
    account = WooCommerceAccountConfig(
        name="test",
        store_url="https://test-store.example.com",
        consumer_key="ck_test",
        consumer_secret="cs_test",
        api_version="wc/v3",
        verify_ssl=True,
        environment="sandbox",
    )

    account_manager = AccountManager()
    account_manager.add_account(account)
    app_state.account_manager = account_manager

    auth = WooCommerceAuth()
    auth.register_account(
        account.name, account.store_url, account.consumer_key,
        account.consumer_secret, account.api_version,
    )
    app_state.auth = auth

    health = MagicMock(spec=HealthChecker)
    health.run = AsyncMock(
        return_value=HealthResponse(status="healthy", version="1.0.0", uptime_seconds=10.0),
    )
    app_state.health_checker = health

    app_state.integration = MagicMock()
    app_state.client = MagicMock()

    return app_state


@pytest.fixture
def app(mock_app_state):
    """Create the FastAPI app without running lifespan (routes only)."""
    from fastapi import FastAPI
    from src.api.routes import router

    test_app = FastAPI()
    test_app.include_router(router)
    return test_app


@pytest.mark.asyncio
async def test_health(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"


@pytest.mark.asyncio
async def test_list_accounts(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/accounts")
    assert resp.status_code == 200
    accounts = resp.json()
    assert len(accounts) == 1
    assert accounts[0]["name"] == "test"
    assert accounts[0]["store_url"] == "https://test-store.example.com"


@pytest.mark.asyncio
async def test_auth_status(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/auth/test/status")
    assert resp.status_code == 200
    data = resp.json()
    assert data["account_name"] == "test"
    assert data["authenticated"] is True


@pytest.mark.asyncio
async def test_orders_requires_auth_for_unknown_account(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/orders", params={"account_name": "nonexistent"})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_add_and_remove_account(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/accounts", json={
            "name": "new-store",
            "store_url": "https://new-store.example.com",
            "consumer_key": "ck_new",
            "consumer_secret": "cs_new",
        })
        assert resp.status_code == 201

        resp = await client.get("/accounts")
        names = [a["name"] for a in resp.json()]
        assert "new-store" in names

        resp = await client.delete("/accounts/new-store")
        assert resp.status_code == 200

        resp = await client.get("/accounts")
        names = [a["name"] for a in resp.json()]
        assert "new-store" not in names


@pytest.mark.asyncio
async def test_remove_nonexistent_account(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.delete("/accounts/nonexistent")
    assert resp.status_code == 404
