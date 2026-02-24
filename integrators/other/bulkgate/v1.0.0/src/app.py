"""BulkGate SMS Gateway Integrator — FastAPI application."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from src.api import BulkGateApiClient
from src.config import settings
from src.schemas import (
    CheckBalanceRequest,
    DeliveryReportPayload,
    IncomingSmsPayload,
    SendAdvancedSmsRequest,
    SendPromotionalSmsRequest,
    SendTransactionalSmsRequest,
)

logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s %(levelname)-8s %(name)s — %(message)s",
)
logger = logging.getLogger("automation-bulkgate")

client: BulkGateApiClient | None = None


@asynccontextmanager
async def lifespan(application: FastAPI):
    global client
    client = BulkGateApiClient()
    yield
    await client.close()


app = FastAPI(
    title="Pinquark Integrator — BulkGate SMS Gateway",
    version="1.0.0",
    docs_url="/docs",
    lifespan=lifespan,
)


def _get_client() -> BulkGateApiClient:
    if client is None:
        raise HTTPException(status_code=503, detail="Service not ready")
    return client


async def _handle_result(result: dict[str, Any], status_code: int) -> JSONResponse:
    if status_code >= 400:
        raise HTTPException(status_code=status_code, detail=result)
    return JSONResponse(content=result, status_code=status_code)


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

@app.get("/health")
async def health():
    return {"status": "healthy", "version": "1.0.0", "system": "bulkgate-sms-gateway"}


@app.get("/readiness")
async def readiness():
    checks: dict[str, str] = {"api_client": "ok" if client is not None else "not_ready"}
    status = "healthy" if all(v == "ok" for v in checks.values()) else "degraded"
    return {"status": status, "checks": checks}


# ---------------------------------------------------------------------------
# SMS endpoints
# ---------------------------------------------------------------------------

@app.post("/sms/transactional", status_code=200)
async def send_transactional_sms(request: SendTransactionalSmsRequest):
    try:
        result, status_code = await _get_client().send_transactional_sms(
            request.credentials,
            request.number,
            request.text,
            unicode=request.unicode,
            sender_id=request.sender_id,
            sender_id_value=request.sender_id_value,
            country=request.country,
            schedule=request.schedule,
            duplicates_check=request.duplicates_check,
            tag=request.tag,
        )
        return await _handle_result(result, status_code)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Failed to send transactional SMS")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/sms/promotional", status_code=200)
async def send_promotional_sms(request: SendPromotionalSmsRequest):
    try:
        result, status_code = await _get_client().send_promotional_sms(
            request.credentials,
            request.number,
            request.text,
            unicode=request.unicode,
            sender_id=request.sender_id,
            sender_id_value=request.sender_id_value,
            country=request.country,
            schedule=request.schedule,
            duplicates_check=request.duplicates_check,
            tag=request.tag,
        )
        return await _handle_result(result, status_code)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Failed to send promotional SMS")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/sms/advanced", status_code=200)
async def send_advanced_sms(request: SendAdvancedSmsRequest):
    try:
        result, status_code = await _get_client().send_advanced_transactional(
            request.credentials,
            request.number,
            request.text,
            variables=request.variables,
            channel=request.channel,
            country=request.country,
            schedule=request.schedule,
            duplicates_check=request.duplicates_check,
            tag=request.tag,
        )
        return await _handle_result(result, status_code)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Failed to send advanced transactional SMS")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# ---------------------------------------------------------------------------
# Account
# ---------------------------------------------------------------------------

@app.post("/account/balance", status_code=200)
async def check_balance(request: CheckBalanceRequest):
    try:
        result, status_code = await _get_client().check_credit_balance(request.credentials)
        return await _handle_result(result, status_code)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Failed to check credit balance")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# ---------------------------------------------------------------------------
# Webhooks — delivery reports & incoming SMS
# ---------------------------------------------------------------------------

@app.post("/webhooks/delivery-report", status_code=200)
async def delivery_report_webhook(request: Request):
    """Receives delivery report callbacks from BulkGate.
    Configure the webhook URL in BulkGate Portal → API settings → Delivery reports.
    """
    try:
        body = await request.json()
        report = DeliveryReportPayload(**body) if isinstance(body, dict) else None
        logger.info(
            "Delivery report received: sms_id=%s status=%s",
            report.sms_id if report else "unknown",
            report.status if report else "unknown",
        )
        return {"status": "received", "data": body}
    except Exception as exc:
        logger.exception("Failed to process delivery report webhook")
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/webhooks/incoming-sms", status_code=200)
async def incoming_sms_webhook(request: Request):
    """Receives incoming SMS (replies) from BulkGate."""
    try:
        body = await request.json()
        incoming = IncomingSmsPayload(**body) if isinstance(body, dict) else None
        logger.info(
            "Incoming SMS received: sender=%s",
            incoming.sender if incoming else "unknown",
        )
        return {"status": "received", "data": body}
    except Exception as exc:
        logger.exception("Failed to process incoming SMS webhook")
        raise HTTPException(status_code=400, detail=str(exc)) from exc
