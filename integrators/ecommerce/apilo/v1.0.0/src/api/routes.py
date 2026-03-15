"""FastAPI routes for Apilo integrator."""

from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pinquark_common.schemas.ecommerce import (
    Order,
    OrdersPage,
    OrderStatus,
    Product,
    ProductsPage,
    StockItem,
)
from pydantic import BaseModel

from src.api.dependencies import app_state
from src.config import ApiloAccountConfig

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
    authorization_code: str = ""
    refresh_token: str = ""
    base_url: str = "https://app.apilo.com"
    environment: str = "production"


@router.get("/accounts")
async def list_accounts() -> list[dict[str, str]]:
    accounts = app_state.account_manager.list_accounts()
    return [{"name": a.name, "base_url": a.base_url, "environment": a.environment} for a in accounts]


@router.post("/accounts", status_code=201)
async def add_account(req: AccountCreateRequest) -> dict[str, str]:
    account = ApiloAccountConfig(**req.model_dump())
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
    account_name: str = Query(..., description="Apilo account name"),
    since: datetime | None = Query(None, description="Fetch orders updated since this timestamp"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=512),
) -> OrdersPage:
    _require_account(account_name)
    return await app_state.integration.fetch_orders(account_name, since, page, page_size)


@router.get("/orders/{order_id}", response_model=Order)
async def get_order(
    order_id: str,
    account_name: str = Query(..., description="Apilo account name"),
) -> Order:
    _require_account(account_name)
    return await app_state.integration.get_order(account_name, order_id)


class UpdateStatusRequest(BaseModel):
    status: OrderStatus


@router.put("/orders/{order_id}/status")
async def update_order_status(
    order_id: str,
    body: UpdateStatusRequest,
    account_name: str = Query(..., description="Apilo account name"),
) -> dict[str, str]:
    _require_account(account_name)
    await app_state.integration.update_order_status(account_name, order_id, body.status)
    return {"status": "updated", "order_id": order_id, "new_status": body.status}


@router.post("/orders", status_code=201)
async def create_order(
    body: dict[str, Any],
    account_name: str = Query(..., description="Apilo account name"),
) -> dict[str, Any]:
    _require_account(account_name)
    result = await app_state.integration.create_order(account_name, body)
    return {"status": "created", "result": result}


class AddPaymentRequest(BaseModel):
    type: int
    payment_date: str
    amount: float
    id_external: str = ""
    comment: str = ""


@router.post("/orders/{order_id}/payment")
async def add_order_payment(
    order_id: str,
    body: AddPaymentRequest,
    account_name: str = Query(..., description="Apilo account name"),
) -> dict[str, Any]:
    _require_account(account_name)
    payment_data = {
        "type": body.type,
        "paymentDate": body.payment_date,
        "amount": body.amount,
    }
    if body.id_external:
        payment_data["idExternal"] = body.id_external
    if body.comment:
        payment_data["comment"] = body.comment

    result = await app_state.integration.add_order_payment(account_name, order_id, payment_data)
    return {"status": "added", "order_id": order_id, "result": result}


class AddNoteRequest(BaseModel):
    comment: str
    type: int = 2


@router.post("/orders/{order_id}/note")
async def add_order_note(
    order_id: str,
    body: AddNoteRequest,
    account_name: str = Query(..., description="Apilo account name"),
) -> dict[str, Any]:
    _require_account(account_name)
    result = await app_state.integration.add_order_note(account_name, order_id, body.comment, body.type)
    return {"status": "added", "order_id": order_id, "result": result}


class AddShipmentRequest(BaseModel):
    tracking: str
    carrier_provider_id: int
    id_external: str = ""
    post_date: str = ""
    media: str = ""


@router.post("/orders/{order_id}/shipment")
async def add_order_shipment(
    order_id: str,
    body: AddShipmentRequest,
    account_name: str = Query(..., description="Apilo account name"),
) -> dict[str, Any]:
    _require_account(account_name)
    shipment_data: dict[str, Any] = {
        "tracking": body.tracking,
        "carrierProviderId": body.carrier_provider_id,
    }
    if body.id_external:
        shipment_data["idExternal"] = body.id_external
    if body.post_date:
        shipment_data["postDate"] = body.post_date
    if body.media:
        shipment_data["media"] = body.media

    result = await app_state.integration.add_order_shipment(account_name, order_id, shipment_data)
    return {"status": "added", "order_id": order_id, "result": result}


class TagRequest(BaseModel):
    tag_id: int


@router.post("/orders/{order_id}/tag")
async def add_order_tag(
    order_id: str,
    body: TagRequest,
    account_name: str = Query(..., description="Apilo account name"),
) -> dict[str, Any]:
    _require_account(account_name)
    result = await app_state.integration.manage_order_tag(account_name, order_id, body.tag_id)
    return {"status": "added", "order_id": order_id, "result": result}


@router.delete("/orders/{order_id}/tag/{tag_id}")
async def remove_order_tag(
    order_id: str,
    tag_id: int,
    account_name: str = Query(..., description="Apilo account name"),
) -> dict[str, Any]:
    _require_account(account_name)
    result = await app_state.integration.manage_order_tag(account_name, order_id, tag_id, remove=True)
    return {"status": "removed", "order_id": order_id, "result": result}


# ---------------------------------------------------------------------------
# Stock
# ---------------------------------------------------------------------------


class StockSyncRequest(BaseModel):
    items: list[StockItem]


@router.post("/stock/sync")
async def sync_stock(
    body: StockSyncRequest,
    account_name: str = Query(..., description="Apilo account name"),
) -> dict[str, Any]:
    _require_account(account_name)
    result = await app_state.integration.sync_stock(account_name, body.items)
    return result.model_dump()


# ---------------------------------------------------------------------------
# Products / Catalog
# ---------------------------------------------------------------------------


@router.get("/products", response_model=ProductsPage)
async def list_products(
    account_name: str = Query(..., description="Apilo account name"),
    query: str = Query("", description="Search by product name"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=512),
) -> ProductsPage:
    _require_account(account_name)
    return await app_state.integration.search_products(account_name, query, page, page_size)


@router.get("/products/{product_id}", response_model=Product)
async def get_product(
    product_id: str,
    account_name: str = Query(..., description="Apilo account name"),
) -> Product:
    _require_account(account_name)
    return await app_state.integration.get_product(account_name, product_id)


# ---------------------------------------------------------------------------
# Shipments
# ---------------------------------------------------------------------------


@router.post("/shipments", status_code=201)
async def create_shipment(
    body: dict[str, Any],
    account_name: str = Query(..., description="Apilo account name"),
) -> dict[str, Any]:
    _require_account(account_name)
    result = await app_state.integration.create_shipment(account_name, body)
    return {"status": "created", "result": result}


@router.get("/shipments/{shipment_id}")
async def get_shipment(
    shipment_id: str,
    account_name: str = Query(..., description="Apilo account name"),
) -> dict[str, Any]:
    _require_account(account_name)
    return await app_state.integration.get_shipment(account_name, shipment_id)


# ---------------------------------------------------------------------------
# Reference Maps
# ---------------------------------------------------------------------------


@router.get("/maps")
async def get_maps(
    account_name: str = Query(..., description="Apilo account name"),
) -> dict[str, Any]:
    _require_account(account_name)
    return await app_state.integration.get_maps(account_name)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _require_account(account_name: str) -> None:
    if not app_state.account_manager.get_account(account_name):
        raise HTTPException(
            status_code=404,
            detail=f"Account '{account_name}' not found. Add it via POST /accounts.",
        )
