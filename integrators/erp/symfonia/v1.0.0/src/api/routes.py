"""REST API routes for the Symfonia ERP WebAPI connector."""

import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Query

from src.api.dependencies import app_state
from src.models.schemas import (
    ContractorCreate,
    ContractorUpdate,
    FilterRequest,
    ProductCreate,
    ProductUpdate,
)
from src.services.symfonia_client import SymfoniaApiError

logger = logging.getLogger(__name__)

router = APIRouter()


def _get_client():  # type: ignore[no-untyped-def]
    if not app_state.symfonia_client:
        raise HTTPException(status_code=503, detail="Service not initialized")
    return app_state.symfonia_client


def _map_error(exc: SymfoniaApiError) -> HTTPException:
    status = exc.status_code
    if status == 401:
        status = 502
    return HTTPException(status_code=status, detail={"message": exc.message, "details": exc.details})


# --- Health ---


@router.get("/health")
async def health() -> dict[str, Any]:
    if app_state.health_checker:
        result = await app_state.health_checker.run()
        return result.model_dump() if hasattr(result, "model_dump") else result
    return {"status": "healthy"}


@router.get("/readiness")
async def readiness() -> dict[str, Any]:
    client = _get_client()
    try:
        ping_result = await client.ping()
        return {"status": "ready", "symfonia": ping_result}
    except Exception as exc:
        logger.exception("Readiness check failed")
        raise HTTPException(status_code=503, detail="Symfonia WebAPI unreachable") from exc


@router.get("/api/v1/ping")
async def ping() -> dict[str, Any]:
    client = _get_client()
    try:
        return await client.ping()
    except SymfoniaApiError as exc:
        raise _map_error(exc) from exc


@router.get("/api/v1/alive")
async def alive() -> dict[str, str]:
    client = _get_client()
    try:
        result = await client.alive()
        return {"server_time": result}
    except SymfoniaApiError as exc:
        raise _map_error(exc) from exc


# --- Contractors ---
# Fixed routes (sync, catalogs, kinds, filter) MUST be registered
# before the parameterized route /{contractor_id}.


@router.get("/api/v1/contractors")
async def list_contractors(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
) -> dict[str, Any]:
    client = _get_client()
    try:
        items = await client.list_contractors()
        if isinstance(items, list):
            total = len(items)
            start = (page - 1) * page_size
            end = start + page_size
            return {"items": items[start:end], "total": total, "page": page, "page_size": page_size}
        return {"items": items, "total": 0, "page": page, "page_size": page_size}
    except SymfoniaApiError as exc:
        raise _map_error(exc) from exc


@router.post("/api/v1/contractors")
async def create_contractor(data: ContractorCreate) -> dict[str, Any]:
    client = _get_client()
    try:
        return await client.create_contractor(data.to_symfonia_payload())
    except SymfoniaApiError as exc:
        raise _map_error(exc) from exc


@router.put("/api/v1/contractors")
async def update_contractor(data: ContractorUpdate) -> dict[str, Any]:
    client = _get_client()
    try:
        return await client.update_contractor(data.to_symfonia_payload())
    except SymfoniaApiError as exc:
        raise _map_error(exc) from exc


@router.patch("/api/v1/contractors/filter")
async def filter_contractors(data: FilterRequest) -> dict[str, Any]:
    client = _get_client()
    try:
        if data.mode == "sql":
            items = await client.filter_contractors_sql({"Sql": data.query})
        else:
            items = await client.filter_contractors({"Filter": data.query})
        return {"items": items, "total": len(items) if isinstance(items, list) else 0}
    except SymfoniaApiError as exc:
        raise _map_error(exc) from exc


@router.get("/api/v1/contractors/sync")
async def sync_contractors(date_from: str = Query(..., description="ISO date, e.g. 2024-01-01")) -> dict[str, Any]:
    client = _get_client()
    try:
        items = await client.sync_contractors(date_from)
        return {"items": items, "total": len(items) if isinstance(items, list) else 0}
    except SymfoniaApiError as exc:
        raise _map_error(exc) from exc


@router.get("/api/v1/contractors/catalogs")
async def contractor_catalogs() -> dict[str, Any]:
    client = _get_client()
    try:
        return {"catalogs": await client.get_contractor_catalogs()}
    except SymfoniaApiError as exc:
        raise _map_error(exc) from exc


@router.get("/api/v1/contractors/kinds")
async def contractor_kinds() -> dict[str, Any]:
    client = _get_client()
    try:
        return {"kinds": await client.get_contractor_kinds()}
    except SymfoniaApiError as exc:
        raise _map_error(exc) from exc


