"""InPost Courier Integrator — FastAPI application."""

import logging

from fastapi import FastAPI, HTTPException, Query, Response
from fastapi.responses import JSONResponse

from src.config import settings
from src.integration import InpostIntegration
from src.schemas import (
    CreateShipmentRequest,
    InpostCredentials,
    LabelRequest,
    PointsQuery,
)

logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s %(levelname)-8s %(name)s — %(message)s",
)
logger = logging.getLogger("courier-inpost")

app = FastAPI(
    title="InPost Courier Connector",
    version="1.0.0",
    docs_url="/docs",
)

integration = InpostIntegration()


@app.get("/health")
async def health():
    return {"status": "healthy", "version": "1.0.0", "system": "inpost"}


@app.get("/readiness")
async def readiness():
    checks = {"api_reachable": "ok"}
    status = "healthy" if all(v == "ok" for v in checks.values()) else "degraded"
    return {"status": status, "checks": checks}


@app.post("/shipments", status_code=201)
async def create_shipment(request: CreateShipmentRequest):
    try:
        result, status_code = await integration.create_order(
            request.credentials, request,
        )
        if status_code >= 400:
            raise HTTPException(status_code=status_code, detail=result)
        return JSONResponse(content=result, status_code=status_code)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Failed to create InPost shipment")
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/shipments/{waybill}/status")
async def get_status(
    waybill: str,
    organization_id: str = Query(...),
    api_token: str = Query(...),
):
    credentials = InpostCredentials(organization_id=organization_id, api_token=api_token)
    try:
        result, status_code = await integration.get_order_status(credentials, waybill)
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
        label_bytes, status_code = await integration.get_waybill_label_bytes(
            request.credentials, request.waybill_numbers,
        )
        if status_code >= 400:
            raise HTTPException(status_code=status_code, detail=label_bytes)
        return Response(content=label_bytes, media_type="application/pdf")
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Failed to get InPost label")
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.delete("/shipments/{waybill}")
async def cancel_shipment(
    waybill: str,
    organization_id: str = Query(...),
    api_token: str = Query(...),
):
    credentials = InpostCredentials(organization_id=organization_id, api_token=api_token)
    try:
        result, status_code = await integration.delete_order(credentials, waybill)
        if status_code >= 400:
            raise HTTPException(status_code=status_code, detail=result)
        return {"result": result}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/shipments/{waybill}")
async def get_shipment(
    waybill: str,
    organization_id: str = Query(...),
    api_token: str = Query(...),
):
    credentials = InpostCredentials(organization_id=organization_id, api_token=api_token)
    try:
        result, status_code = await integration.get_order(credentials, waybill)
        if status_code >= 400:
            raise HTTPException(status_code=status_code, detail=result)
        return result
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/points")
async def get_points(request: PointsQuery):
    try:
        data: dict = {}
        if request.city:
            data["city"] = request.city
        if request.postcode:
            data["postcode"] = request.postcode
        data["extras"] = request.extras

        result, status_code = await integration.get_points(request.credentials, data)
        if status_code >= 400:
            raise HTTPException(status_code=status_code, detail=result)
        return result
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/tracking/{waybill}")
async def get_tracking(waybill: str):
    try:
        result, status_code = await integration.get_tracking_info(waybill)
        if status_code >= 400:
            raise HTTPException(status_code=status_code, detail=str(result))
        return result.model_dump()
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
