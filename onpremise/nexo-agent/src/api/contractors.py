"""Contractor (Podmiot) REST API endpoints."""

from typing import Any

from fastapi import APIRouter, HTTPException, Query

from src.api.dependencies import app_state
from src.models.contractor import ContractorCreate, ContractorUpdate

router = APIRouter()


@router.get("")
async def list_contractors(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    search: str | None = None,
) -> dict[str, Any]:
    svc = app_state.contractor_service
    if not svc:
        raise HTTPException(status_code=503, detail="Service not initialized")
    return svc.list_contractors(page=page, page_size=page_size, search=search)


@router.get("/{symbol}")
async def get_contractor(symbol: str) -> dict[str, Any]:
    svc = app_state.contractor_service
    if not svc:
        raise HTTPException(status_code=503, detail="Service not initialized")

    result = svc.get_contractor(symbol)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Contractor not found: {symbol}")
    return result.model_dump()


@router.get("/by-nip/{nip}")
async def get_contractor_by_nip(nip: str) -> dict[str, Any]:
    svc = app_state.contractor_service
    if not svc:
        raise HTTPException(status_code=503, detail="Service not initialized")

    result = svc.get_contractor_by_nip(nip)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Contractor with NIP {nip} not found")
    return result.model_dump()


@router.post("", status_code=201)
async def create_contractor(data: ContractorCreate) -> dict[str, Any]:
    svc = app_state.contractor_service
    if not svc:
        raise HTTPException(status_code=503, detail="Service not initialized")

    try:
        result = svc.create_contractor(data)
        return result.model_dump()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.put("/{symbol}")
async def update_contractor(symbol: str, data: ContractorUpdate) -> dict[str, Any]:
    svc = app_state.contractor_service
    if not svc:
        raise HTTPException(status_code=503, detail="Service not initialized")

    try:
        result = svc.update_contractor(symbol, data)
        return result.model_dump()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.delete("/{symbol}")
async def delete_contractor(symbol: str) -> dict[str, Any]:
    svc = app_state.contractor_service
    if not svc:
        raise HTTPException(status_code=503, detail="Service not initialized")

    success = svc.delete_contractor(symbol)
    if not success:
        raise HTTPException(status_code=404, detail=f"Contractor not found or cannot be deleted: {symbol}")
    return {"deleted": True, "symbol": symbol}
