"""Raben Group Courier Integrator — FastAPI application."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

try:
    SDK_PYTHON_PATH = Path(__file__).resolve().parents[5] / "sdk/python"
    if SDK_PYTHON_PATH.exists() and str(SDK_PYTHON_PATH) not in sys.path:
        sys.path.insert(0, str(SDK_PYTHON_PATH))
except (IndexError, OSError):
    pass

from fastapi import FastAPI, Header, HTTPException, Response
from fastapi.responses import JSONResponse

try:
    from pinquark_connector_sdk.legacy import augment_legacy_fastapi_app
except ImportError:
    augment_legacy_fastapi_app = None  # type: ignore[assignment,misc]

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
    title="Raben Group Courier Connector",
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
            request.credentials,
            request,
        )
        if status_code >= 400:
            logger.error("Raben shipment creation failed: %s", result)
            raise HTTPException(status_code=status_code, detail="Raben shipment creation failed")
        return JSONResponse(content=result, status_code=status_code)
    except HTTPException:
        raise
    except Exception:
        logger.exception("Failed to create Raben transport order")
        raise HTTPException(status_code=500, detail="Raben shipment creation failed")


@app.get("/shipments/{waybill_number}")
async def get_shipment(
    waybill_number: str,
    username: str = Header(..., alias="X-Username"),
    password: str = Header(..., alias="X-Password"),
    customer_number: str | None = Header(default=None, alias="X-Customer-Number"),
    sandbox_mode: bool = Header(default=False, alias="X-Sandbox-Mode"),
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
            logger.error("Raben shipment retrieval failed: %s", result)
            raise HTTPException(status_code=status_code, detail="Raben shipment retrieval failed")
        return result
    except HTTPException:
        raise
    except Exception:
        logger.exception("Raben shipment retrieval failed")
        raise HTTPException(status_code=500, detail="Raben shipment retrieval failed")


@app.put("/shipments/{waybill_number}/cancel")
async def cancel_shipment(
    waybill_number: str,
    username: str = Header(..., alias="X-Username"),
    password: str = Header(..., alias="X-Password"),
    customer_number: str | None = Header(default=None, alias="X-Customer-Number"),
    sandbox_mode: bool = Header(default=False, alias="X-Sandbox-Mode"),
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
            logger.error("Raben shipment cancellation failed: %s", result)
            raise HTTPException(status_code=status_code, detail="Raben shipment cancellation failed")
        return {"result": result}
    except HTTPException:
        raise
    except Exception:
        logger.exception("Raben shipment cancellation failed")
        raise HTTPException(status_code=500, detail="Raben shipment cancellation failed")


# ---------------------------------------------------------------------------
# Tracking (Track & Trace)
# ---------------------------------------------------------------------------


@app.get("/tracking/{waybill_number}")
async def get_tracking(
    waybill_number: str,
    username: str = Header(..., alias="X-Username"),
    password: str = Header(..., alias="X-Password"),
    customer_number: str | None = Header(default=None, alias="X-Customer-Number"),
    sandbox_mode: bool = Header(default=False, alias="X-Sandbox-Mode"),
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
            logger.error("Raben tracking retrieval failed: %s", result)
            raise HTTPException(status_code=status_code, detail="Raben tracking retrieval failed")
        return result
    except HTTPException:
        raise
    except Exception:
        logger.exception("Raben tracking retrieval failed")
        raise HTTPException(status_code=500, detail="Raben tracking retrieval failed")


@app.get("/shipments/{waybill_number}/status")
async def get_shipment_status(
    waybill_number: str,
    username: str = Header(..., alias="X-Username"),
    password: str = Header(..., alias="X-Password"),
    customer_number: str | None = Header(default=None, alias="X-Customer-Number"),
    sandbox_mode: bool = Header(default=False, alias="X-Sandbox-Mode"),
):
    credentials = RabenCredentials(
        username=username,
        password=password,
        customer_number=customer_number,
        sandbox_mode=sandbox_mode,
    )
    try:
        result, status_code = await integration.get_shipment_status(
            credentials,
            waybill_number,
        )
        if status_code >= 400:
            logger.error("Raben shipment status retrieval failed: %s", result)
            raise HTTPException(status_code=status_code, detail="Raben shipment status retrieval failed")
        return result
    except HTTPException:
        raise
    except Exception:
        logger.exception("Raben shipment status retrieval failed")
        raise HTTPException(status_code=500, detail="Raben shipment status retrieval failed")


@app.get("/shipments/{waybill_number}/eta")
async def get_eta(
    waybill_number: str,
    username: str = Header(..., alias="X-Username"),
    password: str = Header(..., alias="X-Password"),
    customer_number: str | None = Header(default=None, alias="X-Customer-Number"),
    sandbox_mode: bool = Header(default=False, alias="X-Sandbox-Mode"),
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
            logger.error("Raben ETA retrieval failed: %s", result)
            raise HTTPException(status_code=status_code, detail="Raben ETA retrieval failed")
        return result
    except HTTPException:
        raise
    except Exception:
        logger.exception("Raben ETA retrieval failed")
        raise HTTPException(status_code=500, detail="Raben ETA retrieval failed")


# ---------------------------------------------------------------------------
# Labels
# ---------------------------------------------------------------------------


@app.post("/labels")
async def get_label(request: LabelRequest):
    try:
        label_data, status_code = await integration.get_label(
            request.credentials,
            request.waybill_number,
            request.format,
        )
        if status_code >= 400:
            logger.error("Raben label retrieval failed: %s", label_data)
            raise HTTPException(status_code=status_code, detail="Raben label retrieval failed")
        media_type = "application/pdf" if request.format == "pdf" else "application/x-zpl"
        return Response(content=label_data, media_type=media_type)
    except HTTPException:
        raise
    except Exception:
        logger.exception("Failed to get Raben label")
        raise HTTPException(status_code=500, detail="Raben label retrieval failed")


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
            logger.error("Raben claim creation failed: %s", result)
            raise HTTPException(status_code=status_code, detail="Raben claim creation failed")
        return JSONResponse(content=result, status_code=status_code)
    except HTTPException:
        raise
    except Exception:
        logger.exception("Failed to create Raben claim")
        raise HTTPException(status_code=500, detail="Raben claim creation failed")


# ---------------------------------------------------------------------------
# Delivery confirmation (PCD)
# ---------------------------------------------------------------------------


@app.get("/deliveries/{waybill_number}/confirmation")
async def get_delivery_confirmation(
    waybill_number: str,
    username: str = Header(..., alias="X-Username"),
    password: str = Header(..., alias="X-Password"),
    customer_number: str | None = Header(default=None, alias="X-Customer-Number"),
    sandbox_mode: bool = Header(default=False, alias="X-Sandbox-Mode"),
):
    credentials = RabenCredentials(
        username=username,
        password=password,
        customer_number=customer_number,
        sandbox_mode=sandbox_mode,
    )
    try:
        result, status_code = await integration.get_delivery_confirmation(
            credentials,
            waybill_number,
        )
        if status_code >= 400:
            logger.error("Raben delivery confirmation retrieval failed: %s", result)
            raise HTTPException(status_code=status_code, detail="Raben delivery confirmation retrieval failed")
        return result
    except HTTPException:
        raise
    except Exception:
        logger.exception("Raben delivery confirmation retrieval failed")
        raise HTTPException(status_code=500, detail="Raben delivery confirmation retrieval failed")


if augment_legacy_fastapi_app is not None:
    app = augment_legacy_fastapi_app(
        app,
        manifest_path=Path(__file__).resolve().parent.parent / "connector.yaml",
    )
