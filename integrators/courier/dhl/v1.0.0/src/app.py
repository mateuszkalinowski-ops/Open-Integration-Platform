"""DHL Courier Integrator — FastAPI application."""

import logging

from fastapi import FastAPI, HTTPException, Query, Response
from fastapi.responses import JSONResponse

from src.config import settings
from src.integration import DhlIntegration
from src.schemas import CreateShipmentRequest, DhlCredentials, LabelRequest

logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s %(levelname)-8s %(name)s — %(message)s",
)
logger = logging.getLogger("courier-dhl")

app = FastAPI(
    title="Pinquark Courier Integrator — DHL",
    version="1.0.0",
    docs_url="/docs",
)

integration = DhlIntegration()


@app.get("/health")
async def health():
    return {"status": "healthy", "version": "1.0.0", "system": "dhl"}


@app.get("/readiness")
async def readiness():
    checks = {"soap_client": "ok" if integration.client else "unavailable"}
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
        logger.exception("Failed to create DHL shipment")
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/shipments/{waybill_number}/status")
async def get_status(
    waybill_number: str,
    username: str = Query(...),
    password: str = Query(...),
    account_number: str = Query(""),
    sap_number: str = Query(""),
):
    credentials = DhlCredentials(
        username=username, password=password,
        account_number=account_number, sap_number=sap_number,
    )
    try:
        result, status_code = integration.get_order_status(credentials, waybill_number)
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
        label_bytes, status_code = integration.get_waybill_label_bytes(
            request.credentials, request.waybill_numbers, {},
        )
        if status_code >= 400:
            raise HTTPException(status_code=status_code, detail=label_bytes)
        return Response(content=label_bytes, media_type="application/pdf")
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Failed to get DHL label")
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.delete("/shipments/{waybill_number}")
async def cancel_shipment(
    waybill_number: str,
    username: str = Query(...),
    password: str = Query(...),
    account_number: str = Query(""),
    sap_number: str = Query(""),
):
    credentials = DhlCredentials(
        username=username, password=password,
        account_number=account_number, sap_number=sap_number,
    )
    try:
        result, status_code = integration.delete_order(credentials, waybill_number, {})
        if status_code >= 400:
            raise HTTPException(status_code=status_code, detail=result)
        return {"result": result}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/points")
async def get_points(
    username: str = Query(...),
    password: str = Query(...),
    account_number: str = Query(""),
    sap_number: str = Query(""),
    city: str = "",
    postal_code: str = "",
):
    credentials = DhlCredentials(
        username=username, password=password,
        account_number=account_number, sap_number=sap_number,
    )
    try:
        result, status_code = integration.get_points(
            credentials, {"city": city, "postcode": postal_code},
        )
        if status_code >= 400:
            raise HTTPException(status_code=status_code, detail=result)
        return result
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
