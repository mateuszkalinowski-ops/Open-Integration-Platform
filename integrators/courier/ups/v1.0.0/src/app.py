"""UPS Courier Integrator — FastAPI application."""

import logging
from http import HTTPStatus

from fastapi import FastAPI, HTTPException, Response
from fastapi.responses import JSONResponse

from src.config import settings
from src.integration import UpsIntegration
from src.schemas import (
    CreateShipmentRequest,
    LabelRequest,
    LoginRequest,
    RateRequest,
    StandardizedRateResponse,
    StatusRequest,
    UploadDocumentRequest,
)

logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s %(levelname)-8s %(name)s — %(message)s",
)
logger = logging.getLogger("courier-ups")

app = FastAPI(
    title="UPS Courier Connector",
    version="1.0.0",
    docs_url="/docs",
)

integration = UpsIntegration()


@app.get("/health")
async def health():
    return {"status": "healthy", "version": "1.0.0", "system": "ups"}


@app.get("/readiness")
async def readiness():
    return {"status": "healthy", "checks": {"http_client": "ok"}}


@app.post("/login")
async def login(request: LoginRequest):
    """Obtain an OAuth2 access token (client_credentials grant)."""
    try:
        result, status_code = await integration.login(request.credentials)
        return JSONResponse(content=result, status_code=status_code)
    except Exception as exc:
        logger.exception("UPS login failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/shipments")
async def create_shipment(request: CreateShipmentRequest):
    try:
        result, status_code = await integration.create_order(
            request.credentials, request,
        )
        return JSONResponse(content=result, status_code=status_code)
    except Exception as exc:
        logger.exception("Failed to create UPS shipment")
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/labels")
async def get_label(request: LabelRequest):
    try:
        label_bytes, status_code = await integration.get_waybill_label_bytes(
            request.credentials, request.waybill_numbers,
        )
        if status_code == HTTPStatus.OK:
            return Response(content=label_bytes, media_type="application/pdf")
        return JSONResponse(content={"error": label_bytes}, status_code=status_code)
    except Exception as exc:
        logger.exception("Failed to get UPS label")
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/shipments/{waybill}/status")
async def get_status(waybill: str, request: StatusRequest):
    try:
        result, status_code = await integration.get_order_status(
            request.credentials, waybill,
        )
        return JSONResponse(
            content={"status": result} if status_code == HTTPStatus.OK else {"error": result},
            status_code=status_code,
        )
    except Exception as exc:
        logger.exception("Failed to get UPS shipment status")
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/rates")
async def get_rates(request: RateRequest):
    """Return standardized shipping rates via UPS Rating API."""
    try:
        result, status_code = await integration.get_rates(request)
        if status_code != HTTPStatus.OK:
            return StandardizedRateResponse(
                source="ups",
                raw={"error": str(result), "status_code": status_code},
            ).model_dump()
        return result
    except Exception as exc:
        logger.exception("Failed to get UPS rates")
        return StandardizedRateResponse(
            source="ups",
            raw={"error": str(exc)},
        ).model_dump()


@app.post("/upload-documents")
async def upload_document(request: UploadDocumentRequest):
    try:
        params = {
            "waybill": request.waybill,
            "filename": request.filename,
            "file": request.file,
            "type": request.document_type,
        }
        result, status_code = await integration.upload_file_to_order(
            request.credentials, params,
        )
        return JSONResponse(content=result, status_code=status_code)
    except Exception as exc:
        logger.exception("Failed to upload document to UPS")
        raise HTTPException(status_code=400, detail=str(exc)) from exc
