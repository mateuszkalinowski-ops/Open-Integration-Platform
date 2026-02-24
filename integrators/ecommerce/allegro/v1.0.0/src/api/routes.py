"""FastAPI routes for Allegro integrator."""

from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel, Field

from pinquark_common.schemas.common import ErrorResponse, ErrorDetail
from pinquark_common.schemas.ecommerce import (
    Order,
    OrdersPage,
    OrderStatus,
    StockItem,
)
from src.allegro.schemas import AuthStatusResponse
from src.api.dependencies import app_state
from src.config import AllegroAccountConfig

router = APIRouter()


# --- Health ---

@router.get("/health")
async def health():
    if app_state.health_checker:
        return await app_state.health_checker.run()
    return {"status": "healthy"}


@router.get("/readiness")
async def readiness():
    if app_state.health_checker:
        result = await app_state.health_checker.run()
        if result.status != "healthy":
            raise HTTPException(status_code=503, detail=result.model_dump())
        return result
    return {"status": "ready"}


# --- Auth ---

@router.post("/auth/{account_name}/device-code", response_model=dict)
async def start_device_flow(account_name: str):
    """Start OAuth2 device flow for a specific account."""
    account = app_state.account_manager.get_account(account_name)
    if not account:
        raise HTTPException(status_code=404, detail=f"Account '{account_name}' not found")

    device_code = await app_state.auth_manager.start_device_flow(
        account.name, account.client_id, account.auth_url,
    )
    return {
        "user_code": device_code.user_code,
        "verification_uri": device_code.verification_uri,
        "verification_uri_complete": device_code.verification_uri_complete,
        "expires_in": device_code.expires_in,
        "message": f"Go to {device_code.verification_uri_complete} and enter code {device_code.user_code}",
    }


@router.post("/auth/{account_name}/poll-token")
async def poll_for_token(account_name: str, background_tasks: BackgroundTasks):
    """Poll for token after user has authorized the device code.

    This runs in the background to avoid HTTP timeout.
    """
    account = app_state.account_manager.get_account(account_name)
    if not account:
        raise HTTPException(status_code=404, detail=f"Account '{account_name}' not found")

    try:
        token = await app_state.auth_manager.poll_for_token(
            account.name, account.client_id, account.client_secret, account.auth_url,
        )
        return {"status": "authenticated", "expires_in": token.expires_in}
    except TimeoutError:
        raise HTTPException(status_code=408, detail="Device flow timed out. Start again.")
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc))


@router.get("/auth/{account_name}/status", response_model=AuthStatusResponse)
async def auth_status(account_name: str):
    return app_state.auth_manager.get_status(account_name)


@router.get("/auth/status", response_model=list[AuthStatusResponse])
async def all_auth_statuses():
    accounts = app_state.account_manager.list_accounts()
    return [app_state.auth_manager.get_status(a.name) for a in accounts]


# --- Accounts ---

class AccountCreateRequest(BaseModel):
    name: str
    client_id: str
    client_secret: str
    api_url: str = "https://api.allegro.pl"
    auth_url: str = "https://allegro.pl/auth/oauth"
    environment: str = "production"


@router.get("/accounts")
async def list_accounts():
    accounts = app_state.account_manager.list_accounts()
    return [{"name": a.name, "environment": a.environment, "api_url": a.api_url} for a in accounts]


@router.post("/accounts", status_code=201)
async def add_account(req: AccountCreateRequest):
    account = AllegroAccountConfig(**req.model_dump())
    app_state.account_manager.add_account(account)
    return {"status": "created", "name": account.name}


@router.delete("/accounts/{account_name}")
async def remove_account(account_name: str):
    if not app_state.account_manager.remove_account(account_name):
        raise HTTPException(status_code=404, detail=f"Account '{account_name}' not found")
    return {"status": "removed"}


# --- Orders ---

@router.get("/orders", response_model=OrdersPage)
async def list_orders(
    account_name: str = Query(..., description="Allegro account name"),
    since: datetime | None = Query(None, description="Fetch orders updated since this timestamp"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
):
    _require_auth(account_name)
    return await app_state.integration.fetch_orders(account_name, since, page, page_size)


@router.get("/orders/{order_id}", response_model=Order)
async def get_order(
    order_id: str,
    account_name: str = Query(..., description="Allegro account name"),
):
    _require_auth(account_name)
    return await app_state.integration.get_order(account_name, order_id)


class UpdateStatusRequest(BaseModel):
    status: OrderStatus


@router.put("/orders/{order_id}/status")
async def update_order_status(
    order_id: str,
    body: UpdateStatusRequest,
    account_name: str = Query(..., description="Allegro account name"),
):
    _require_auth(account_name)
    await app_state.integration.update_order_status(account_name, order_id, body.status)
    return {"status": "updated", "order_id": order_id, "new_status": body.status}


# --- Stock ---

class StockSyncRequest(BaseModel):
    items: list[StockItem]


@router.post("/stock/sync")
async def sync_stock(
    body: StockSyncRequest,
    account_name: str = Query(..., description="Allegro account name"),
):
    _require_auth(account_name)
    result = await app_state.integration.sync_stock(account_name, body.items)
    return result.model_dump()


# --- Product ---

@router.get("/products/{product_id}")
async def get_product(
    product_id: str,
    account_name: str = Query(..., description="Allegro account name"),
):
    _require_auth(account_name)
    return await app_state.integration.get_product(account_name, product_id)


# --- Product Search ---

@router.get("/products/search")
async def search_products(
    query: str = Query("", description="Search phrase"),
    account_name: str = Query(..., description="Allegro account name"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=60),
):
    _require_auth(account_name)
    return await app_state.integration.search_products(account_name, query, page, page_size)


# --- Helpers ---

def _require_auth(account_name: str) -> None:
    if not app_state.auth_manager.is_authenticated(account_name):
        raise HTTPException(
            status_code=401,
            detail=f"Account '{account_name}' not authenticated. Use POST /auth/{account_name}/device-code first.",
        )
