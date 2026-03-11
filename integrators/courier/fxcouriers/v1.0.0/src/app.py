"""FX Couriers (KurierSystem) Courier Integrator — FastAPI application."""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Optional

SDK_PYTHON_PATH = Path(__file__).resolve().parents[5] / "sdk/python"
if str(SDK_PYTHON_PATH) not in sys.path:
    sys.path.insert(0, str(SDK_PYTHON_PATH))

from fastapi import FastAPI, HTTPException, Query, Response
from fastapi.responses import JSONResponse
from pinquark_connector_sdk.legacy import augment_legacy_fastapi_app

from src.config import settings
from src.integration import FxCouriersIntegration
from src.schemas import (
    CreateOrderApiRequest,
    CreatePickupApiRequest,
    FxCouriersCredentials,
    LabelRequest,
)

logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s %(levelname)-8s %(name)s — %(message)s",
)
logger = logging.getLogger("courier-fxcouriers")

app = FastAPI(
    title="FX Couriers Connector",
    version="1.0.0",
    docs_url="/docs",
)

integration = FxCouriersIntegration()


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

@app.get("/health")
async def health():
    return {"status": "healthy", "version": "1.0.0", "system": "fxcouriers"}


@app.get("/readiness")
async def readiness():
    checks = {"api_reachable": "ok"}
    status = "healthy" if all(v == "ok" for v in checks.values()) else "degraded"
    return {"status": status, "checks": checks}


# ---------------------------------------------------------------------------
# Services
# ---------------------------------------------------------------------------

@app.get("/services")
async def get_services(
    api_token: str = Query(...),
):
    credentials = FxCouriersCredentials(api_token=api_token)
    try:
        result, status_code = await integration.get_services(credentials)
        if status_code >= 400:
            raise HTTPException(status_code=status_code, detail=result)
        return result
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


# ---------------------------------------------------------------------------
# Company
# ---------------------------------------------------------------------------

@app.get("/company/{company_id}")
async def get_company(
    company_id: int,
    api_token: str = Query(...),
):
    credentials = FxCouriersCredentials(api_token=api_token)
    try:
        result, status_code = await integration.get_company(credentials, company_id)
        if status_code >= 400:
            raise HTTPException(status_code=status_code, detail=result)
        return result
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


# ---------------------------------------------------------------------------
# Orders
# ---------------------------------------------------------------------------

@app.post("/shipments", status_code=201)
async def create_order(request: CreateOrderApiRequest):
    try:
        result, status_code = await integration.create_order(
            request.credentials, request,
        )
        if status_code >= 400:
            raise HTTPException(status_code=status_code, detail=result)
        return JSONResponse(content=result, status_code=status_code)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Failed to create FX Couriers order")
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/shipments")
async def get_orders(
    api_token: str = Query(...),
    since: Optional[str] = Query(default=None, description="YYYY-MM-DD"),
    offset: Optional[int] = Query(default=None),
    company_id: Optional[int] = Query(default=None),
):
    credentials = FxCouriersCredentials(api_token=api_token)
    try:
        result, status_code = await integration.get_orders(
            credentials, since=since, offset=offset, company_id=company_id,
        )
        if status_code >= 400:
            raise HTTPException(status_code=status_code, detail=result)
        return result
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/shipments/by-number/{order_number}")
async def find_order_by_number(
    order_number: str,
    api_token: str = Query(...),
):
    """Find order by order_number (e.g. E000123) and return full order with order_id."""
    credentials = FxCouriersCredentials(api_token=api_token)
    try:
        result, status_code = await integration.find_order_by_number(
            credentials, order_number,
        )
        if status_code >= 400:
            raise HTTPException(status_code=status_code, detail=result)
        return result
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/shipments/{order_id}")
async def get_order(
    order_id: int,
    api_token: str = Query(...),
):
    credentials = FxCouriersCredentials(api_token=api_token)
    try:
        result, status_code = await integration.get_order(credentials, order_id)
        if status_code >= 400:
            raise HTTPException(status_code=status_code, detail=result)
        return result
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.delete("/shipments/{order_id}")
async def delete_order(
    order_id: int,
    api_token: str = Query(...),
):
    credentials = FxCouriersCredentials(api_token=api_token)
    try:
        result, status_code = await integration.delete_order(credentials, order_id)
        if status_code >= 400:
            raise HTTPException(status_code=status_code, detail=result)
        return {"result": result}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


# ---------------------------------------------------------------------------
# Status & Tracking
# ---------------------------------------------------------------------------

@app.get("/shipments/{order_id}/status")
async def get_order_status(
    order_id: int,
    api_token: str = Query(...),
):
    credentials = FxCouriersCredentials(api_token=api_token)
    try:
        result, status_code = await integration.get_order_status(credentials, order_id)
        if status_code >= 400:
            raise HTTPException(status_code=status_code, detail=result)
        return result
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/tracking/{order_id}")
async def get_tracking(
    order_id: int,
    api_token: str = Query(...),
):
    credentials = FxCouriersCredentials(api_token=api_token)
    try:
        result, status_code = await integration.get_tracking(credentials, order_id)
        if status_code >= 400:
            raise HTTPException(status_code=status_code, detail=result)
        return result
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


# ---------------------------------------------------------------------------
# Labels
# ---------------------------------------------------------------------------

@app.post("/labels")
async def get_label(request: LabelRequest):
    import base64

    try:
        label_data, status_code = await integration.get_label(
            request.credentials, request.order_id,
        )
        if status_code >= 400:
            raise HTTPException(status_code=status_code, detail=label_data)
        label_b64 = base64.b64encode(label_data).decode("ascii")
        return {
            "order_id": request.order_id,
            "format": "pdf",
            "label_base64": label_b64,
        }
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Failed to get FX Couriers label")
        raise HTTPException(status_code=400, detail=str(exc)) from exc


# ---------------------------------------------------------------------------
# Pickup (Shipment scheduling)
# ---------------------------------------------------------------------------

@app.post("/pickups", status_code=201)
async def create_pickup(request: CreatePickupApiRequest):
    try:
        result, status_code = await integration.create_shipment(
            request.credentials, request,
        )
        if status_code >= 400:
            raise HTTPException(status_code=status_code, detail=result)
        return JSONResponse(content=result, status_code=status_code)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Failed to create FX Couriers pickup")
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/pickups/{order_id}")
async def get_pickup(
    order_id: int,
    api_token: str = Query(...),
):
    credentials = FxCouriersCredentials(api_token=api_token)
    try:
        result, status_code = await integration.get_shipment(credentials, order_id)
        if status_code >= 400:
            raise HTTPException(status_code=status_code, detail=result)
        return result
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.delete("/pickups/{order_id}")
async def cancel_pickup(
    order_id: int,
    api_token: str = Query(...),
):
    credentials = FxCouriersCredentials(api_token=api_token)
    try:
        result, status_code = await integration.cancel_shipment(credentials, order_id)
        if status_code >= 400:
            raise HTTPException(status_code=status_code, detail=result)
        return {"result": result}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


app = augment_legacy_fastapi_app(
    app,
    manifest_path=Path(__file__).resolve().parent.parent / "connector.yaml",
)
