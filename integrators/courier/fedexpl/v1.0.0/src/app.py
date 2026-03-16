"""FedEx PL Courier Integrator — FastAPI application."""

import logging
import sys
from pathlib import Path

try:
    SDK_PYTHON_PATH = Path(__file__).resolve().parents[5] / "sdk/python"
    if SDK_PYTHON_PATH.exists() and str(SDK_PYTHON_PATH) not in sys.path:
        sys.path.insert(0, str(SDK_PYTHON_PATH))
except (IndexError, OSError):
    pass

from fastapi import FastAPI, HTTPException, Response
from fastapi.responses import JSONResponse

try:
    from pinquark_connector_sdk.legacy import augment_legacy_fastapi_app
except ImportError:
    augment_legacy_fastapi_app = None  # type: ignore[assignment,misc]

from src.config import settings
from src.integration import FedexPlIntegration
from src.schemas import CreateShipmentRequest, FedexPlCredentials, LabelRequest

logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s %(levelname)-8s %(name)s — %(message)s",
)
logger = logging.getLogger("courier-fedexpl")

app = FastAPI(
    title="FedEx PL Courier Connector",
    version="1.0.0",
    docs_url="/docs",
)

integration = FedexPlIntegration()


@app.get("/health")
async def health():
    return {"status": "healthy", "version": "1.0.0", "system": "fedexpl"}


@app.get("/readiness")
async def readiness():
    checks = {"soap_client": "ok" if integration.client else "unavailable"}
    status = "healthy" if all(v == "ok" for v in checks.values()) else "degraded"
    return {"status": status, "checks": checks}


@app.post("/shipments")
async def create_shipment(request: CreateShipmentRequest):
    try:
        result, status_code = integration.create_order(
            request.credentials,
            request.command,
        )
        return JSONResponse(content=result, status_code=status_code)
    except Exception:
        logger.exception("Failed to create FedEx PL shipment")
        raise HTTPException(status_code=500, detail="FedEx PL shipment creation failed")


@app.get("/shipments/{waybill_number}/status")
async def get_status(waybill_number: str, credentials: FedexPlCredentials):
    try:
        result, status_code = integration.get_order_status(
            credentials,
            waybill_number,
        )
        return JSONResponse(content={"status": result}, status_code=status_code)
    except Exception:
        logger.exception("FedEx PL shipment status retrieval failed")
        raise HTTPException(status_code=500, detail="FedEx PL shipment status retrieval failed")


@app.post("/labels")
async def get_label(request: LabelRequest):
    try:
        label_bytes, status_code = integration.get_waybill_label_bytes(
            request.credentials,
            request.waybill_numbers,
            {},
        )
        if status_code != 200:
            return JSONResponse(content={"error": str(label_bytes)}, status_code=status_code)
        return Response(content=label_bytes, media_type="application/pdf")
    except Exception:
        logger.exception("Failed to get FedEx PL label")
        raise HTTPException(status_code=500, detail="FedEx PL label retrieval failed")


if augment_legacy_fastapi_app is not None:
    app = augment_legacy_fastapi_app(
        app,
        manifest_path=Path(__file__).resolve().parent.parent / "connector.yaml",
    )
