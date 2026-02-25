"""InPost International 2024 Courier Integrator — FastAPI application."""

import logging

from fastapi import FastAPI, HTTPException, Query, Response
from fastapi.responses import JSONResponse

from src.config import settings
from src.integration import InpostIntegration
from src.schemas import (
    CreateShipmentRequest,
    InpostCredentials,
    LabelRequest,
    PickupHoursRequest,
    PickupRequest,
    PointsQuery,
)

logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s %(levelname)-8s %(name)s — %(message)s",
)
logger = logging.getLogger("courier-inpost-int-2024")

app = FastAPI(
    title="InPost International 2024 Courier Connector",
    version="2.0.0",
    docs_url="/docs",
)

integration = InpostIntegration()


@app.get("/health")
async def health():
    return {"status": "healthy", "version": "2.0.0", "system": "inpost-international-2024"}


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
        logger.exception("Failed to create InPost International 2024 shipment")
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/shipments/{waybill}/status")
async def get_status(
    waybill: str,
    organization_id: str = Query(...),
    client_secret: str = Query(...),
    access_token: str | None = Query(default=None),
):
    credentials = InpostCredentials(
        organization_id=organization_id,
        client_secret=client_secret,
        access_token=access_token,
    )
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
            request.credentials, request.shipment_uuid,
        )
        if status_code >= 400:
            raise HTTPException(status_code=status_code, detail=label_bytes)
        return Response(content=label_bytes, media_type="application/pdf")
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Failed to get InPost International 2024 label")
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/shipments/{shipment_uuid}")
async def get_shipment(
    shipment_uuid: str,
    organization_id: str = Query(...),
    client_secret: str = Query(...),
    access_token: str | None = Query(default=None),
):
    credentials = InpostCredentials(
        organization_id=organization_id,
        client_secret=client_secret,
        access_token=access_token,
    )
    try:
        result, status_code = await integration.get_order(credentials, shipment_uuid)
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


@app.post("/pickups")
async def create_pickup(request: PickupRequest):
    try:
        pickup_dto = integration._build_pickup_order_dto(
            CreateShipmentRequest(
                credentials=request.credentials,
                serviceName="inpost_international",
                extras=request.extras,
                content=request.content,
                parcels=request.parcels,
                shipper=request.shipper,
                receiver=request.shipper,
            ),
        )
        result = await integration._create_pickup_order(pickup_dto, request.credentials)
        return result
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Failed to create InPost International 2024 pickup order")
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/pickup-hours")
async def get_pickup_hours(request: PickupHoursRequest):
    try:
        result, status_code = await integration.get_pickup_hours(
            request.credentials, request.postcode, request.country_code,
        )
        if status_code >= 400:
            raise HTTPException(status_code=status_code, detail=result)
        return result
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
