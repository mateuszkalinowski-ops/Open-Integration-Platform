"""AI Agent — FastAPI application.

Universal AI agent connector powered by Google Gemini.
Takes a prompt and data, returns structured AI-generated response.
Includes built-in templates for common tasks: risk analysis,
courier recommendation, priority classification, data extraction.
"""

from __future__ import annotations

import logging

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from google import genai

from src import ai_engine
from src.config import settings
from src.schemas import (
    AnalyzeRequest,
    CourierRecommendationRequest,
    DataExtractionRequest,
    PriorityClassificationRequest,
    RiskAnalysisRequest,
)

logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s %(levelname)-8s %(name)s — %(message)s",
)
logger = logging.getLogger("ai-agent")

app = FastAPI(
    title="AI Agent Connector",
    version="1.0.0",
    description=(
        "Universal AI agent — give it a prompt and data, "
        "get structured results. Built-in templates for risk analysis, "
        "courier selection, priority classification, data extraction."
    ),
    docs_url="/docs",
)


# ── Health ───────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {"status": "healthy", "version": "1.0.0", "system": "ai-agent"}


@app.get("/readiness")
async def readiness():
    has_key = bool(settings.gemini_api_key)
    checks = {
        "gemini_api_key_configured": "ok" if has_key else "missing",
    }
    status = "healthy" if all(v == "ok" for v in checks.values()) else "degraded"
    return {"status": status, "checks": checks, "model": settings.model_name}


# ── Connection status ────────────────────────────────────────────

@app.get("/connection/{account_name}/status")
async def connection_status(
    account_name: str,
    gemini_api_key: str = Query("", description="API key override (falls back to env var)"),
):
    """Validate the Gemini API key by listing available models."""
    api_key = gemini_api_key or settings.gemini_api_key
    if not api_key:
        return {"connected": False, "error": "No Gemini API key configured"}
    try:
        client = genai.Client(api_key=api_key)
        models = list(client.models.list())
        return {
            "connected": True,
            "account_name": account_name,
            "model": settings.model_name,
            "available_models": len(models),
        }
    except Exception as exc:
        logger.warning("Gemini connection check failed: %s", exc)
        return {"connected": False, "error": str(exc)}


# ── PRIMARY: Generic prompt-based analysis ──────────────────────

