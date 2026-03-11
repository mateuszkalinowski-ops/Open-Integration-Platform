"""Schenker Courier Integrator — FastAPI application."""

import logging
import sys
from pathlib import Path

SDK_PYTHON_PATH = Path(__file__).resolve().parents[5] / "sdk/python"
if str(SDK_PYTHON_PATH) not in sys.path:
    sys.path.insert(0, str(SDK_PYTHON_PATH))

from fastapi import FastAPI, HTTPException, Query, Response
from fastapi.responses import JSONResponse
from pinquark_connector_sdk.legacy import augment_legacy_fastapi_app

from src.config import settings
from src.integration import SchenkerIntegration
from src.schemas import (
    CreateShipmentRequest,
    DeleteOrderRequest,
    LabelRequest,
    SchenkerCredentials,
)

logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s %(levelname)-8s %(name)s — %(message)s",
)
logger = logging.getLogger("courier-schenker")

app = FastAPI(
    title="Schenker Courier Connector",
    version="1.0.0",
    docs_url="/docs",
)

integration = SchenkerIntegration()


@app.get("/health")
async def health():
    return {"status": "healthy", "version": "1.0.0", "system": "schenker"}


@app.get("/readiness")
async def readiness():
    checks = {"soap_client": "ok" if integration.client else "unavailable"}
    status = "healthy" if all(v == "ok" for v in checks.values()) else "degraded"
    return {"status": status, "checks": checks}


@app.post("/shipments")
async def create_shipment(request: CreateShipmentRequest):
    try:
        result, status_code = integration.create_order(request.credentials, request)
        return JSONResponse(content=result, status_code=status_code)
    except Exception as exc:
        logger.exception("Failed to create Schenker shipment")
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/shipments/{waybill_number}/status")
async def get_status(
    waybill_number: str,
    login: str = Query(...),
    password: str = Query(...),
    credentials_id: str = Query(""),
):
    credentials = SchenkerCredentials(
        login=login, password=password, credentials_id=credentials_id
    )
    try:
        result, status_code = integration.get_order_status(credentials, waybill_number)
        return JSONResponse(content={"status": result}, status_code=status_code)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/shipments/{waybill_number}/tracking")
async def get_tracking(waybill_number: str):
    result, status_code = integration.get_tracking_info(waybill_number)
    return JSONResponse(content=result, status_code=status_code)


@app.post("/labels")
async def get_label(request: LabelRequest):
    try:
        label_bytes, status_code = integration.get_waybill_label_bytes(
            request.credentials, request.waybill_numbers, {}
        )
        if status_code == 200:
            return Response(content=label_bytes, media_type="application/pdf")
        return JSONResponse(content={"error": label_bytes}, status_code=status_code)
    except Exception as exc:
        logger.exception("Failed to get Schenker label")
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.delete("/shipments/{waybill_number}")
async def cancel_shipment(
    waybill_number: str,
    login: str = Query(...),
    password: str = Query(...),
    credentials_id: str = Query(""),
):
    credentials = SchenkerCredentials(
        login=login, password=password, credentials_id=credentials_id
    )
    try:
        result, status_code = integration.delete_order(credentials, waybill_number)
        return JSONResponse(content=result, status_code=status_code)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


app = augment_legacy_fastapi_app(
    app,
    manifest_path=Path(__file__).resolve().parent.parent / "connector.yaml",
)
