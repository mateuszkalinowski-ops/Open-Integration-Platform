"""Order (Zamówienie) REST API endpoints."""

from typing import Any

from fastapi import APIRouter, HTTPException, Query

from src.api.dependencies import app_state
from src.models.order import OrderCreate, OrderType, OrderUpdate

router = APIRouter()


@router.get("")
async def list_orders(
    order_type: OrderType = OrderType.FROM_CUSTOMER,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
) -> dict[str, Any]:
    svc = app_state.order_service
    if not svc:
        raise HTTPException(status_code=503, detail="Service not initialized")
    return svc.list_orders(order_type=order_type, page=page, page_size=page_size)


@router.get("/{order_id}")
async def get_order(
    order_id: int,
    order_type: OrderType = OrderType.FROM_CUSTOMER,
) -> dict[str, Any]:
    svc = app_state.order_service
    if not svc:
        raise HTTPException(status_code=503, detail="Service not initialized")

    result = svc.get_order(order_id, order_type)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Order not found: {order_id}")
    return result.model_dump()


@router.post("", status_code=201)
async def create_order(data: OrderCreate) -> dict[str, Any]:
    svc = app_state.order_service
    if not svc:
        raise HTTPException(status_code=503, detail="Service not initialized")

    try:
        result = svc.create_order(data)
        return result.model_dump()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.put("/{order_id}")
async def update_order(
    order_id: int,
    data: OrderUpdate,
    order_type: OrderType = OrderType.FROM_CUSTOMER,
) -> dict[str, Any]:
    svc = app_state.order_service
    if not svc:
        raise HTTPException(status_code=503, detail="Service not initialized")

    try:
        result = svc.update_order(order_id, data, order_type)
        return result.model_dump()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
