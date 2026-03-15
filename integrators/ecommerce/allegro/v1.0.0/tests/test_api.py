"""Integration tests for the FastAPI endpoints."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import ASGITransport, AsyncClient
from pinquark_common.monitoring.health import HealthChecker
from pinquark_common.schemas.common import HealthResponse
from src.allegro.auth import AllegroAuthManager
from src.allegro.schemas import AuthStatusResponse
from src.api.dependencies import app_state
from src.config import AllegroAccountConfig
from src.services.account_manager import AccountManager


@pytest.fixture
def mock_app_state():
    """Prepare a minimal app_state for testing routes without full lifespan."""
    account = AllegroAccountConfig(
        name="test",
        client_id="cid",
        client_secret="cs",
        api_url="https://api.allegro.pl.allegrosandbox.pl",
        auth_url="https://allegro.pl.allegrosandbox.pl/auth/oauth",
        environment="sandbox",
    )

    account_manager = AccountManager()
    account_manager.add_account(account)
    app_state.account_manager = account_manager

    auth_manager = MagicMock(spec=AllegroAuthManager)
    auth_manager.is_authenticated.return_value = False
    auth_manager.get_status.return_value = AuthStatusResponse(
        account_name="test",
        authenticated=False,
    )
    app_state.auth_manager = auth_manager

    health = MagicMock(spec=HealthChecker)
    health.run = AsyncMock(return_value=HealthResponse(status="healthy", version="1.0.0", uptime_seconds=10.0))
    app_state.health_checker = health

    app_state.integration = MagicMock()

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


@pytest.mark.asyncio
async def test_auth_status(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/auth/test/status")
    assert resp.status_code == 200
    data = resp.json()
    assert data["account_name"] == "test"
    assert data["authenticated"] is False


@pytest.mark.asyncio
async def test_orders_requires_auth(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/orders", params={"account_name": "test"})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_add_and_remove_account(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/accounts",
            json={
                "name": "new-shop",
                "client_id": "new-cid",
                "client_secret": "new-cs",
            },
        )
        assert resp.status_code == 201

        resp = await client.get("/accounts")
        names = [a["name"] for a in resp.json()]
        assert "new-shop" in names

        resp = await client.delete("/accounts/new-shop")
        assert resp.status_code == 200

        resp = await client.get("/accounts")
        names = [a["name"] for a in resp.json()]
        assert "new-shop" not in names
