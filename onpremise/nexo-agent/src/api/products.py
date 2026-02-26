"""Product (Asortyment) REST API endpoints."""

from typing import Any

from fastapi import APIRouter, HTTPException, Query

from src.api.dependencies import app_state
from src.models.product import ProductCreate, ProductUpdate

router = APIRouter()


@router.get("")
async def list_products(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    search: str | None = None,
    group: str | None = None,
) -> dict[str, Any]:
    svc = app_state.product_service
    if not svc:
        raise HTTPException(status_code=503, detail="Service not initialized")
    return svc.list_products(page=page, page_size=page_size, search=search, group=group)


@router.get("/by-ean/{ean}")
async def get_product_by_ean(ean: str) -> dict[str, Any]:
    svc = app_state.product_service
    if not svc:
        raise HTTPException(status_code=503, detail="Service not initialized")

    result = svc.get_product_by_ean(ean)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Product with EAN {ean} not found")
    return result.model_dump()


@router.get("/{symbol}")
async def get_product(symbol: str) -> dict[str, Any]:
    svc = app_state.product_service
    if not svc:
        raise HTTPException(status_code=503, detail="Service not initialized")

    result = svc.get_product(symbol)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Product not found: {symbol}")
    return result.model_dump()


@router.post("", status_code=201)
async def create_product(data: ProductCreate) -> dict[str, Any]:
    svc = app_state.product_service
    if not svc:
        raise HTTPException(status_code=503, detail="Service not initialized")

    try:
        result = svc.create_product(data)
        return result.model_dump()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.put("/{symbol}")
async def update_product(symbol: str, data: ProductUpdate) -> dict[str, Any]:
    svc = app_state.product_service
    if not svc:
        raise HTTPException(status_code=503, detail="Service not initialized")

    try:
        result = svc.update_product(symbol, data)
        return result.model_dump()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.delete("/{symbol}")
async def delete_product(symbol: str) -> dict[str, Any]:
    svc = app_state.product_service
    if not svc:
        raise HTTPException(status_code=503, detail="Service not initialized")

    success = svc.delete_product(symbol)
    if not success:
        raise HTTPException(status_code=404, detail=f"Product not found or cannot be deleted: {symbol}")
    return {"deleted": True, "symbol": symbol}
