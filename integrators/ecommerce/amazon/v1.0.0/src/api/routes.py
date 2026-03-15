"""FastAPI routes for Amazon SP-API integrator."""

from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pinquark_common.schemas.ecommerce import (
    Order,
    OrdersPage,
    OrderStatus,
    Product,
    StockItem,
)
from pydantic import BaseModel

from src.api.dependencies import app_state
from src.config import AmazonAccountConfig

router = APIRouter()


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Accounts
# ---------------------------------------------------------------------------


class AccountCreateRequest(BaseModel):
    name: str
    client_id: str
    client_secret: str
    refresh_token: str
    marketplace_id: str
    region: str = "eu"
    sandbox_mode: bool = False
    environment: str = "production"


@router.get("/accounts")
async def list_accounts() -> list[dict[str, str]]:
    accounts = app_state.account_manager.list_accounts()
    return [{"name": a.name, "region": a.region, "environment": a.environment} for a in accounts]


@router.post("/accounts", status_code=201)
async def add_account(req: AccountCreateRequest) -> dict[str, str]:
    account = AmazonAccountConfig(**req.model_dump())
    app_state.account_manager.add_account(account)
    return {"status": "created", "name": account.name}


@router.delete("/accounts/{account_name}")
async def remove_account(account_name: str) -> dict[str, str]:
    if not app_state.account_manager.remove_account(account_name):
        raise HTTPException(status_code=404, detail=f"Account '{account_name}' not found")
    return {"status": "removed"}


# ---------------------------------------------------------------------------
# Orders
# ---------------------------------------------------------------------------


@router.get("/orders", response_model=OrdersPage)
async def list_orders(
    account_name: str = Query(..., description="Amazon account name"),
    since: datetime | None = Query(None, description="Fetch orders created since this timestamp"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
) -> OrdersPage:
    _require_account(account_name)
    return await app_state.integration.fetch_orders(account_name, since, page, page_size)


@router.get("/orders/{order_id}", response_model=Order)
async def get_order(
    order_id: str,
    account_name: str = Query(..., description="Amazon account name"),
) -> Order:
    _require_account(account_name)
    return await app_state.integration.get_order(account_name, order_id)


class UpdateStatusRequest(BaseModel):
    status: OrderStatus


@router.put("/orders/{order_id}/status")
async def update_order_status(
    order_id: str,
    body: UpdateStatusRequest,
    account_name: str = Query(..., description="Amazon account name"),
) -> dict[str, str]:
    _require_account(account_name)
    await app_state.integration.update_order_status(account_name, order_id, body.status)
    return {"status": "updated", "order_id": order_id, "new_status": body.status}


class AcknowledgeRequest(BaseModel):
    pass


@router.post("/orders/{order_id}/acknowledge")
async def acknowledge_order(
    order_id: str,
    account_name: str = Query(..., description="Amazon account name"),
) -> dict[str, Any]:
    _require_account(account_name)
    result = await app_state.integration.acknowledge_order(account_name, order_id)
    return {"status": "acknowledged", "order_id": order_id, "feed": result}


class ShipmentConfirmRequest(BaseModel):
    carrier_code: str
    tracking_number: str
    ship_date: str | None = None
    carrier_name: str = ""


@router.post("/orders/{order_id}/ship")
async def confirm_shipment(
    order_id: str,
    body: ShipmentConfirmRequest,
    account_name: str = Query(..., description="Amazon account name"),
) -> dict[str, Any]:
    _require_account(account_name)
    result = await app_state.integration.confirm_shipment(
        account_name,
        order_id,
        body.carrier_code,
        body.tracking_number,
        ship_date=body.ship_date,
        carrier_name=body.carrier_name,
    )
    return {"status": "shipped", "order_id": order_id, "feed": result}


# ---------------------------------------------------------------------------
# Stock
# ---------------------------------------------------------------------------


class StockSyncRequest(BaseModel):
    items: list[StockItem]


@router.post("/stock/sync")
async def sync_stock(
    body: StockSyncRequest,
    account_name: str = Query(..., description="Amazon account name"),
) -> dict[str, Any]:
    _require_account(account_name)
    result = await app_state.integration.sync_stock(account_name, body.items)
    return result.model_dump()


# ---------------------------------------------------------------------------
# Products / Catalog
# ---------------------------------------------------------------------------


@router.get("/products/{asin}", response_model=Product)
async def get_product(
    asin: str,
    account_name: str = Query(..., description="Amazon account name"),
) -> Product:
    _require_account(account_name)
    return await app_state.integration.get_product(account_name, asin)


class ProductSearchRequest(BaseModel):
    keywords: list[str] | None = None
    identifiers: list[str] | None = None
    identifiers_type: str | None = None
    page_size: int = 10


@router.post("/products/search")
async def search_products(
    body: ProductSearchRequest,
    account_name: str = Query(..., description="Amazon account name"),
) -> list[Product]:
    _require_account(account_name)
    return await app_state.integration.search_products(
        account_name,
        keywords=body.keywords,
        identifiers=body.identifiers,
        identifiers_type=body.identifiers_type,
        page_size=body.page_size,
    )


# ---------------------------------------------------------------------------
# Reports
# ---------------------------------------------------------------------------


class CreateReportRequest(BaseModel):
    report_type: str
    data_start_time: str | None = None
    data_end_time: str | None = None


@router.post("/reports", status_code=201)
async def create_report(
    body: CreateReportRequest,
    account_name: str = Query(..., description="Amazon account name"),
) -> dict[str, Any]:
    _require_account(account_name)
    result = await app_state.integration.create_report(
        account_name,
        body.report_type,
        data_start_time=body.data_start_time,
        data_end_time=body.data_end_time,
    )
    return {"status": "created", "report": result}


@router.get("/reports/{report_id}")
async def get_report(
    report_id: str,
    account_name: str = Query(..., description="Amazon account name"),
) -> dict[str, Any]:
    _require_account(account_name)
    return await app_state.integration.get_report(account_name, report_id)


# ---------------------------------------------------------------------------
# Feeds
# ---------------------------------------------------------------------------


@router.get("/feeds/{feed_id}")
async def get_feed_status(
    feed_id: str,
    account_name: str = Query(..., description="Amazon account name"),
) -> dict[str, Any]:
    _require_account(account_name)
    return await app_state.integration.get_feed_status(account_name, feed_id)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _require_account(account_name: str) -> None:
    if not app_state.account_manager.get_account(account_name):
        raise HTTPException(
            status_code=404,
            detail=f"Account '{account_name}' not found. Add it via POST /accounts.",
        )
