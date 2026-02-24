"""FastAPI routes for WooCommerce integrator."""

from datetime import datetime

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from pinquark_common.schemas.ecommerce import (
    Order,
    OrdersPage,
    OrderStatus,
    Product,
    StockItem,
)
from src.woocommerce.schemas import AuthStatusResponse
from src.api.dependencies import app_state
from src.config import WooCommerceAccountConfig

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


@router.get("/auth/{account_name}/status", response_model=AuthStatusResponse)
async def auth_status(account_name: str):
    if not app_state.auth:
        raise HTTPException(status_code=503, detail="Auth not initialized")
    return app_state.auth.get_status(account_name)


@router.get("/auth/status", response_model=list[AuthStatusResponse])
async def all_auth_statuses():
    accounts = app_state.account_manager.list_accounts()
    return [app_state.auth.get_status(a.name) for a in accounts]


@router.post("/auth/{account_name}/test")
async def test_connection(account_name: str):
    """Test WooCommerce API connection for a specific account."""
    _require_auth(account_name)
    try:
        result = await app_state.client.test_connection(account_name)
        return {"status": "connected", "woocommerce_version": result.get("settings", {}).get("version", "unknown")}
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Connection test failed: {exc}") from exc


# --- Accounts ---


class AccountCreateRequest(BaseModel):
    name: str
    store_url: str
    consumer_key: str
    consumer_secret: str
    api_version: str = "wc/v3"
    verify_ssl: bool = True
    environment: str = "production"


@router.get("/accounts")
async def list_accounts():
    accounts = app_state.account_manager.list_accounts()
    return [
        {"name": a.name, "environment": a.environment, "store_url": a.store_url}
        for a in accounts
    ]


@router.post("/accounts", status_code=201)
async def add_account(req: AccountCreateRequest):
    account = WooCommerceAccountConfig(**req.model_dump())
    app_state.account_manager.add_account(account)
    app_state.auth.register_account(
        account.name, account.store_url, account.consumer_key,
        account.consumer_secret, account.api_version,
    )
    return {"status": "created", "name": account.name}


@router.delete("/accounts/{account_name}")
async def remove_account(account_name: str):
    if not app_state.account_manager.remove_account(account_name):
        raise HTTPException(status_code=404, detail=f"Account '{account_name}' not found")
    app_state.auth.remove_account(account_name)
    return {"status": "removed"}


# --- Orders ---


@router.get("/orders", response_model=OrdersPage)
async def list_orders(
    account_name: str = Query(..., description="WooCommerce account name"),
    since: datetime | None = Query(None, description="Fetch orders modified since this timestamp"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
):
    _require_auth(account_name)
    return await app_state.integration.fetch_orders(account_name, since, page, page_size)


@router.get("/orders/{order_id}", response_model=Order)
async def get_order(
    order_id: str,
    account_name: str = Query(..., description="WooCommerce account name"),
):
    _require_auth(account_name)
    return await app_state.integration.get_order(account_name, order_id)


class UpdateStatusRequest(BaseModel):
    status: OrderStatus


@router.put("/orders/{order_id}/status")
async def update_order_status(
    order_id: str,
    body: UpdateStatusRequest,
    account_name: str = Query(..., description="WooCommerce account name"),
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
    account_name: str = Query(..., description="WooCommerce account name"),
):
    _require_auth(account_name)
    result = await app_state.integration.sync_stock(account_name, body.items)
    return result.model_dump()


# --- Products ---


@router.get("/products/{product_id}", response_model=Product)
async def get_product(
    product_id: str,
    account_name: str = Query(..., description="WooCommerce account name"),
):
    _require_auth(account_name)
    return await app_state.integration.get_product(account_name, product_id)


@router.get("/products/search")
async def search_products(
    query: str = Query("", description="Search phrase"),
    account_name: str = Query(..., description="WooCommerce account name"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
):
    _require_auth(account_name)
    return await app_state.integration.search_products(account_name, query, page, page_size)


class ProductSyncRequest(BaseModel):
    products: list[Product]


@router.post("/products/sync")
async def sync_products(
    body: ProductSyncRequest,
    account_name: str = Query(..., description="WooCommerce account name"),
):
    _require_auth(account_name)
    result = await app_state.integration.sync_products(account_name, body.products)
    return result.model_dump()


# --- Helpers ---


def _require_auth(account_name: str) -> None:
    if not app_state.auth or not app_state.auth.is_authenticated(account_name):
        raise HTTPException(
            status_code=401,
            detail=f"Account '{account_name}' not configured. Add it via POST /accounts first.",
        )
