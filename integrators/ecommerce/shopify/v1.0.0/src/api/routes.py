"""FastAPI routes for Shopify integrator."""

from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from pinquark_common.schemas.ecommerce import (
    Order,
    OrdersPage,
    OrderStatus,
    Product,
    StockItem,
)
from src.shopify.schemas import AuthStatusResponse
from src.api.dependencies import app_state
from src.config import ShopifyAccountConfig

router = APIRouter()


# --- Health ---

@router.get("/health")
async def health() -> dict[str, Any]:
    if app_state.health_checker:
        result = await app_state.health_checker.run()
        return result.model_dump() if hasattr(result, "model_dump") else result
    return {"status": "healthy"}


@router.get("/readiness")
async def readiness() -> dict[str, Any]:
    if app_state.health_checker:
        result = await app_state.health_checker.run()
        data = result.model_dump() if hasattr(result, "model_dump") else result
        status = result.status if hasattr(result, "status") else data.get("status")
        if status != "healthy":
            raise HTTPException(status_code=503, detail=data)
        return data
    return {"status": "ready"}


# --- Auth ---

@router.post("/auth/{account_name}/validate")
async def validate_credentials(account_name: str) -> dict[str, Any]:
    """Validate Shopify access token for a specific account."""
    account = app_state.account_manager.get_account(account_name)
    if not account:
        raise HTTPException(status_code=404, detail=f"Account '{account_name}' not found")

    is_valid = await app_state.auth_manager.validate_credentials(account)
    if not is_valid:
        raise HTTPException(status_code=401, detail="Invalid access token")
    return {"status": "validated", "account": account_name, "shop_url": account.shop_url}


@router.get("/auth/{account_name}/status", response_model=AuthStatusResponse)
async def auth_status(account_name: str) -> AuthStatusResponse:
    account = app_state.account_manager.get_account(account_name)
    return app_state.auth_manager.get_status(account_name, account)


@router.get("/auth/status", response_model=list[AuthStatusResponse])
async def all_auth_statuses() -> list[AuthStatusResponse]:
    accounts = app_state.account_manager.list_accounts()
    return [app_state.auth_manager.get_status(a.name, a) for a in accounts]


# --- Accounts ---

class AccountCreateRequest(BaseModel):
    name: str
    shop_url: str
    access_token: str
    api_version: str = "2024-07"
    default_location_id: str = ""
    default_carrier: str = "Kurier"


@router.get("/accounts")
async def list_accounts() -> list[dict[str, str]]:
    accounts = app_state.account_manager.list_accounts()
    return [{"name": a.name, "shop_url": a.shop_url, "api_version": a.api_version} for a in accounts]


@router.post("/accounts", status_code=201)
async def add_account(req: AccountCreateRequest) -> dict[str, str]:
    account = ShopifyAccountConfig(**req.model_dump())
    app_state.account_manager.add_account(account)
    app_state.auth_manager.mark_authenticated(account.name)
    return {"status": "created", "name": account.name}


@router.delete("/accounts/{account_name}")
async def remove_account(account_name: str) -> dict[str, str]:
    if not app_state.account_manager.remove_account(account_name):
        raise HTTPException(status_code=404, detail=f"Account '{account_name}' not found")
    return {"status": "removed"}


# --- Orders ---

@router.get("/orders", response_model=OrdersPage)
async def list_orders(
    account_name: str = Query(..., description="Shopify account name"),
    since: datetime | None = Query(None, description="Fetch orders updated since this timestamp"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=250),
) -> OrdersPage:
    _require_auth(account_name)
    return await app_state.integration.fetch_orders(account_name, since, page, page_size)


@router.get("/orders/{order_id}", response_model=Order)
async def get_order(
    order_id: str,
    account_name: str = Query(..., description="Shopify account name"),
) -> Order:
    _require_auth(account_name)
    return await app_state.integration.get_order(account_name, order_id)


class UpdateStatusRequest(BaseModel):
    status: OrderStatus
    tracking_number: str = ""
    tracking_company: str = ""


@router.put("/orders/{order_id}/status")
async def update_order_status(
    order_id: str,
    body: UpdateStatusRequest,
    account_name: str = Query(..., description="Shopify account name"),
) -> dict[str, Any]:
    _require_auth(account_name)
    await app_state.integration.update_order_status(
        account_name, order_id, body.status,
        tracking_number=body.tracking_number,
        tracking_company=body.tracking_company,
    )
    return {"status": "updated", "order_id": order_id, "new_status": body.status}


class FulfillRequest(BaseModel):
    tracking_number: str = ""
    tracking_company: str = ""
    notify_customer: bool = True


@router.post("/orders/{order_id}/fulfill")
async def fulfill_order(
    order_id: str,
    body: FulfillRequest,
    account_name: str = Query(..., description="Shopify account name"),
) -> dict[str, Any]:
    _require_auth(account_name)
    await app_state.integration.update_order_status(
        account_name, order_id, OrderStatus.SHIPPED,
        tracking_number=body.tracking_number,
        tracking_company=body.tracking_company,
    )
    return {"status": "fulfilled", "order_id": order_id}


# --- Stock ---

class StockSyncRequest(BaseModel):
    items: list[StockItem]


@router.post("/stock/sync")
async def sync_stock(
    body: StockSyncRequest,
    account_name: str = Query(..., description="Shopify account name"),
) -> dict[str, Any]:
    _require_auth(account_name)
    result = await app_state.integration.sync_stock(account_name, body.items)
    return result.model_dump()


# --- Products ---

@router.get("/products/{product_id}", response_model=Product)
async def get_product(
    product_id: str,
    account_name: str = Query(..., description="Shopify account name"),
) -> Product:
    _require_auth(account_name)
    return await app_state.integration.get_product(account_name, product_id)


@router.get("/products/search")
async def search_products(
    query: str = Query("", description="Search by product title"),
    account_name: str = Query(..., description="Shopify account name"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=250),
):
    _require_auth(account_name)
    return await app_state.integration.search_products(account_name, query, page, page_size)


class ProductSyncRequest(BaseModel):
    products: list[Product]


@router.post("/products/sync")
async def sync_products(
    body: ProductSyncRequest,
    account_name: str = Query(..., description="Shopify account name"),
) -> dict[str, Any]:
    _require_auth(account_name)
    result = await app_state.integration.sync_products(account_name, body.products)
    return result.model_dump()


# --- Helpers ---

def _require_auth(account_name: str) -> None:
    if not app_state.auth_manager.is_authenticated(account_name):
        raise HTTPException(
            status_code=401,
            detail=(
                f"Account '{account_name}' not authenticated. "
                f"Use POST /auth/{account_name}/validate first."
            ),
        )