@router.get("/api/v1/contractors/{contractor_id}")
async def get_contractor(contractor_id: str) -> dict[str, Any]:
    client = _get_client()
    try:
        if contractor_id.isdigit():
            return await client.get_contractor_by_id(int(contractor_id))
        return await client.get_contractor_by_code(contractor_id)
    except SymfoniaApiError as exc:
        raise _map_error(exc) from exc


# --- Products ---
# Fixed routes MUST be registered before /{product_id}.


@router.get("/api/v1/products")
async def list_products(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
) -> dict[str, Any]:
    client = _get_client()
    try:
        items = await client.list_products()
        if isinstance(items, list):
            total = len(items)
            start = (page - 1) * page_size
            end = start + page_size
            return {"items": items[start:end], "total": total, "page": page, "page_size": page_size}
        return {"items": items, "total": 0, "page": page, "page_size": page_size}
    except SymfoniaApiError as exc:
        raise _map_error(exc) from exc


@router.post("/api/v1/products")
async def create_product(data: ProductCreate) -> dict[str, Any]:
    client = _get_client()
    try:
        return await client.create_product(data.to_symfonia_payload())
    except SymfoniaApiError as exc:
        raise _map_error(exc) from exc


@router.put("/api/v1/products")
async def update_product(data: ProductUpdate) -> dict[str, Any]:
    client = _get_client()
    try:
        return await client.update_product(data.to_symfonia_payload())
    except SymfoniaApiError as exc:
        raise _map_error(exc) from exc


@router.patch("/api/v1/products/filter")
async def filter_products(data: FilterRequest) -> dict[str, Any]:
    client = _get_client()
    try:
        if data.mode == "sql":
            items = await client.filter_products_sql({"Sql": data.query})
        else:
            items = await client.filter_products({"Filter": data.query})
        return {"items": items, "total": len(items) if isinstance(items, list) else 0}
    except SymfoniaApiError as exc:
        raise _map_error(exc) from exc


@router.get("/api/v1/products/sync")
async def sync_products(date_from: str = Query(...)) -> dict[str, Any]:
    client = _get_client()
    try:
        items = await client.sync_products(date_from)
        return {"items": items, "total": len(items) if isinstance(items, list) else 0}
    except SymfoniaApiError as exc:
        raise _map_error(exc) from exc


@router.get("/api/v1/products/{product_id}")
async def get_product(product_id: str) -> dict[str, Any]:
    client = _get_client()
    try:
        if product_id.isdigit():
            return await client.get_product_by_id(int(product_id))
        return await client.get_product_by_code(product_id)
    except SymfoniaApiError as exc:
        raise _map_error(exc) from exc


@router.get("/api/v1/products/{product_id}/barcodes")
async def product_barcodes(product_id: str) -> dict[str, Any]:
    client = _get_client()
    try:
        if product_id.isdigit():
            barcodes = await client.get_product_barcodes(product_id=int(product_id))
        else:
            barcodes = await client.get_product_barcodes(product_code=product_id)
        return {"barcodes": barcodes}
    except SymfoniaApiError as exc:
        raise _map_error(exc) from exc


# --- Sales Documents ---
# Fixed routes MUST be registered before /{document_id}.


@router.get("/api/v1/sales")
async def list_sales(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
) -> dict[str, Any]:
    client = _get_client()
    try:
        items = await client.list_sales()
        if isinstance(items, list):
            total = len(items)
            start = (page - 1) * page_size
            end = start + page_size
            return {"items": items[start:end], "total": total, "page": page, "page_size": page_size}
        return {"items": items, "total": 0, "page": page, "page_size": page_size}
    except SymfoniaApiError as exc:
        raise _map_error(exc) from exc


@router.get("/api/v1/sales/filter")
async def filter_sales(
    date_from: str = Query(...),
    date_to: str = Query(...),
    buyer_code: str | None = None,
    buyer_id: int | None = None,
) -> dict[str, Any]:
    client = _get_client()
    try:
        items = await client.filter_sales(date_from, date_to, buyer_code=buyer_code, buyer_id=buyer_id)
        return {"items": items, "total": len(items) if isinstance(items, list) else 0}
    except SymfoniaApiError as exc:
        raise _map_error(exc) from exc


@router.get("/api/v1/sales/sync")
async def sync_sales(date_from: str = Query(...)) -> dict[str, Any]:
    client = _get_client()
    try:
        items = await client.sync_sales(date_from)
        return {"items": items, "total": len(items) if isinstance(items, list) else 0}
    except SymfoniaApiError as exc:
        raise _map_error(exc) from exc


