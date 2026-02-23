"""Raben Group Courier Integrator — FastAPI application."""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import FastAPI, HTTPException, Query, Response
from fastapi.responses import JSONResponse

from src.config import settings
from src.integration import RabenIntegration
from src.schemas import (
    ClaimSubmitRequest,
    CreateShipmentRequest,
    LabelRequest,
    RabenCredentials,
)

logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s %(levelname)-8s %(name)s — %(message)s",
)
logger = logging.getLogger("courier-raben")

app = FastAPI(
    title="Pinquark Courier Integrator — Raben Group",
    version="1.0.0",
    docs_url="/docs",
)

integration = RabenIntegration()


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

@app.get("/health")
async def health():
    return {"status": "healthy", "version": "1.0.0", "system": "raben"}


@app.get("/readiness")
async def readiness():
    checks = {"api_reachable": "ok"}
    status = "healthy" if all(v == "ok" for v in checks.values()) else "degraded"
    return {"status": status, "checks": checks}


# ---------------------------------------------------------------------------
# Transport orders (myOrder)
# ---------------------------------------------------------------------------

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
        logger.exception("Failed to create Raben transport order")
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/shipments/{waybill_number}")
async def get_shipment(
    waybill_number: str,
    username: str = Query(...),
    password: str = Query(...),
    customer_number: Optional[str] = Query(default=None),
    sandbox_mode: bool = Query(default=False),
):
    credentials = RabenCredentials(
        username=username,
        password=password,
        customer_number=customer_number,
        sandbox_mode=sandbox_mode,
    )
    try:
        result, status_code = await integration.get_order(credentials, waybill_number)
        if status_code >= 400:
            raise HTTPException(status_code=status_code, detail=result)
        return result
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.put("/shipments/{waybill_number}/cancel")
async def cancel_shipment(
    waybill_number: str,
    username: str = Query(...),
    password: str = Query(...),
    customer_number: Optional[str] = Query(default=None),
    sandbox_mode: bool = Query(default=False),
):
    credentials = RabenCredentials(
        username=username,
        password=password,
        customer_number=customer_number,
        sandbox_mode=sandbox_mode,
    )
    try:
        result, status_code = await integration.cancel_order(credentials, waybill_number)
        if status_code >= 400:
            raise HTTPException(status_code=status_code, detail=result)
        return {"result": result}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


# ---------------------------------------------------------------------------
# Tracking (Track & Trace)
# ---------------------------------------------------------------------------

@app.get("/tracking/{waybill_number}")
async def get_tracking(
    waybill_number: str,
    username: str = Query(...),
    password: str = Query(...),
    customer_number: Optional[str] = Query(default=None),
    sandbox_mode: bool = Query(default=False),
):
    credentials = RabenCredentials(
        username=username,
        password=password,
        customer_number=customer_number,
        sandbox_mode=sandbox_mode,
    )
    try:
        result, status_code = await integration.get_tracking(credentials, waybill_number)
        if status_code >= 400:
            raise HTTPException(status_code=status_code, detail=result)
        return result
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/shipments/{waybill_number}/status")
async def get_shipment_status(
    waybill_number: str,
    username: str = Query(...),
    password: str = Query(...),
    customer_number: Optional[str] = Query(default=None),
    sandbox_mode: bool = Query(default=False),
):
    credentials = RabenCredentials(
        username=username,
        password=password,
        customer_number=customer_number,
        sandbox_mode=sandbox_mode,
    )
    try:
        result, status_code = await integration.get_shipment_status(
            credentials, waybill_number,
        )
        if status_code >= 400:
            raise HTTPException(status_code=status_code, detail=result)
        return result
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/shipments/{waybill_number}/eta")
async def get_eta(
    waybill_number: str,
    username: str = Query(...),
    password: str = Query(...),
    customer_number: Optional[str] = Query(default=None),
    sandbox_mode: bool = Query(default=False),
):
    credentials = RabenCredentials(
        username=username,
        password=password,
        customer_number=customer_number,
        sandbox_mode=sandbox_mode,
    )
    try:
        result, status_code = await integration.get_eta(credentials, waybill_number)
        if status_code >= 400:
            raise HTTPException(status_code=status_code, detail=result)
        return result
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


# ---------------------------------------------------------------------------
# Labels
# ---------------------------------------------------------------------------

@app.post("/labels")
async def get_label(request: LabelRequest):
    try:
        label_data, status_code = await integration.get_label(
            request.credentials, request.waybill_number, request.format,
        )
        if status_code >= 400:
            raise HTTPException(status_code=status_code, detail=label_data)
        media_type = "application/pdf" if request.format == "pdf" else "application/x-zpl"
        return Response(content=label_data, media_type=media_type)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Failed to get Raben label")
        raise HTTPException(status_code=400, detail=str(exc)) from exc


# ---------------------------------------------------------------------------
# Claims (myClaim)
# ---------------------------------------------------------------------------

@app.post("/claims", status_code=201)
async def create_claim(request: ClaimSubmitRequest):
    try:
        result, status_code = await integration.create_claim(
            request.credentials,
            request.waybill_number,
            request.claim_type,
            request.description,
            request.contact_email,
            request.contact_phone,
        )
        if status_code >= 400:
            raise HTTPException(status_code=status_code, detail=result)
        return JSONResponse(content=result, status_code=status_code)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Failed to create Raben claim")
        raise HTTPException(status_code=400, detail=str(exc)) from exc


# ---------------------------------------------------------------------------
# Delivery confirmation (PCD)
# ---------------------------------------------------------------------------

@app.get("/deliveries/{waybill_number}/confirmation")
async def get_delivery_confirmation(
    waybill_number: str,
    username: str = Query(...),
    password: str = Query(...),
    customer_number: Optional[str] = Query(default=None),
    sandbox_mode: bool = Query(default=False),
):
    credentials = RabenCredentials(
        username=username,
        password=password,
        customer_number=customer_number,
        sandbox_mode=sandbox_mode,
    )
    try:
        result, status_code = await integration.get_delivery_confirmation(
            credentials, waybill_number,
        )
        if status_code >= 400:
            raise HTTPException(status_code=status_code, detail=result)
        return result
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
