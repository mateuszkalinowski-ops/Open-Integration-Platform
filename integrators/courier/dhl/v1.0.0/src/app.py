"""DHL Courier Integrator — FastAPI application."""

import logging
import sys
from pathlib import Path

try:
    SDK_PYTHON_PATH = Path(__file__).resolve().parents[5] / "sdk/python"
    if SDK_PYTHON_PATH.exists() and str(SDK_PYTHON_PATH) not in sys.path:
        sys.path.insert(0, str(SDK_PYTHON_PATH))
except (IndexError, OSError):
    pass

from fastapi import FastAPI, HTTPException, Query, Response
from fastapi.responses import JSONResponse
try:
    from pinquark_connector_sdk.legacy import augment_legacy_fastapi_app
except ImportError:
    augment_legacy_fastapi_app = None  # type: ignore[assignment,misc]

from src.config import settings
from src.integration import DhlIntegration
from src.schemas import (
    CreateShipmentRequest,
    DhlCredentials,
    LabelRequest,
    RateProduct,
    RateRequest,
    StandardizedRateResponse,
)

logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s %(levelname)-8s %(name)s — %(message)s",
)
logger = logging.getLogger("courier-dhl")

app = FastAPI(
    title="DHL Courier Connector",
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


@app.post("/rates")
async def get_rates(request: RateRequest):
    """Return standardized shipping rates for price comparison workflows.

    DHL Parcel Poland SOAP API does not expose a public rating endpoint.
    Rates are estimated from published weight-based pricing tiers.
    """
    try:
        is_domestic = request.sender_country_code == request.receiver_country_code == "PL"
        products = _calculate_dhl_rates(
            weight=request.weight,
            length=request.length,
            width=request.width,
            height=request.height,
            is_domestic=is_domestic,
        )
        return StandardizedRateResponse(
            products=products,
            source="dhl",
            raw={"method": "pricing_table", "weight": request.weight},
        ).model_dump()
    except Exception as exc:
        logger.exception("Failed to calculate DHL Parcel rates")
        return StandardizedRateResponse(
            source="dhl",
            raw={"error": str(exc)},
        ).model_dump()


def _calculate_dhl_rates(
    weight: float,
    length: float,
    width: float,
    height: float,
    is_domestic: bool,
) -> list[RateProduct]:
    """Estimate DHL Parcel Poland rates from published weight/size tiers."""
    volume_weight = (length * width * height) / 5000
    billable = max(weight, volume_weight)
    products: list[RateProduct] = []

    if is_domestic:
        if billable <= 1:
            base = 11.00
        elif billable <= 5:
            base = 13.00
        elif billable <= 10:
            base = 15.00
        elif billable <= 20:
            base = 18.00
        elif billable <= 31.5:
            base = 21.50
        else:
            base = 21.50 + (billable - 31.5) * 0.85

        products.append(RateProduct(
            name="DHL Parcel Standard",
            price=round(base, 2),
            currency="PLN",
            delivery_days=2,
            attributes={"source": "dhl", "service": "standard"},
        ))
        products.append(RateProduct(
            name="DHL Parcel Connect",
            price=round(base * 0.88, 2),
            currency="PLN",
            delivery_days=3,
            attributes={"source": "dhl", "service": "parcel_connect"},
        ))
        if billable <= 31.5:
            products.append(RateProduct(
                name="DHL Parcel 9:00",
                price=round(base * 2.1, 2),
                currency="PLN",
                delivery_days=1,
                attributes={"source": "dhl", "service": "guarantee_0900"},
            ))
            products.append(RateProduct(
                name="DHL Parcel 12:00",
                price=round(base * 1.7, 2),
                currency="PLN",
                delivery_days=1,
                attributes={"source": "dhl", "service": "guarantee_1200"},
            ))
    else:
        if billable <= 5:
            base = 48.00
        elif billable <= 10:
            base = 58.00
        elif billable <= 20:
            base = 72.00
        else:
            base = 72.00 + (billable - 20) * 2.5

        products.append(RateProduct(
            name="DHL Parcel International",
            price=round(base, 2),
            currency="PLN",
            delivery_days=5,
            attributes={"source": "dhl", "service": "international"},
        ))

    return products


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


if augment_legacy_fastapi_app is not None:
    app = augment_legacy_fastapi_app(
        app,
        manifest_path=Path(__file__).resolve().parent.parent / "connector.yaml",
    )