@router.get("/api/v1/sales/{document_id}")
async def get_sale(document_id: str) -> dict[str, Any]:
    client = _get_client()
    try:
        if document_id.isdigit():
            return await client.get_sale_by_id(int(document_id))
        return await client.get_sale_by_number(document_id)
    except SymfoniaApiError as exc:
        raise _map_error(exc) from exc


@router.get("/api/v1/sales/{document_id}/status")
async def sale_status(document_id: str) -> dict[str, Any]:
    client = _get_client()
    try:
        if document_id.isdigit():
            return await client.get_sale_status(document_id=int(document_id))
        return await client.get_sale_status(number=document_id)
    except SymfoniaApiError as exc:
        raise _map_error(exc) from exc


@router.get("/api/v1/sales/{document_id}/pdf")
async def sale_pdf(document_id: str) -> dict[str, Any]:
    client = _get_client()
    try:
        if document_id.isdigit():
            pdf_base64 = await client.get_sale_pdf(document_id=int(document_id))
        else:
            pdf_base64 = await client.get_sale_pdf(number=document_id)
        return {"pdf_base64": pdf_base64}
    except SymfoniaApiError as exc:
        raise _map_error(exc) from exc


# --- Purchase Documents ---
# Fixed routes MUST be registered before /{document_id}.


@router.get("/api/v1/purchases")
async def list_purchases(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
) -> dict[str, Any]:
    client = _get_client()
    try:
        items = await client.list_purchases()
        if isinstance(items, list):
            total = len(items)
            start = (page - 1) * page_size
            end = start + page_size
            return {"items": items[start:end], "total": total, "page": page, "page_size": page_size}
        return {"items": items, "total": 0, "page": page, "page_size": page_size}
    except SymfoniaApiError as exc:
        raise _map_error(exc) from exc


@router.get("/api/v1/purchases/filter")
async def filter_purchases(
    date_from: str = Query(...),
    date_to: str = Query(...),
    supplier_code: str | None = None,
    supplier_id: int | None = None,
) -> dict[str, Any]:
    client = _get_client()
    try:
        items = await client.filter_purchases(date_from, date_to, supplier_code=supplier_code, supplier_id=supplier_id)
        return {"items": items, "total": len(items) if isinstance(items, list) else 0}
    except SymfoniaApiError as exc:
        raise _map_error(exc) from exc


@router.get("/api/v1/purchases/sync")
async def sync_purchases(date_from: str = Query(...)) -> dict[str, Any]:
    client = _get_client()
    try:
        items = await client.sync_purchases(date_from)
        return {"items": items, "total": len(items) if isinstance(items, list) else 0}
    except SymfoniaApiError as exc:
        raise _map_error(exc) from exc


@router.get("/api/v1/purchases/{document_id}")
async def get_purchase(document_id: str) -> dict[str, Any]:
    client = _get_client()
    try:
        if document_id.isdigit():
            return await client.get_purchase_by_id(int(document_id))
        return await client.get_purchase_by_number(document_id)
    except SymfoniaApiError as exc:
        raise _map_error(exc) from exc


@router.get("/api/v1/purchases/{document_id}/status")
async def purchase_status(document_id: str) -> dict[str, Any]:
    client = _get_client()
    try:
        if document_id.isdigit():
            return await client.get_purchase_status(document_id=int(document_id))
        return await client.get_purchase_status(number=document_id)
    except SymfoniaApiError as exc:
        raise _map_error(exc) from exc


# --- Orders (foreign / ZMO) ---
# Fixed routes MUST be registered before /{order_id}.


@router.get("/api/v1/orders")
async def list_orders(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
) -> dict[str, Any]:
    client = _get_client()
    try:
        items = await client.list_orders()
        if isinstance(items, list):
            total = len(items)
            start = (page - 1) * page_size
            end = start + page_size
            return {"items": items[start:end], "total": total, "page": page, "page_size": page_size}
        return {"items": items, "total": 0, "page": page, "page_size": page_size}
    except SymfoniaApiError as exc:
        raise _map_error(exc) from exc


@router.get("/api/v1/orders/filter")
async def filter_orders(
    date_from: str = Query(...),
    date_to: str = Query(...),
    recipient_code: str | None = None,
    recipient_id: int | None = None,
) -> dict[str, Any]:
    client = _get_client()
    try:
        items = await client.filter_orders(date_from, date_to, recipient_code=recipient_code, recipient_id=recipient_id)
        return {"items": items, "total": len(items) if isinstance(items, list) else 0}
    except SymfoniaApiError as exc:
        raise _map_error(exc) from exc