@app.post("/analyze", status_code=200)
async def analyze(request: AnalyzeRequest):
    """Main endpoint — send prompt + data, get AI response."""
    try:
        result = await ai_engine.analyze(
            credentials=request.credentials,
            prompt=request.prompt,
            data=request.data,
            output_schema=request.output_schema,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
        )
        return JSONResponse(content=result.model_dump())
    except Exception as exc:
        logger.exception("Analysis failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# ── TEMPLATE: Risk Analysis ─────────────────────────────────────

@app.post("/analyze/risk", status_code=200)
async def analyze_risk(request: RiskAnalysisRequest):
    try:
        result = await ai_engine.analyze_risk(
            credentials=request.credentials,
            order_data=request.order_data,
            customer_history=request.customer_history,
            extra_context=request.extra_context,
        )
        response = result.model_dump()

        if result.risk_score >= settings.risk_threshold_critical:
            logger.warning(
                "CRITICAL risk detected: score=%d, id=%s",
                result.risk_score,
                result.analysis_id,
            )
        elif result.risk_score >= settings.risk_threshold_high:
            logger.warning(
                "HIGH risk detected: score=%d, id=%s",
                result.risk_score,
                result.analysis_id,
            )

        return JSONResponse(content=response)
    except Exception as exc:
        logger.exception("Risk analysis failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# ── TEMPLATE: Courier Recommendation ────────────────────────────

@app.post("/analyze/courier", status_code=200)
async def recommend_courier(request: CourierRecommendationRequest):
    try:
        result = await ai_engine.recommend_courier(
            credentials=request.credentials,
            order_data=request.order_data,
            available_couriers=request.available_couriers,
            preferences=request.preferences,
            destination_country=request.destination_country,
        )
        return JSONResponse(content=result.model_dump())
    except Exception as exc:
        logger.exception("Courier recommendation failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# ── TEMPLATE: Priority Classification ───────────────────────────

@app.post("/analyze/priority", status_code=200)
async def classify_priority(request: PriorityClassificationRequest):
    try:
        result = await ai_engine.classify_priority(
            credentials=request.credentials,
            order_data=request.order_data,
            customer_tier=request.customer_tier,
            sla_rules=request.sla_rules,
        )
        return JSONResponse(content=result.model_dump())
    except Exception as exc:
        logger.exception("Priority classification failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# ── TEMPLATE: Data Extraction ───────────────────────────────────

@app.post("/analyze/extract", status_code=200)
async def extract_data(request: DataExtractionRequest):
    try:
        result = await ai_engine.extract_data(
            credentials=request.credentials,
            input_text=request.input_text,
            extraction_schema=request.extraction_schema,
            input_type=request.input_type,
        )
        return JSONResponse(content=result.model_dump())
    except Exception as exc:
        logger.exception("Data extraction failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# ── Generic action endpoint (used by Flow Engine dispatcher) ────

@app.post("/actions/{action}")
async def generic_action(action: str, payload: dict):
    """Fallback for action dispatcher — maps action names to handlers."""
    action_handlers = {
        "agent.analyze": _handle_analyze,
        "agent.analyze_risk": _handle_risk,
        "agent.recommend_courier": _handle_courier,
        "agent.classify_priority": _handle_priority,
        "agent.extract_data": _handle_extract,
    }

    handler = action_handlers.get(action)
    if not handler:
        raise HTTPException(
            status_code=404,
            detail=f"Unknown action: {action}. Available: {list(action_handlers.keys())}",
        )

    return await handler(payload)


def _make_credentials(payload: dict) -> "AiCredentials":
    from src.schemas import AiCredentials
    return AiCredentials(
        gemini_api_key=payload.pop("gemini_api_key", settings.gemini_api_key),
        model_name=payload.pop("model_name", settings.model_name),
    )


async def _handle_analyze(payload: dict) -> dict:
    creds = _make_credentials(payload)
    result = await ai_engine.analyze(
        credentials=creds,
        prompt=payload.get("prompt", "Analyze the provided data"),
        data=payload.get("data", payload),
        output_schema=payload.get("output_schema"),
        temperature=payload.get("temperature"),
        max_tokens=payload.get("max_tokens"),
    )
    return result.model_dump()


async def _handle_risk(payload: dict) -> dict:
    creds = _make_credentials(payload)
    result = await ai_engine.analyze_risk(
        credentials=creds,
        order_data=payload.get("order_data", payload),
        customer_history=payload.get("customer_history"),
        extra_context=payload.get("extra_context"),
    )
    return result.model_dump()


async def _handle_courier(payload: dict) -> dict:
    from src.schemas import CourierPreferences
    creds = _make_credentials(payload)
    prefs_data = payload.get("preferences")
    prefs = CourierPreferences(**prefs_data) if prefs_data else None
    result = await ai_engine.recommend_courier(
        credentials=creds,
        order_data=payload.get("order_data", payload),
        available_couriers=payload.get("available_couriers"),
        preferences=prefs,
        destination_country=payload.get("destination_country", "PL"),
    )
    return result.model_dump()


async def _handle_priority(payload: dict) -> dict:
    creds = _make_credentials(payload)
    result = await ai_engine.classify_priority(
        credentials=creds,
        order_data=payload.get("order_data", payload),
        customer_tier=payload.get("customer_tier"),
        sla_rules=payload.get("sla_rules"),
    )
    return result.model_dump()


async def _handle_extract(payload: dict) -> dict:
    creds = _make_credentials(payload)
    result = await ai_engine.extract_data(
        credentials=creds,
        input_text=payload.get("input_text", ""),
        extraction_schema=payload.get("extraction_schema", {}),
        input_type=payload.get("input_type", "custom"),
    )
    return result.model_dump()
