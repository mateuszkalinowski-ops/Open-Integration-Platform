"""Document (sales & warehouse) REST API endpoints."""

from typing import Any

from fastapi import APIRouter, HTTPException, Query

from src.api.dependencies import app_state
from src.models.document import DocumentCreate, DocumentType

router = APIRouter()


@router.get("/sales")
async def list_sales_documents(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
) -> dict[str, Any]:
    svc = app_state.sales_document_service
    if not svc:
        raise HTTPException(status_code=503, detail="Service not initialized")
    return svc.list_documents(page=page, page_size=page_size)


@router.get("/sales/{doc_id}")
async def get_sales_document(doc_id: int) -> dict[str, Any]:
    svc = app_state.sales_document_service
    if not svc:
        raise HTTPException(status_code=503, detail="Service not initialized")

    result = svc.get_document(doc_id)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Sales document not found: {doc_id}")
    return result.model_dump()


@router.get("/sales/by-number/{number}")
async def get_sales_document_by_number(number: str) -> dict[str, Any]:
    svc = app_state.sales_document_service
    if not svc:
        raise HTTPException(status_code=503, detail="Service not initialized")

    result = svc.get_document_by_number(number)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Sales document not found: {number}")
    return result.model_dump()


@router.post("/sales", status_code=201)
async def create_sales_document(data: DocumentCreate) -> dict[str, Any]:
    svc = app_state.sales_document_service
    if not svc:
        raise HTTPException(status_code=503, detail="Service not initialized")

    allowed = {DocumentType.SALES_INVOICE, DocumentType.SALES_RECEIPT, DocumentType.PROFORMA}
    if data.document_type not in allowed:
        raise HTTPException(status_code=400, detail=f"Invalid sales document type: {data.document_type}")

    try:
        result = svc.create_invoice(data)
        return result.model_dump()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/warehouse/issues")
async def list_warehouse_issues(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
) -> dict[str, Any]:
    svc = app_state.warehouse_document_service
    if not svc:
        raise HTTPException(status_code=503, detail="Service not initialized")
    return svc.list_issues(page=page, page_size=page_size)


@router.get("/warehouse/receipts")
async def list_warehouse_receipts(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
) -> dict[str, Any]:
    svc = app_state.warehouse_document_service
    if not svc:
        raise HTTPException(status_code=503, detail="Service not initialized")
    return svc.list_receipts(page=page, page_size=page_size)


@router.post("/warehouse/issue", status_code=201)
async def create_warehouse_issue(data: DocumentCreate) -> dict[str, Any]:
    svc = app_state.warehouse_document_service
    if not svc:
        raise HTTPException(status_code=503, detail="Service not initialized")

    try:
        result = svc.create_issue(data)
        return result.model_dump()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/warehouse/receipt", status_code=201)
async def create_warehouse_receipt(data: DocumentCreate) -> dict[str, Any]:
    svc = app_state.warehouse_document_service
    if not svc:
        raise HTTPException(status_code=503, detail="Service not initialized")

    try:
        result = svc.create_receipt(data)
        return result.model_dump()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
