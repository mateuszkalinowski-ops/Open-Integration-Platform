"""Paxy Courier Integrator — FastAPI application."""

import logging
import sys
from pathlib import Path

SDK_PYTHON_PATH = Path(__file__).resolve().parents[5] / "sdk/python"
if str(SDK_PYTHON_PATH) not in sys.path:
    sys.path.insert(0, str(SDK_PYTHON_PATH))

from fastapi import FastAPI, HTTPException, Response
from fastapi.responses import JSONResponse
from pinquark_connector_sdk.legacy import augment_legacy_fastapi_app

from src.config import settings
from src.integration import PaxyIntegration
from src.schemas import CreateShipmentRequest, DeleteRequest, LabelRequest, StatusRequest

logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s %(levelname)-8s %(name)s — %(message)s",
)
logger = logging.getLogger("courier-paxy")

app = FastAPI(
    title="Paxy Courier Connector",
    version="1.0.0",
    docs_url="/docs",
)

integration = PaxyIntegration()


@app.get("/health")
async def health():
    return {"status": "healthy", "version": "1.0.0", "system": "paxy"}


@app.get("/readiness")
async def readiness():
    checks = {"api_url": "ok" if integration.base_url else "unavailable"}
    status = "healthy" if all(v == "ok" for v in checks.values()) else "degraded"
    return {"status": status, "checks": checks}


@app.post("/shipments")
async def create_shipment(request: CreateShipmentRequest):
    result, status_code = await integration.create_order(
        request.credentials, request.command,
    )
    if status_code >= 400:
        raise HTTPException(status_code=status_code, detail=result)
    return JSONResponse(content=result, status_code=status_code)


@app.post("/shipments/status")
async def get_status(request: StatusRequest):
    result, status_code = await integration.get_order_status(
        request.credentials, request.waybill_number,
    )
    if status_code >= 400:
        raise HTTPException(status_code=status_code, detail=result)
    return {"status": result}


@app.post("/labels")
async def get_label(request: LabelRequest):
    label_bytes, status_code = await integration.get_waybill_label_bytes(
        request.credentials, request.waybill_numbers,
    )
    if status_code >= 400:
        raise HTTPException(status_code=status_code, detail=label_bytes)
    return Response(content=label_bytes, media_type="application/pdf")


@app.post("/shipments/delete")
async def cancel_shipment(request: DeleteRequest):
    result, status_code = await integration.delete_order(
        request.credentials, request.waybill_number,
    )
    if status_code >= 400:
        raise HTTPException(status_code=status_code, detail=result)
    return {"result": result}


app = augment_legacy_fastapi_app(
    app,
    manifest_path=Path(__file__).resolve().parent.parent / "connector.yaml",
)