@router.get("/api/v1/orders/sync")
async def sync_orders(date_from: str = Query(...)) -> dict[str, Any]:
    client = _get_client()
    try:
        items = await client.sync_orders(date_from)
        return {"items": items, "total": len(items) if isinstance(items, list) else 0}
    except SymfoniaApiError as exc:
        raise _map_error(exc) from exc


@router.get("/api/v1/orders/{order_id}")
async def get_order(order_id: str) -> dict[str, Any]:
    client = _get_client()
    try:
        if order_id.isdigit():
            return await client.get_order_by_id(int(order_id))
        return await client.get_order_by_number(order_id)
    except SymfoniaApiError as exc:
        raise _map_error(exc) from exc


@router.get("/api/v1/orders/{order_id}/status")
async def order_status(order_id: str) -> dict[str, Any]:
    client = _get_client()
    try:
        if order_id.isdigit():
            return await client.get_order_status(order_id=int(order_id))
        return await client.get_order_status(number=order_id)
    except SymfoniaApiError as exc:
        raise _map_error(exc) from exc


# --- Own Orders (ZMW) ---


@router.get("/api/v1/own-orders")
async def list_own_orders(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
) -> dict[str, Any]:
    client = _get_client()
    try:
        items = await client.list_own_orders()
        if isinstance(items, list):
            total = len(items)
            start = (page - 1) * page_size
            end = start + page_size
            return {"items": items[start:end], "total": total, "page": page, "page_size": page_size}
        return {"items": items, "total": 0, "page": page, "page_size": page_size}
    except SymfoniaApiError as exc:
        raise _map_error(exc) from exc


@router.get("/api/v1/own-orders/{order_id}")
async def get_own_order(order_id: str) -> dict[str, Any]:
    client = _get_client()
    try:
        if not order_id.isdigit():
            raise HTTPException(status_code=400, detail="Own order ID must be numeric")
        return await client.get_own_order_by_id(int(order_id))
    except SymfoniaApiError as exc:
        raise _map_error(exc) from exc


# --- Inventory / Stock ---
# Fixed route /changes MUST be registered before /{product_id}.


@router.get("/api/v1/inventory")
async def inventory_states(
    warehouse_id: int | None = None,
    warehouse_code: str | None = None,
) -> dict[str, Any]:
    client = _get_client()
    try:
        if warehouse_id is not None:
            items = await client.get_inventory_by_warehouse_id(warehouse_id)
        elif warehouse_code is not None:
            items = await client.get_inventory_by_warehouse_code(warehouse_code)
        else:
            items = await client.get_inventory_all()
        total = len(items) if isinstance(items, list) else 0
        return {"items": items, "total_products": total}
    except SymfoniaApiError as exc:
        raise _map_error(exc) from exc


@router.get("/api/v1/inventory/changes")
async def inventory_changes() -> dict[str, Any]:
    client = _get_client()
    try:
        items = await client.get_inventory_changes()
        return {"items": items, "total": len(items) if isinstance(items, list) else 0}
    except SymfoniaApiError as exc:
        raise _map_error(exc) from exc


@router.get("/api/v1/inventory/{product_id}")
async def inventory_by_product(product_id: str) -> dict[str, Any]:
    client = _get_client()
    try:
        if product_id.isdigit():
            items = await client.get_inventory_by_product_id(int(product_id))
        else:
            items = await client.get_inventory_by_product_code(product_id)
        return {"items": items, "total_products": len(items) if isinstance(items, list) else 0}
    except SymfoniaApiError as exc:
        raise _map_error(exc) from exc


# --- Payments ---


@router.get("/api/v1/payments")
async def list_payments(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
) -> dict[str, Any]:
    client = _get_client()
    try:
        items = await client.list_payments()
        if isinstance(items, list):
            total = len(items)
            start = (page - 1) * page_size
            end = start + page_size
            return {"items": items[start:end], "total": total, "page": page, "page_size": page_size}
        return {"items": items, "total": 0, "page": page, "page_size": page_size}
    except SymfoniaApiError as exc:
        raise _map_error(exc) from exc


# --- Warehouses (dictionary) ---


@router.get("/api/v1/warehouses")
async def list_warehouses() -> dict[str, Any]:
    client = _get_client()
    try:
        return {"warehouses": await client.list_warehouses()}
    except SymfoniaApiError as exc:
        raise _map_error(exc) from exc
