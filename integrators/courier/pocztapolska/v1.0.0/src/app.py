"""Poczta Polska Courier Integrator — FastAPI application."""

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
from src.integration import PocztaPolskaIntegration
from src.schemas import (
    CreateShipmentRequest,
    LabelRequest,
    PocztaPolskaCredentials,
    PointsRequest,
)

logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s %(levelname)-8s %(name)s — %(message)s",
)
logger = logging.getLogger("courier-pocztapolska")

app = FastAPI(
    title="Poczta Polska Courier Connector",
    version="1.0.0",
    docs_url="/docs",
)

integration = PocztaPolskaIntegration()


@app.get("/health")
async def health():
    return {"status": "healthy", "version": "1.0.0", "system": "pocztapolska"}


@app.get("/readiness")
async def readiness():
    checks = {
        "tracking_client": "ok" if integration.tracking_client else "unavailable",
        "posting_client": "ok" if integration.posting_client else "unavailable",
    }
    status = "healthy" if all(v == "ok" for v in checks.values()) else "degraded"
    return {"status": status, "checks": checks}


@app.post("/shipments")
async def create_shipment(request: CreateShipmentRequest):
    try:
        result, status_code = integration.create_order(request.credentials, request)
        return JSONResponse(content=result, status_code=status_code)
    except Exception as exc:
        logger.exception("Failed to create Poczta Polska shipment")
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/shipments/{order_id}/status")
async def get_status(
    order_id: str,
    login: str = Query(...),
    password: str = Query(...),
):
    credentials = PocztaPolskaCredentials(login=login, password=password)
    try:
        result, status_code = integration.get_order_status(credentials, order_id)
        return JSONResponse(content={"status": result}, status_code=status_code)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/shipments/{order_id}/tracking")
async def get_tracking(order_id: str):
    result, status_code = integration.get_tracking_info(order_id)
    return JSONResponse(content=result, status_code=status_code)


@app.post("/labels")
async def get_label(request: LabelRequest):
    try:
        args: dict = {}
        if request.external_id:
            args["external_id"] = request.external_id
        label_bytes, status_code = integration.get_waybill_label_bytes(
            request.credentials, request.waybill_numbers, args
        )
        if status_code == 200:
            return Response(content=label_bytes, media_type="application/pdf")
        return JSONResponse(content={"error": label_bytes}, status_code=status_code)
    except Exception as exc:
        logger.exception("Failed to get Poczta Polska label")
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/points")
async def get_points(request: PointsRequest):
    try:
        result, status_code = integration.get_points(
            request.credentials, request.voivodeship_id
        )
        return JSONResponse(content=result, status_code=status_code)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


if augment_legacy_fastapi_app is not None:
    app = augment_legacy_fastapi_app(
        app,
        manifest_path=Path(__file__).resolve().parent.parent / "connector.yaml",
    )
