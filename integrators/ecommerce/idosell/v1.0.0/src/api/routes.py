"""FastAPI routes for IdoSell integrator."""

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
from src.api.dependencies import app_state
from src.config import IdoSellAccountConfig
from src.idosell.schemas import IdoSellAuthStatus

router = APIRouter()


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


@router.get("/auth/{account_name}/status", response_model=IdoSellAuthStatus)
async def auth_status(account_name: str) -> IdoSellAuthStatus:
    account = app_state.account_manager.get_account(account_name)
    api_version = account.api_version if account else ""
    return IdoSellAuthStatus(
        account_name=account_name,
        authenticated=account is not None,
        api_version=api_version,
    )


@router.post("/auth/{account_name}/validate")
async def validate_auth(account_name: str) -> dict[str, Any]:
    account = app_state.account_manager.get_account(account_name)
    if not account:
        raise HTTPException(status_code=404, detail=f"Account '{account_name}' not found")
    from src.idosell.auth import IdoSellAuthManager
    auth_mgr = IdoSellAuthManager()
    valid = await auth_mgr.validate(account)
    return {"account_name": account_name, "valid": valid}


class AccountCreateRequest(BaseModel):
    name: str
    shop_url: str
    api_key: str
    api_version: str = "v6"
    default_stock_id: int = 1
    default_currency: str = "PLN"
    environment: str = "production"


@router.get("/accounts")
async def list_accounts() -> list[dict[str, str]]:
    accounts = app_state.account_manager.list_accounts()
    return [
        {"name": a.name, "environment": a.environment, "shop_url": a.shop_url, "api_version": a.api_version}
        for a in accounts
    ]


@router.post("/accounts", status_code=201)
async def add_account(req: AccountCreateRequest) -> dict[str, str]:
    account = IdoSellAccountConfig(**req.model_dump())
    app_state.account_manager.add_account(account)
    return {"status": "created", "name": account.name}


@router.delete("/accounts/{account_name}")
async def remove_account(account_name: str) -> dict[str, str]:
    if not app_state.account_manager.remove_account(account_name):
        raise HTTPException(status_code=404, detail=f"Account '{account_name}' not found")
    return {"status": "removed"}


@router.get("/orders", response_model=OrdersPage)
async def list_orders(
    account_name: str = Query(..., description="IdoSell account name"),
    since: datetime | None = Query(None, description="Fetch orders modified since this timestamp"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
) -> OrdersPage:
    _require_account(account_name)
    return await app_state.integration.fetch_orders(account_name, since, page, page_size)


@router.get("/orders/{order_id}", response_model=Order)
async def get_order(
    order_id: str,
    account_name: str = Query(..., description="IdoSell account name"),
) -> Order:
    _require_account(account_name)
    return await app_state.integration.get_order(account_name, order_id)


class UpdateStatusRequest(BaseModel):
    status: OrderStatus


@router.put("/orders/{order_id}/status")
async def update_order_status(
    order_id: str,
    body: UpdateStatusRequest,
    account_name: str = Query(..., description="IdoSell account name"),
) -> dict[str, str]:
    _require_account(account_name)
    await app_state.integration.update_order_status(account_name, order_id, body.status)
    return {"status": "updated", "order_id": order_id, "new_status": body.status}


class StockSyncRequest(BaseModel):
    items: list[StockItem]


@router.post("/stock/sync")
async def sync_stock(
    body: StockSyncRequest,
    account_name: str = Query(..., description="IdoSell account name"),
) -> dict[str, Any]:
    _require_account(account_name)
    result = await app_state.integration.sync_stock(account_name, body.items)
    return result.model_dump()


@router.get("/products/{product_id}", response_model=Product)
async def get_product(
    product_id: str,
    account_name: str = Query(..., description="IdoSell account name"),
) -> Product:
    _require_account(account_name)
    return await app_state.integration.get_product(account_name, product_id)


@router.get("/products/search")
async def search_products(
    query: str = Query("", description="Search phrase"),
    account_name: str = Query(..., description="IdoSell account name"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
):
    _require_account(account_name)
    return await app_state.integration.search_products(account_name, query, page, page_size)


class ParcelCreateRequest(BaseModel):
    order_serial_number: int
    courier_id: int
    tracking_numbers: list[str]


@router.post("/parcels", status_code=201)
async def create_parcel(
    body: ParcelCreateRequest,
    account_name: str = Query(..., description="IdoSell account name"),
) -> dict[str, Any]:
    _require_account(account_name)
    result = await app_state.integration.create_parcel(
        account_name, body.order_serial_number, body.courier_id, body.tracking_numbers,
    )
    return {"status": "created", "result": result}


def _require_account(account_name: str) -> None:
    if not app_state.account_manager.get_account(account_name):
        raise HTTPException(
            status_code=404,
            detail=f"Account '{account_name}' not found. Add it via POST /accounts.",
        )
