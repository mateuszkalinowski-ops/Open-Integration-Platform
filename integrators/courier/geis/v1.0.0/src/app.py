"""Geis Courier Integrator — FastAPI application."""

import logging

from fastapi import FastAPI, HTTPException, Response
from fastapi.responses import JSONResponse

from src.config import settings
from src.integration import GeisIntegration
from src.schemas import (
    CreateOrderRequest,
    DeleteRequest,
    LabelRequest,
    OrderDetailRequest,
    StatusRequest,
)

logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s %(levelname)-8s %(name)s — %(message)s",
)
logger = logging.getLogger("courier-geis")

app = FastAPI(
    title="Geis Courier Connector",
    version="1.0.0",
    docs_url="/docs",
)

integration = GeisIntegration()


@app.get("/health")
async def health():
    return {"status": "healthy", "version": "1.0.0", "system": "geis"}


@app.get("/readiness")
async def readiness():
    soap_ok = integration.client is not None
    geis_healthy = integration.check_healthy() if soap_ok else False
    checks = {
        "soap_client": "ok" if soap_ok else "unavailable",
        "geis_service": "ok" if geis_healthy else "unhealthy",
    }
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
        logger.exception("Failed to create Geis shipment")
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/shipments/status")
async def get_status(request: StatusRequest):
    try:
        result, status_code = integration.get_order_status(
            request.credentials, request.waybill_number
        )
        if status_code >= 400:
            raise HTTPException(status_code=status_code, detail=str(result))
        return {"status": result}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/shipments/detail")
async def get_order_detail(request: OrderDetailRequest):
    try:
        result, status_code = integration.get_order(
            request.credentials, request.waybill_number
        )
        if status_code >= 400:
            raise HTTPException(status_code=status_code, detail=str(result))
        return result
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


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
        logger.exception("Failed to get Geis label")
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/shipments/delete")
async def delete_shipment(request: DeleteRequest):
    try:
        result, status_code = integration.delete_order(
            request.credentials, request.waybill_number
        )
        if status_code >= 400:
            raise HTTPException(status_code=status_code, detail=str(result))
        return JSONResponse(content={"deleted": True}, status_code=status_code)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/shipments/assign-range")
async def assign_range(request: StatusRequest):
    try:
        result, status_code = integration.assign_range(request.credentials)
        if status_code >= 400:
            raise HTTPException(status_code=status_code, detail=str(result))
        range_low, range_high = result
        return {"range_low": range_low, "range_high": range_high}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
