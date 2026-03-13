"""FedEx Courier Integrator — FastAPI application."""

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
from src.integration import FedexIntegration
from src.schemas import (
    CreateShipmentRequest,
    DeleteShipmentRequest,
    FedexCredentials,
    LabelRequest,
    PointsRequest,
    RateRequest,
    StandardizedRateResponse,
)

logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s %(levelname)-8s %(name)s — %(message)s",
)
logger = logging.getLogger("courier-fedex")

app = FastAPI(
    title="FedEx Courier Connector",
    version="1.0.0",
    docs_url="/docs",
)

integration = FedexIntegration()


@app.get("/health")
async def health():
    return {"status": "healthy", "version": "1.0.0", "system": "fedex"}


@app.get("/readiness")
async def readiness():
    return {"status": "healthy", "checks": {"api_reachable": "ok"}}


@app.post("/shipments")
async def create_shipment(request: CreateShipmentRequest):
    try:
        result, status_code = await integration.create_order(
            request.credentials, request.command,
        )
        return JSONResponse(content=result, status_code=status_code)
    except Exception as exc:
        logger.exception("Failed to create FedEx shipment")
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.delete("/shipments/{order_id}")
async def cancel_shipment(order_id: str, request: DeleteShipmentRequest):
    try:
        result, status_code = await integration.delete_order(
            request.credentials, order_id, request.extras,
        )
        return JSONResponse(content=result, status_code=status_code)
    except Exception as exc:
        logger.exception("Failed to cancel FedEx shipment")
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/labels")
async def get_label(request: LabelRequest):
    """Return label bytes. Expects the full create-shipment response stored
    client-side to be posted as ``shipment_response`` in the body, or
    alternatively call with waybill_numbers for tracking info only."""
    try:
        tracking_number = request.waybill_numbers[0]
        info, status_code = FedexIntegration.get_tracking_info(tracking_number)
        return JSONResponse(content=info, status_code=status_code)
    except Exception as exc:
        logger.exception("Failed to get FedEx label")
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/rates")
async def get_rates(request: RateRequest):
    """Return standardized shipping rates via FedEx Rate API."""
    try:
        result, status_code = await integration.get_rates(
            request.credentials, request,
        )
        if status_code != 200:
            return StandardizedRateResponse(
                source="fedex",
                raw={"error": str(result), "status_code": status_code},
            ).model_dump()
        return result
    except Exception as exc:
        logger.exception("Failed to get FedEx rates")
        return StandardizedRateResponse(
            source="fedex",
            raw={"error": str(exc)},
        ).model_dump()


@app.post("/points")
async def get_points(request: PointsRequest):
    try:
        result, status_code = await integration.get_points(
            request.credentials,
            {"city": request.city, "postcode": request.postcode},
        )
        return JSONResponse(content=result, status_code=status_code)
    except Exception as exc:
        logger.exception("Failed to get FedEx points")
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/tracking/{tracking_number}")
async def get_tracking(tracking_number: str):
    info, status_code = FedexIntegration.get_tracking_info(tracking_number)
    return JSONResponse(content=info, status_code=status_code)


if augment_legacy_fastapi_app is not None:
    app = augment_legacy_fastapi_app(
        app,
        manifest_path=Path(__file__).resolve().parent.parent / "connector.yaml",
    )
