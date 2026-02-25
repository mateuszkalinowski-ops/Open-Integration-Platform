"""GLS Courier Integrator — FastAPI application."""

import logging

from fastapi import FastAPI, HTTPException, Query, Response
from fastapi.responses import JSONResponse

from src.config import settings
from src.integration import GlsIntegration
from src.schemas import (
    CreateShipmentRequest,
    GlsCredentials,
    LabelRequest,
    RateProduct,
    RateRequest,
    StandardizedRateResponse,
)

logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s %(levelname)-8s %(name)s — %(message)s",
)
logger = logging.getLogger("courier-gls")

app = FastAPI(
    title="GLS Courier Connector",
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


@app.post("/rates")
async def get_rates(request: RateRequest):
    """Return standardized shipping rates for price comparison workflows.

    GLS SOAP API does not expose a dedicated pricing endpoint.
    Rates are estimated from published weight-based pricing tiers.
    """
    try:
        is_domestic = request.sender_country_code == request.receiver_country_code == "PL"
        products = _calculate_gls_rates(
            weight=request.weight,
            length=request.length,
            width=request.width,
            height=request.height,
            is_domestic=is_domestic,
        )
        return StandardizedRateResponse(
            products=products,
            source="gls",
            raw={"method": "pricing_table", "weight": request.weight},
        ).model_dump()
    except Exception as exc:
        logger.exception("Failed to calculate GLS rates")
        return StandardizedRateResponse(
            source="gls",
            raw={"error": str(exc)},
        ).model_dump()


def _calculate_gls_rates(
    weight: float,
    length: float,
    width: float,
    height: float,
    is_domestic: bool,
) -> list[RateProduct]:
    """Estimate GLS rates from published weight/size tiers."""
    volume_weight = (length * width * height) / 5000
    billable = max(weight, volume_weight)
    products: list[RateProduct] = []

    if is_domestic:
        if billable <= 2:
            base = 10.50
        elif billable <= 5:
            base = 12.50
        elif billable <= 10:
            base = 14.50
        elif billable <= 20:
            base = 17.50
        elif billable <= 31.5:
            base = 21.00
        elif billable <= 40:
            base = 28.00
        else:
            base = 28.00 + (billable - 40) * 0.9

        products.append(RateProduct(
            name="GLS Business Parcel",
            price=round(base, 2),
            currency="PLN",
            delivery_days=2,
            attributes={"source": "gls", "service": "business_parcel"},
        ))
        products.append(RateProduct(
            name="GLS ShopDelivery",
            price=round(base * 0.82, 2),
            currency="PLN",
            delivery_days=3,
            attributes={"source": "gls", "service": "shop_delivery"},
        ))
        if billable <= 31.5:
            products.append(RateProduct(
                name="GLS 10:00",
                price=round(base * 2.3, 2),
                currency="PLN",
                delivery_days=1,
                attributes={"source": "gls", "service": "guarantee_1000"},
            ))
            products.append(RateProduct(
                name="GLS 12:00",
                price=round(base * 1.9, 2),
                currency="PLN",
                delivery_days=1,
                attributes={"source": "gls", "service": "guarantee_1200"},
            ))
    else:
        if billable <= 5:
            base = 50.00
        elif billable <= 10:
            base = 60.00
        elif billable <= 20:
            base = 75.00
        else:
            base = 75.00 + (billable - 20) * 2.8

        products.append(RateProduct(
            name="GLS EuroBusinessParcel",
            price=round(base, 2),
            currency="PLN",
            delivery_days=5,
            attributes={"source": "gls", "service": "euro_business_parcel"},
        ))

    return products


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
