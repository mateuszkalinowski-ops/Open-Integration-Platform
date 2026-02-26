"""Stock level REST API endpoints."""

from typing import Any

from fastapi import APIRouter, HTTPException, Query

from src.api.dependencies import app_state
from src.models.stock import StockQuery

router = APIRouter()


@router.get("")
async def get_stock_levels(
    warehouse: str | None = None,
    only_available: bool = False,
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=1000),
) -> dict[str, Any]:
    svc = app_state.stock_service
    if not svc:
        raise HTTPException(status_code=503, detail="Service not initialized")

    query = StockQuery(
        warehouse_symbol=warehouse,
        only_available=only_available,
        page=page,
        page_size=page_size,
    )
    result = svc.get_stock_levels(query)
    return result.model_dump()


@router.get("/{product_symbol}")
async def get_stock_for_product(
    product_symbol: str,
    warehouse: str | None = None,
) -> dict[str, Any]:
    svc = app_state.stock_service
    if not svc:
        raise HTTPException(status_code=503, detail="Service not initialized")

    result = svc.get_stock_for_product(product_symbol, warehouse or "")
    if result is None:
        raise HTTPException(status_code=404, detail=f"Product not found: {product_symbol}")
    return result.model_dump()
