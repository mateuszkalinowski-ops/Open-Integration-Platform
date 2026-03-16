"""REST API routes for the InsERT Nexo cloud connector.

All entity operations are proxied to the on-premise agent.
"""

import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Query

logger = logging.getLogger(__name__)

from src.api.dependencies import app_state

router = APIRouter()


def _get_proxy(account: str):  # type: ignore[no-untyped-def]
    if not app_state.account_manager:
        raise HTTPException(status_code=503, detail="Service not initialized")
    proxy = app_state.account_manager.get_proxy(account)
    if not proxy:
        raise HTTPException(status_code=404, detail=f"Agent account not found: {account}")
    return proxy


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
            logger.error("InsERT Nexo readiness check failed: %s", data)
            raise HTTPException(status_code=503, detail="Service unavailable")
        return data
    return {"status": "ready"}


@router.get("/accounts")
async def list_accounts() -> dict[str, Any]:
    if not app_state.account_manager:
        raise HTTPException(status_code=503, detail="Service not initialized")
    accounts = app_state.account_manager.list_accounts()
    return {"accounts": [{"name": a.name, "agent_url": a.agent_url, "environment": a.environment} for a in accounts]}


@router.get("/agents/{account}/health")
async def agent_health(account: str) -> dict[str, Any]:
    proxy = _get_proxy(account)
    try:
        return await proxy.health()
    except Exception:
        logger.exception("InsERT Nexo agent unreachable")
        raise HTTPException(status_code=502, detail="Agent unreachable")


@router.get("/agents/{account}/connection/status")
async def agent_connection_status(account: str) -> dict[str, Any]:
    proxy = _get_proxy(account)
    try:
        return await proxy.get("/connection/status")
    except Exception:
        logger.exception("InsERT Nexo agent unreachable")
        raise HTTPException(status_code=502, detail="Agent unreachable")


# --- Contractors ---


@router.get("/agents/{account}/contractors")
async def list_contractors(
    account: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    search: str | None = None,
) -> dict[str, Any]:
    proxy = _get_proxy(account)
    params: dict[str, Any] = {"page": page, "page_size": page_size}
    if search:
        params["search"] = search
    return await proxy.get("/contractors", params=params)


@router.get("/agents/{account}/contractors/{symbol}")
async def get_contractor(account: str, symbol: str) -> dict[str, Any]:
    proxy = _get_proxy(account)
    return await proxy.get(f"/contractors/{symbol}")


@router.post("/agents/{account}/contractors")
async def create_contractor(account: str, data: dict[str, Any]) -> dict[str, Any]:
    proxy = _get_proxy(account)
    return await proxy.post("/contractors", json_body=data)


@router.put("/agents/{account}/contractors/{symbol}")
async def update_contractor(account: str, symbol: str, data: dict[str, Any]) -> dict[str, Any]:
    proxy = _get_proxy(account)
    return await proxy.put(f"/contractors/{symbol}", json_body=data)


@router.delete("/agents/{account}/contractors/{symbol}")
async def delete_contractor(account: str, symbol: str) -> dict[str, Any]:
    proxy = _get_proxy(account)
    return await proxy.delete(f"/contractors/{symbol}")


# --- Products ---


@router.get("/agents/{account}/products")
async def list_products(
    account: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    search: str | None = None,
) -> dict[str, Any]:
    proxy = _get_proxy(account)
    params: dict[str, Any] = {"page": page, "page_size": page_size}
    if search:
        params["search"] = search
    return await proxy.get("/products", params=params)


@router.get("/agents/{account}/products/{symbol}")
async def get_product(account: str, symbol: str) -> dict[str, Any]:
    proxy = _get_proxy(account)
    return await proxy.get(f"/products/{symbol}")


@router.post("/agents/{account}/products")
async def create_product(account: str, data: dict[str, Any]) -> dict[str, Any]:
    proxy = _get_proxy(account)
    return await proxy.post("/products", json_body=data)


@router.put("/agents/{account}/products/{symbol}")
async def update_product(account: str, symbol: str, data: dict[str, Any]) -> dict[str, Any]:
    proxy = _get_proxy(account)
    return await proxy.put(f"/products/{symbol}", json_body=data)


# --- Documents ---


@router.get("/agents/{account}/documents/sales")
async def list_sales_documents(
    account: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
) -> dict[str, Any]:
    proxy = _get_proxy(account)
    return await proxy.get("/documents/sales", params={"page": page, "page_size": page_size})


@router.post("/agents/{account}/documents/sales")
async def create_sales_document(account: str, data: dict[str, Any]) -> dict[str, Any]:
    proxy = _get_proxy(account)
    return await proxy.post("/documents/sales", json_body=data)


@router.get("/agents/{account}/documents/warehouse/issues")
async def list_warehouse_issues(account: str, page: int = 1, page_size: int = 50) -> dict[str, Any]:
    proxy = _get_proxy(account)
    return await proxy.get("/documents/warehouse/issues", params={"page": page, "page_size": page_size})


@router.post("/agents/{account}/documents/warehouse/issue")
async def create_warehouse_issue(account: str, data: dict[str, Any]) -> dict[str, Any]:
    proxy = _get_proxy(account)
    return await proxy.post("/documents/warehouse/issue", json_body=data)


@router.post("/agents/{account}/documents/warehouse/receipt")
async def create_warehouse_receipt(account: str, data: dict[str, Any]) -> dict[str, Any]:
    proxy = _get_proxy(account)
    return await proxy.post("/documents/warehouse/receipt", json_body=data)


# --- Orders ---


@router.get("/agents/{account}/orders")
async def list_orders(
    account: str,
    order_type: str = "from_customer",
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
) -> dict[str, Any]:
    proxy = _get_proxy(account)
    return await proxy.get("/orders", params={"order_type": order_type, "page": page, "page_size": page_size})


@router.post("/agents/{account}/orders")
async def create_order(account: str, data: dict[str, Any]) -> dict[str, Any]:
    proxy = _get_proxy(account)
    return await proxy.post("/orders", json_body=data)


# --- Stock ---


@router.get("/agents/{account}/stock")
async def get_stock_levels(
    account: str,
    warehouse: str | None = None,
    only_available: bool = False,
) -> dict[str, Any]:
    proxy = _get_proxy(account)
    params: dict[str, Any] = {"only_available": only_available}
    if warehouse:
        params["warehouse"] = warehouse
    return await proxy.get("/stock", params=params)


@router.get("/agents/{account}/stock/{product_symbol}")
async def get_stock_for_product(account: str, product_symbol: str) -> dict[str, Any]:
    proxy = _get_proxy(account)
    return await proxy.get(f"/stock/{product_symbol}")


# --- Agent sync endpoint (receives data pushed from on-premise agent) ---


@router.post("/agents/heartbeat")
async def receive_heartbeat(data: dict[str, Any]) -> dict[str, str]:
    # Store heartbeat in memory / database for dashboard display
    return {"status": "ok"}


@router.post("/agents/sync")
async def receive_sync(data: dict[str, Any]) -> dict[str, str]:
    # Process sync payload from on-premise agent
    return {"status": "ok"}
