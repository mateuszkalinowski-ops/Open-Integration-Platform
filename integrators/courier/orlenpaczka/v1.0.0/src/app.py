"""Orlen Paczka Courier Integrator — FastAPI application."""

import logging
import sys
from pathlib import Path

try:
    SDK_PYTHON_PATH = Path(__file__).resolve().parents[5] / "sdk/python"
    if SDK_PYTHON_PATH.exists() and str(SDK_PYTHON_PATH) not in sys.path:
        sys.path.insert(0, str(SDK_PYTHON_PATH))
except (IndexError, OSError):
    pass

from fastapi import FastAPI, HTTPException, Query, Response
from fastapi.responses import JSONResponse
try:
    from pinquark_connector_sdk.legacy import augment_legacy_fastapi_app
except ImportError:
    augment_legacy_fastapi_app = None  # type: ignore[assignment,misc]

from src.config import settings
from src.integration import OrlenPaczkaIntegration
from src.schemas import (
    CreateOrderRequest,
    DeleteRequest,
    LabelRequest,
    OrlenPaczkaCredentials,
    PointsRequest,
    StatusRequest,
)

logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s %(levelname)-8s %(name)s — %(message)s",
)
logger = logging.getLogger("courier-orlenpaczka")

app = FastAPI(
    title="Orlen Paczka Courier Connector",
    version="1.0.0",
    docs_url="/docs",
)

integration = OrlenPaczkaIntegration()


@app.get("/health")
async def health():
    return {"status": "healthy", "version": "1.0.0", "system": "orlenpaczka"}


@app.get("/readiness")
async def readiness():
    checks = {"soap_client": "ok" if integration.client else "unavailable"}
    status = "healthy" if all(v == "ok" for v in checks.values()) else "degraded"
    return {"status": status, "checks": checks}


@app.post("/shipments")
async def create_shipment(request: CreateOrderRequest):
    try:
        result, status_code = integration.create_order(request.credentials, request.command)
        if status_code >= 400:
            raise HTTPException(status_code=status_code, detail=str(result))
        return JSONResponse(
            content=result.model_dump() if hasattr(result, "model_dump") else result,
            status_code=status_code,
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Failed to create Orlen Paczka shipment")
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/shipments/status")
async def get_status(request: StatusRequest):
    try:
        result, status_code = integration.get_order_status(request.credentials, request.order_id)
        if status_code >= 400:
            raise HTTPException(status_code=status_code, detail=str(result))
        return {"status": result}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/shipments/{order_id}/tracking")
async def get_tracking(order_id: str):
    result, status_code = integration.get_tracking_info(order_id)
    return result.model_dump()


@app.post("/labels")
async def get_label(request: LabelRequest):
    try:
        label_data, status_code = integration.get_waybill_label_bytes(
            request.credentials, request.waybill_numbers
        )
        if status_code >= 400:
            raise HTTPException(status_code=status_code, detail=str(label_data))
        return Response(content=label_data, media_type="application/pdf")
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Failed to get Orlen Paczka label")
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/shipments/delete")
async def cancel_shipment(request: DeleteRequest):
    try:
        result, status_code = integration.delete_order(request.credentials, request.order_id)
        if status_code >= 400:
            raise HTTPException(status_code=status_code, detail=str(result))
        return JSONResponse(content=result, status_code=status_code)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/points")
async def get_points(request: PointsRequest):
    try:
        result, status_code = integration.get_points(request.credentials)
        if status_code >= 400:
            raise HTTPException(status_code=status_code, detail=str(result))
        return result
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


if augment_legacy_fastapi_app is not None:
    app = augment_legacy_fastapi_app(
        app,
        manifest_path=Path(__file__).resolve().parent.parent / "connector.yaml",
    )
