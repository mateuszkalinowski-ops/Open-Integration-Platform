"""DPD Courier Integrator — FastAPI application."""

import logging

from fastapi import FastAPI, HTTPException, Query, Response
from fastapi.responses import JSONResponse

from src.config import settings
from src.integration import DpdIntegration
from src.schemas import (
    CreateShipmentRequest,
    DpdCredentials,
    DpdInfoCredentials,
    LabelRequest,
    ProtocolRequest,
)

logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s %(levelname)-8s %(name)s — %(message)s",
)
logger = logging.getLogger("courier-dpd")

app = FastAPI(
    title="Pinquark Courier Integrator — DPD",
    version="1.0.0",
    docs_url="/docs",
)

integration = DpdIntegration()


@app.get("/health")
async def health():
    return {"status": "healthy", "version": "1.0.0", "system": "dpd"}


@app.get("/readiness")
async def readiness():
    checks = {
        "soap_client": "ok" if integration.client else "unavailable",
        "soap_info_client": "ok" if integration.info_client else "unavailable",
    }
    status = "healthy" if all(v == "ok" for v in checks.values()) else "degraded"
    return {"status": status, "checks": checks}


@app.post("/shipments", status_code=201)
async def create_shipment(request: CreateShipmentRequest):
    try:
        result, status_code = integration.create_order(request.credentials, request.command)
        if status_code >= 400:
            raise HTTPException(status_code=status_code, detail=result)
        return JSONResponse(content=result, status_code=status_code)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Failed to create DPD shipment")
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/shipments/{waybill_number}/status")
async def get_status(
    waybill_number: str,
    login: str = Query(...),
    password: str = Query(...),
    master_fid: int | None = Query(None),
    info_channel: str = Query(""),
):
    try:
        credentials = DpdCredentials(login=login, password=password, master_fid=master_fid)
        info_creds = DpdInfoCredentials(login=login, password=password, channel=info_channel) if info_channel else None
        result, status_code = integration.get_order_status(credentials, waybill_number, info_creds)
        if status_code >= 400:
            raise HTTPException(status_code=status_code, detail=result)
        return {"status": result}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/labels")
async def get_label(request: LabelRequest):
    try:
        args = {}
        if request.external_id:
            args["external_id"] = request.external_id
        label_bytes = integration.get_waybill_label_bytes(
            request.credentials, request.waybill_numbers, args,
        )
        if isinstance(label_bytes, tuple):
            data, code = label_bytes
            if code != 200:
                raise HTTPException(status_code=code, detail=str(data))
            label_bytes = data
        return Response(content=label_bytes, media_type="application/pdf")
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Failed to get DPD label")
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/protocol")
async def generate_protocol(request: ProtocolRequest):
    try:
        result, status_code = integration.generate_protocol(
            request.credentials,
            request.waybill_numbers,
            request.session_type,
        )
        if status_code != 200:
            raise HTTPException(status_code=status_code, detail=str(result))
        return Response(content=result, media_type="application/pdf")
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Failed to generate DPD protocol")
        raise HTTPException(status_code=400, detail=str(exc)) from exc
