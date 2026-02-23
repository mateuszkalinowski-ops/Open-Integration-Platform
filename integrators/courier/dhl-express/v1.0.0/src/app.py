"""DHL Express Courier Integrator — FastAPI application."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, HTTPException, Query, Response
from fastapi.responses import JSONResponse

from src.config import settings
from src.integration import DhlExpressError, DhlExpressIntegration
from src.schemas import CreateShipmentRequest, PickupRequest, RateRequest

logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s %(levelname)-8s %(name)s — %(message)s",
)
logger = logging.getLogger("courier-dhl-express")

integration = DhlExpressIntegration()


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    yield
    await integration.close()


app = FastAPI(
    title="Pinquark Courier Integrator — DHL Express",
    version="1.0.0",
    docs_url="/docs",
    lifespan=lifespan,
)


# ------------------------------------------------------------------
# Health / readiness
# ------------------------------------------------------------------


@app.get("/health")
async def health() -> dict:
    return {"status": "healthy", "version": "1.0.0", "system": "dhl-express"}


@app.get("/readiness")
async def readiness() -> dict:
    checks = {"api_configured": "ok" if integration.is_configured else "missing_credentials"}
    status = "healthy" if all(v == "ok" for v in checks.values()) else "degraded"
    return {"status": status, "checks": checks}


# ------------------------------------------------------------------
# Shipment creation
# ------------------------------------------------------------------


@app.post("/shipments", status_code=201)
async def create_shipment(request: CreateShipmentRequest) -> JSONResponse:
    payload = request.model_dump(by_alias=True, exclude_none=True)
    try:
        result, status_code = await integration.create_shipment(payload)
        return JSONResponse(content=result, status_code=status_code)
    except DhlExpressError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc
    except Exception as exc:
        logger.exception("Failed to create DHL Express shipment")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# ------------------------------------------------------------------
# Tracking
# ------------------------------------------------------------------


@app.get("/shipments/{tracking_number}/status")
async def get_status(
    tracking_number: str,
    tracking_view: str = Query("all-checkpoints", alias="trackingView"),
    level_of_detail: str = Query("all", alias="levelOfDetail"),
) -> dict:
    try:
        result, _ = await integration.get_tracking(
            tracking_number,
            tracking_view=tracking_view,
            level_of_detail=level_of_detail,
        )
        return result
    except DhlExpressError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# ------------------------------------------------------------------
# Rating
# ------------------------------------------------------------------


@app.post("/rates")
async def get_rates(request: RateRequest) -> dict:
    payload = {
        "customerDetails": {
            "shipperDetails": {
                "postalCode": request.shipper_postal_code,
                "cityName": request.shipper_city,
                "countryCode": request.shipper_country_code,
            },
            "receiverDetails": {
                "postalCode": request.receiver_postal_code,
                "cityName": request.receiver_city,
                "countryCode": request.receiver_country_code,
            },
        },
        "plannedShippingDateAndTime": request.planned_shipping_date,
        "unitOfMeasurement": request.unit_of_measurement,
        "isCustomsDeclarable": request.is_customs_declarable,
        "packages": [
            {
                "weight": request.weight,
                "dimensions": {
                    "length": request.length,
                    "width": request.width,
                    "height": request.height,
                },
            },
        ],
    }
    try:
        result, _ = await integration.get_rates(payload)
        return result
    except DhlExpressError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/products")
async def get_products(
    shipper_country_code: str = Query(..., alias="originCountryCode"),
    shipper_postal_code: str = Query("", alias="originPostalCode"),
    receiver_country_code: str = Query(..., alias="receiverCountryCode"),
    receiver_postal_code: str = Query("", alias="receiverPostalCode"),
    weight: float = Query(...),
    length: float = Query(1),
    width: float = Query(1),
    height: float = Query(1),
    planned_shipping_date: str = Query(..., alias="plannedShippingDate"),
    is_customs_declarable: bool = Query(False, alias="isCustomsDeclarable"),
    unit_of_measurement: str = Query("metric", alias="unitOfMeasurement"),
) -> dict:
    try:
        result, _ = await integration.get_products(
            shipper_country_code=shipper_country_code,
            shipper_postal_code=shipper_postal_code,
            receiver_country_code=receiver_country_code,
            receiver_postal_code=receiver_postal_code,
            weight=weight,
            length=length,
            width=width,
            height=height,
            planned_shipping_date=planned_shipping_date,
            is_customs_declarable=is_customs_declarable,
            unit_of_measurement=unit_of_measurement,
        )
        return result
    except DhlExpressError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# ------------------------------------------------------------------
# Labels / document images
# ------------------------------------------------------------------


@app.get("/shipments/{tracking_number}/label")
async def get_label(tracking_number: str) -> Response:
    try:
        label_bytes, status_code = await integration.get_label_bytes(tracking_number)
        if not label_bytes:
            raise HTTPException(status_code=404, detail="Label not found")
        return Response(content=label_bytes, media_type="application/pdf")
    except DhlExpressError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/shipments/{tracking_number}/documents")
async def get_documents(
    tracking_number: str,
    type_code: str = Query("label", alias="typeCode"),
) -> dict:
    try:
        result, _ = await integration.get_shipment_image(
            tracking_number, type_code=type_code,
        )
        if isinstance(result, dict):
            for doc in result.get("documents", []):
                doc.pop("_decoded_content", None)
        return result
    except DhlExpressError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# ------------------------------------------------------------------
# Pickup management
# ------------------------------------------------------------------


@app.post("/pickups", status_code=201)
async def create_pickup(request: PickupRequest) -> JSONResponse:
    payload = request.model_dump(by_alias=True, exclude_none=True)
    try:
        result, status_code = await integration.create_pickup(payload)
        return JSONResponse(content=result, status_code=status_code)
    except DhlExpressError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.patch("/pickups/{dispatch_confirmation_number}")
async def update_pickup(
    dispatch_confirmation_number: str,
    payload: dict,
) -> dict:
    try:
        result, _ = await integration.update_pickup(
            dispatch_confirmation_number, payload,
        )
        return result
    except DhlExpressError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.delete("/pickups/{dispatch_confirmation_number}")
async def cancel_pickup(
    dispatch_confirmation_number: str,
    requestor_name: str = Query("", alias="requestorName"),
    reason: str = Query("not needed"),
) -> dict:
    try:
        result, _ = await integration.cancel_pickup(
            dispatch_confirmation_number,
            requestor_name=requestor_name,
            reason=reason,
        )
        return result
    except DhlExpressError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# ------------------------------------------------------------------
# Address validation
# ------------------------------------------------------------------


@app.get("/address-validate")
async def validate_address(
    country_code: str = Query(..., alias="countryCode"),
    postal_code: str = Query("", alias="postalCode"),
    city: str = Query("", alias="cityName"),
    address_type: str = Query("delivery", alias="type"),
) -> dict:
    try:
        result, _ = await integration.validate_address(
            country_code=country_code,
            postal_code=postal_code,
            city=city,
            address_type=address_type,
        )
        return result
    except DhlExpressError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# ------------------------------------------------------------------
# Service points
# ------------------------------------------------------------------


@app.get("/points")
async def get_service_points(
    country_code: str = Query(..., alias="countryCode"),
    postal_code: str = Query("", alias="postalCode"),
    city: str = Query("", alias="cityName"),
    latitude: float | None = Query(None),
    longitude: float | None = Query(None),
    radius: int = Query(5000),
    max_results: int = Query(25, alias="maxResults"),
) -> dict:
    try:
        result, _ = await integration.get_service_points(
            country_code=country_code,
            postal_code=postal_code,
            city=city,
            latitude=latitude,
            longitude=longitude,
            radius=radius,
            max_results=max_results,
        )
        return result
    except DhlExpressError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# ------------------------------------------------------------------
# Landed cost
# ------------------------------------------------------------------


@app.post("/landed-cost")
async def get_landed_cost(payload: dict) -> dict:
    try:
        result, _ = await integration.get_landed_cost(payload)
        return result
    except DhlExpressError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
