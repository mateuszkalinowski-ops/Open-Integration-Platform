"""DPD Courier Integrator — FastAPI application."""

import logging
import sys
from pathlib import Path

SDK_PYTHON_PATH = Path(__file__).resolve().parents[5] / "sdk/python"
if str(SDK_PYTHON_PATH) not in sys.path:
    sys.path.insert(0, str(SDK_PYTHON_PATH))

from fastapi import FastAPI, HTTPException, Query, Response
from fastapi.responses import JSONResponse
from pinquark_connector_sdk.legacy import augment_legacy_fastapi_app

from src.config import settings
from src.integration import DpdIntegration
from src.schemas import (
    CreateShipmentRequest,
    DpdCredentials,
    DpdInfoCredentials,
    LabelRequest,
    ProtocolRequest,
    RateProduct,
    RateRequest,
    StandardizedRateResponse,
)

logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s %(levelname)-8s %(name)s — %(message)s",
)
logger = logging.getLogger("courier-dpd")

app = FastAPI(
    title="DPD Courier Connector",
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


@app.post("/rates")
async def get_rates(request: RateRequest):
    """Return standardized shipping rates for price comparison workflows.

    DPD SOAP API does not expose a public rating endpoint.
    Rates are estimated from published weight-based pricing tiers.
    """
    try:
        is_domestic = request.sender_country_code == request.receiver_country_code == "PL"
        products = _calculate_dpd_rates(
            weight=request.weight,
            length=request.length,
            width=request.width,
            height=request.height,
            is_domestic=is_domestic,
        )
        return StandardizedRateResponse(
            products=products,
            source="dpd",
            raw={"method": "pricing_table", "weight": request.weight},
        ).model_dump()
    except Exception as exc:
        logger.exception("Failed to calculate DPD rates")
        return StandardizedRateResponse(
            source="dpd",
            raw={"error": str(exc)},
        ).model_dump()


def _calculate_dpd_rates(
    weight: float,
    length: float,
    width: float,
    height: float,
    is_domestic: bool,
) -> list[RateProduct]:
    """Estimate DPD rates from published weight/size tiers."""
    volume_weight = (length * width * height) / 5000
    billable = max(weight, volume_weight)
    products: list[RateProduct] = []

    if is_domestic:
        if billable <= 1:
            base = 11.50
        elif billable <= 5:
            base = 13.50
        elif billable <= 10:
            base = 15.50
        elif billable <= 20:
            base = 18.50
        elif billable <= 31.5:
            base = 22.00
        else:
            base = 22.00 + (billable - 31.5) * 0.8

        products.append(RateProduct(
            name="DPD Classic",
            price=round(base, 2),
            currency="PLN",
            delivery_days=2,
            attributes={"source": "dpd", "service": "classic"},
        ))
        products.append(RateProduct(
            name="DPD Pickup",
            price=round(base * 0.85, 2),
            currency="PLN",
            delivery_days=3,
            attributes={"source": "dpd", "service": "pickup"},
        ))
        if billable <= 31.5:
            products.append(RateProduct(
                name="DPD 9:30",
                price=round(base * 2.2, 2),
                currency="PLN",
                delivery_days=1,
                attributes={"source": "dpd", "service": "guarantee_0930"},
            ))
            products.append(RateProduct(
                name="DPD 12:00",
                price=round(base * 1.8, 2),
                currency="PLN",
                delivery_days=1,
                attributes={"source": "dpd", "service": "guarantee_1200"},
            ))
    else:
        if billable <= 5:
            base = 45.00
        elif billable <= 10:
            base = 55.00
        elif billable <= 20:
            base = 70.00
        else:
            base = 70.00 + (billable - 20) * 2.5

        products.append(RateProduct(
            name="DPD Classic International",
            price=round(base, 2),
            currency="PLN",
            delivery_days=5,
            attributes={"source": "dpd", "service": "classic_international"},
        ))

    return products


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


app = augment_legacy_fastapi_app(
    app,
    manifest_path=Path(__file__).resolve().parent.parent / "connector.yaml",
)
