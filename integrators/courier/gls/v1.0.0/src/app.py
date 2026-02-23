"""GLS Courier Integrator — FastAPI application."""

import logging

from fastapi import FastAPI, HTTPException, Query, Response
from fastapi.responses import JSONResponse

from src.config import settings
from src.integration import GlsIntegration
from src.schemas import CreateShipmentRequest, GlsCredentials, LabelRequest

logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s %(levelname)-8s %(name)s — %(message)s",
)
logger = logging.getLogger("courier-gls")

app = FastAPI(
    title="Pinquark Courier Integrator — GLS",
    version="1.0.0",
    docs_url="/docs",
)

integration = GlsIntegration()


@app.get("/health")
async def health():
    return {"status": "healthy", "version": "1.0.0", "system": "gls"}


@app.get("/readiness")
async def readiness():
    checks = {"soap_client": "ok" if integration.client else "unavailable"}
    status = "healthy" if all(v == "ok" for v in checks.values()) else "degraded"
    return {"status": status, "checks": checks}


@app.post("/shipments")
async def create_shipment(request: CreateShipmentRequest):
    try:
        result = integration.create_order(request.credentials, request.command)
        if isinstance(result, tuple):
            data, code = result
            if code >= 400:
                raise HTTPException(status_code=code, detail=str(data))
            return JSONResponse(content=data, status_code=code)
        return JSONResponse(content=result, status_code=201)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Failed to create GLS shipment")
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/shipments/{waybill_number}/status")
async def get_tracking(
    waybill_number: str,
    username: str = Query(...),
    password: str = Query(...),
):
    try:
        credentials = GlsCredentials(username=username, password=password)
        result, status_code = integration.get_tracking_info(credentials, waybill_number)
        if status_code != 200:
            raise HTTPException(status_code=status_code, detail=str(result))
        return result
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/labels")
async def get_label(request: LabelRequest):
    try:
        args: dict = {}
        if request.external_id:
            args["external_id"] = request.external_id
        label_bytes, status_code = integration.get_waybill_label_bytes(
            request.credentials, request.waybill_numbers, args,
        )
        if status_code != 200:
            raise HTTPException(status_code=status_code, detail=str(label_bytes))
        return Response(content=label_bytes, media_type="application/pdf")
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Failed to get GLS label")
        raise HTTPException(status_code=400, detail=str(exc)) from exc
