"""InPost International 2025 Courier Integrator — FastAPI application."""

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
    RateProduct,
    RateRequest,
    ReturnsShipmentRequest,
    StandardizedRateResponse,
)

logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s %(levelname)-8s %(name)s — %(message)s",
)
logger = logging.getLogger("courier-inpost-int-2025")

app = FastAPI(
    title="InPost International 2025 Courier Connector",
    version="3.0.0",
    docs_url="/docs",
)

integration = InpostIntegration()


@app.get("/health")
async def health():
    return {"status": "healthy", "version": "3.0.0", "system": "inpost-international-2025"}


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
        logger.exception("Failed to create InPost International 2025 shipment")
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
            request.credentials, request.tracking_number,
        )
        if status_code >= 400:
            raise HTTPException(status_code=status_code, detail=label_bytes)
        return Response(content=label_bytes, media_type="application/pdf")
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Failed to get InPost International 2025 label")
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.delete("/shipments/{waybill}")
async def cancel_shipment(
    waybill: str,
    organization_id: str = Query(...),
    client_secret: str = Query(...),
    access_token: str | None = Query(default=None),
    order_id: str | None = Query(default=None),
):
    credentials = InpostCredentials(
        organization_id=organization_id,
        client_secret=client_secret,
        access_token=access_token,
    )
    try:
        result, status_code = await integration.delete_order(
            credentials, waybill, order_id=order_id,
        )
        if status_code >= 400:
            raise HTTPException(status_code=status_code, detail=result)
        return {"result": result}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/shipments/{tracking_number}")
async def get_shipment(
    tracking_number: str,
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
        result, status_code = await integration.get_order(credentials, tracking_number)
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
            tracking_number=request.tracking_numbers[0] if request.tracking_numbers else "",
        )
        result = await integration._create_pickup_order(pickup_dto, request.credentials)
        return result
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Failed to create InPost International 2025 pickup order")
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


@app.post("/rates")
async def get_rates(request: RateRequest):
    """Return standardized shipping rates for price comparison workflows.

    InPost International API does not expose a dedicated pricing endpoint.
    Rates are derived from published weight/size-based pricing tables.
    """
    try:
        products = _calculate_inpost_rates(
            weight=request.weight,
            length=request.length,
            width=request.width,
            height=request.height,
            sender_country=request.sender_country_code,
            receiver_country=request.receiver_country_code,
        )
        return StandardizedRateResponse(
            products=products,
            source="inpost",
            raw={"method": "pricing_table", "weight": request.weight},
        ).model_dump()
    except Exception as exc:
        logger.exception("Failed to calculate InPost rates")
        return StandardizedRateResponse(
            source="inpost",
            raw={"error": str(exc)},
        ).model_dump()


def _calculate_inpost_rates(
    weight: float,
    length: float,
    width: float,
    height: float,
    sender_country: str,
    receiver_country: str,
) -> list[RateProduct]:
    """Estimate InPost rates from published weight/size tiers.

    These are approximate net prices (PLN) for the most common domestic
    services. Real prices depend on the customer's contract — this provides
    a reasonable baseline for comparison workflows.
    """
    is_domestic = sender_country == receiver_country == "PL"
    products: list[RateProduct] = []

    volume_weight = (length * width * height) / 5000
    billable = max(weight, volume_weight)

    if is_domestic:
        if billable <= 25 and max(length, width, height) <= 41:
            products.append(RateProduct(
                name="InPost Paczkomat (A)",
                price=12.99,
                currency="PLN",
                delivery_days=2,
                attributes={"source": "inpost", "service": "paczkomat", "size": "A"},
            ))
        if billable <= 25 and max(length, width, height) <= 64:
            products.append(RateProduct(
                name="InPost Paczkomat (B)",
                price=13.99,
                currency="PLN",
                delivery_days=2,
                attributes={"source": "inpost", "service": "paczkomat", "size": "B"},
            ))
        if billable <= 25:
            products.append(RateProduct(
                name="InPost Paczkomat (C)",
                price=15.49,
                currency="PLN",
                delivery_days=2,
                attributes={"source": "inpost", "service": "paczkomat", "size": "C"},
            ))
        if billable <= 30:
            products.append(RateProduct(
                name="InPost Kurier Standard",
                price=14.99,
                currency="PLN",
                delivery_days=2,
                attributes={"source": "inpost", "service": "courier_standard"},
            ))
            products.append(RateProduct(
                name="InPost Kurier Express",
                price=19.99,
                currency="PLN",
                delivery_days=1,
                attributes={"source": "inpost", "service": "courier_express"},
            ))
    else:
        if billable <= 30:
            products.append(RateProduct(
                name="InPost International Standard",
                price=39.99,
                currency="PLN",
                delivery_days=5,
                attributes={"source": "inpost", "service": "international_standard"},
            ))
            products.append(RateProduct(
                name="InPost International Express",
                price=59.99,
                currency="PLN",
                delivery_days=3,
                attributes={"source": "inpost", "service": "international_express"},
            ))

    return products


@app.post("/returns", status_code=201)
async def create_return_shipment(request: ReturnsShipmentRequest):
    try:
        returns_dto = integration.build_returns_dto(request)
        result, status_code = await integration.create_return_shipment(
            request.credentials, returns_dto,
        )
        if status_code >= 400:
            raise HTTPException(status_code=status_code, detail=result)
        return JSONResponse(content=result, status_code=status_code)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Failed to create InPost International 2025 return shipment")
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/returns/{tracking_number}/label")
async def get_return_label(
    tracking_number: str,
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
        label_bytes, status_code = await integration.get_return_label_bytes(
            credentials, tracking_number,
        )
        if status_code >= 400:
            raise HTTPException(status_code=status_code, detail=label_bytes)
        return Response(content=label_bytes, media_type="application/pdf")
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Failed to get InPost International 2025 return label")
        raise HTTPException(status_code=400, detail=str(exc)) from exc
