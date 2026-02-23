"""AI Engine — Google Gemini client with prompt management."""

from __future__ import annotations

import json
import uuid
from typing import Any

from google import genai
from google.genai import types

from src.config import settings
from src.schemas import (
    AiCredentials,
    AnalyzeResponse,
    CourierAlternative,
    CourierPreferences,
    CourierRecommendationResponse,
    DataExtractionResponse,
    PriorityClassificationResponse,
    PriorityLevel,
    Recommendation,
    RiskAnalysisResponse,
    RiskFactor,
    RiskLevel,
)


# ── Prompt templates for built-in analysis types ─────────────────

RISK_ANALYSIS_PROMPT = """\
You are a fraud detection specialist for an e-commerce integration platform.
Analyze the following order data and assess the risk of fraud or issues.

Consider these factors:
- Address consistency (shipping vs billing)
- Order value anomalies (unusually high quantities, expensive items)
- Customer behavior patterns (if history provided)
- Geographic risk signals (cross-border, known high-risk regions)
- Product category risk (electronics, gift cards are higher risk)
- Payment method indicators
- Time-of-day patterns (orders placed at unusual hours)

Respond with a JSON object matching this exact schema:
{{
  "risk_score": <integer 0-100>,
  "risk_level": "<low|medium|high|critical>",
  "recommendation": "<approve|review|reject>",
  "risk_factors": [
    {{
      "factor": "<short name>",
      "severity": "<low|medium|high|critical>",
      "description": "<explanation>"
    }}
  ],
  "reasoning": "<overall assessment>",
  "confidence": <float 0.0-1.0>
}}

Risk level thresholds: 0-30=low, 31-59=medium, 60-84=high, 85-100=critical.
Recommendation mapping: low/medium=approve, high=review, critical=reject.

ORDER DATA:
{order_data}

CUSTOMER HISTORY:
{customer_history}

ADDITIONAL CONTEXT:
{extra_context}
"""

COURIER_RECOMMENDATION_PROMPT = """\
You are a logistics optimization specialist for a Polish e-commerce platform.
Based on the order data and preferences, recommend the best courier service.

Available couriers and their general characteristics (Polish market):
- inpost: Paczkomaty (lockers) + courier. Cheapest for small parcels. Fast in Poland.
- dhl: Reliable international + domestic. Good for heavier parcels.
- dpd: Strong domestic network. Competitive pricing for business clients.
- gls: Good European coverage. Competitive for medium parcels.
- fedex: Premium international shipping. Fastest for overseas.
- ups: Strong international + domestic. Good for B2B.
- pocztapolska: Cheapest option. Slower delivery. Wide rural coverage.
- orlenpaczka: Budget option with parcel lockers. Growing network.
- schenker: LTL/FTL freight. Best for pallets and heavy shipments.
- suus: Regional Polish courier. Good for local deliveries.
- paxy: Same-day delivery in major cities.
- packeta: Central European focus (CZ, SK, HU, PL).
- geis: Heavy freight specialist. Good for oversized parcels.

Consider: parcel dimensions/weight, destination, delivery speed needed,
cost optimization, COD requirement, pickup point availability.

Respond with JSON:
{{
  "recommended_courier": "<courier name>",
  "score": <float 0.0-1.0>,
  "reasoning": "<why this courier is best>",
  "alternatives": [
    {{
      "courier": "<name>",
      "score": <float>,
      "reasoning": "<why it's an alternative>",
      "estimated_cost_pln": <float or null>,
      "estimated_delivery_days": <int or null>
    }}
  ],
  "estimated_cost_pln": <float or null>,
  "estimated_delivery_days": <int or null>,
  "confidence": <float 0.0-1.0>
}}

ORDER DATA:
{order_data}

AVAILABLE COURIERS: {available_couriers}
DESTINATION COUNTRY: {destination_country}
OPTIMIZATION PREFERENCE: {optimize_for}
CONSTRAINTS: max_delivery_days={max_delivery_days}, max_cost={max_cost_pln}, \
pickup_points_required={require_pickup_points}, cod_required={require_cod}
"""

PRIORITY_CLASSIFICATION_PROMPT = """\
You are an order prioritization specialist. Classify the order priority based on:
- Customer tier (VIP/premium customers get higher priority)
- Product type (perishable, time-sensitive items)
- Delivery deadline commitments
- Order value
- Custom SLA rules if provided

Priority levels: low, normal, high, urgent.

Respond with JSON:
{{
  "priority": "<low|normal|high|urgent>",
  "reasoning": "<explanation>",
  "suggested_actions": ["<action 1>", "<action 2>"],
  "confidence": <float 0.0-1.0>
}}

ORDER DATA:
{order_data}

CUSTOMER TIER: {customer_tier}
SLA RULES: {sla_rules}
"""

DATA_EXTRACTION_PROMPT = """\
You are a data extraction specialist. Extract structured data from the input text
according to the provided schema.

INPUT TYPE: {input_type}

EXTRACTION SCHEMA (fields to extract):
{extraction_schema}

INPUT TEXT:
{input_text}

Respond with JSON:
{{
  "extracted_data": {{ <extracted fields matching schema> }},
  "confidence": <float 0.0-1.0>,
  "warnings": ["<any issues or uncertainties>"]
}}

If a field cannot be extracted, set it to null and add a warning.
"""


# ── Helpers ──────────────────────────────────────────────────────

def _build_client(credentials: AiCredentials) -> genai.Client:
    return genai.Client(api_key=credentials.gemini_api_key)


def _parse_json_response(text: str) -> dict[str, Any]:
    """Extract JSON from model response, handling markdown code fences."""
    cleaned = text.strip()
    if cleaned.startswith("```"):
        first_newline = cleaned.index("\n")
        last_fence = cleaned.rfind("```")
        cleaned = cleaned[first_newline + 1 : last_fence].strip()
    return json.loads(cleaned)


# ── Main action: generic prompt-based analysis ──────────────────

async def analyze(
    credentials: AiCredentials,
    prompt: str,
    data: dict[str, Any] | str,
    output_schema: dict[str, Any] | None = None,
    temperature: float | None = None,
    max_tokens: int | None = None,
) -> AnalyzeResponse:
    """Core action — send prompt + data to AI, get structured result."""
    client = _build_client(credentials)
    model_name = credentials.model_name or settings.model_name

    schema_instruction = ""
    if output_schema:
        schema_instruction = (
            f"\n\nRespond with JSON matching this schema:\n"
            f"{json.dumps(output_schema, ensure_ascii=False, indent=2)}"
        )

    data_str = (
        json.dumps(data, ensure_ascii=False, indent=2)
        if isinstance(data, dict)
        else str(data)
    )

    full_prompt = f"{prompt}{schema_instruction}\n\nDATA:\n{data_str}"

    response = client.models.generate_content(
        model=model_name,
        contents=full_prompt,
        config=types.GenerateContentConfig(
            temperature=temperature or settings.default_temperature,
            max_output_tokens=max_tokens or settings.max_tokens,
            response_mime_type="application/json" if output_schema else None,
        ),
    )

    try:
        result = _parse_json_response(response.text)
    except (json.JSONDecodeError, ValueError):
        result = response.text

    usage = response.usage_metadata
    tokens = usage.total_token_count if usage else None

    return AnalyzeResponse(
        analysis_id=str(uuid.uuid4()),
        result=result,
        confidence=0.8,
        model_used=model_name,
        tokens_used=tokens,
    )


# ── Built-in template: Risk Analysis ────────────────────────────

async def analyze_risk(
    credentials: AiCredentials,
    order_data: dict[str, Any],
    customer_history: dict[str, Any] | None = None,
    extra_context: str | None = None,
) -> RiskAnalysisResponse:
    client = _build_client(credentials)
    model_name = credentials.model_name or settings.model_name

    prompt = RISK_ANALYSIS_PROMPT.format(
        order_data=json.dumps(order_data, ensure_ascii=False, indent=2),
        customer_history=json.dumps(customer_history, ensure_ascii=False, indent=2)
        if customer_history
        else "No history available",
        extra_context=extra_context or "None",
    )

    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=settings.default_temperature,
            max_output_tokens=settings.max_tokens,
            response_mime_type="application/json",
        ),
    )

    data = _parse_json_response(response.text)

    risk_factors = [
        RiskFactor(
            factor=f["factor"],
            severity=RiskLevel(f["severity"]),
            description=f["description"],
        )
        for f in data.get("risk_factors", [])
    ]

    return RiskAnalysisResponse(
        analysis_id=str(uuid.uuid4()),
        risk_score=data["risk_score"],
        risk_level=RiskLevel(data["risk_level"]),
        recommendation=Recommendation(data["recommendation"]),
        risk_factors=risk_factors,
        reasoning=data["reasoning"],
        confidence=data.get("confidence", 0.8),
    )


# ── Built-in template: Courier Recommendation ───────────────────

async def recommend_courier(
    credentials: AiCredentials,
    order_data: dict[str, Any],
    available_couriers: list[str] | None = None,
    preferences: CourierPreferences | None = None,
    destination_country: str = "PL",
) -> CourierRecommendationResponse:
    client = _build_client(credentials)
    model_name = credentials.model_name or settings.model_name

    prefs = preferences or CourierPreferences()
    couriers = available_couriers or settings.courier_list

    prompt = COURIER_RECOMMENDATION_PROMPT.format(
        order_data=json.dumps(order_data, ensure_ascii=False, indent=2),
        available_couriers=", ".join(couriers),
        destination_country=destination_country,
        optimize_for=prefs.optimize_for.value,
        max_delivery_days=prefs.max_delivery_days or "no limit",
        max_cost_pln=prefs.max_cost_pln or "no limit",
        require_pickup_points=prefs.require_pickup_points,
        require_cod=prefs.require_cod,
    )

    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=settings.default_temperature,
            max_output_tokens=settings.max_tokens,
            response_mime_type="application/json",
        ),
    )

    data = _parse_json_response(response.text)

    alternatives = [
        CourierAlternative(
            courier=a["courier"],
            score=a["score"],
            reasoning=a["reasoning"],
            estimated_cost_pln=a.get("estimated_cost_pln"),
            estimated_delivery_days=a.get("estimated_delivery_days"),
        )
        for a in data.get("alternatives", [])
    ]

    return CourierRecommendationResponse(
        analysis_id=str(uuid.uuid4()),
        recommended_courier=data["recommended_courier"],
        score=data.get("score", 0.8),
        reasoning=data["reasoning"],
        alternatives=alternatives,
        estimated_cost_pln=data.get("estimated_cost_pln"),
        estimated_delivery_days=data.get("estimated_delivery_days"),
        confidence=data.get("confidence", 0.8),
    )


# ── Built-in template: Priority Classification ──────────────────

async def classify_priority(
    credentials: AiCredentials,
    order_data: dict[str, Any],
    customer_tier: str | None = None,
    sla_rules: dict[str, Any] | None = None,
) -> PriorityClassificationResponse:
    client = _build_client(credentials)
    model_name = credentials.model_name or settings.model_name

    prompt = PRIORITY_CLASSIFICATION_PROMPT.format(
        order_data=json.dumps(order_data, ensure_ascii=False, indent=2),
        customer_tier=customer_tier or "standard",
        sla_rules=json.dumps(sla_rules, ensure_ascii=False, indent=2)
        if sla_rules
        else "Default SLA",
    )

    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=settings.default_temperature,
            max_output_tokens=settings.max_tokens,
            response_mime_type="application/json",
        ),
    )

    data = _parse_json_response(response.text)

    return PriorityClassificationResponse(
        analysis_id=str(uuid.uuid4()),
        priority=PriorityLevel(data["priority"]),
        reasoning=data["reasoning"],
        suggested_actions=data.get("suggested_actions", []),
        confidence=data.get("confidence", 0.8),
    )


# ── Built-in template: Data Extraction ──────────────────────────

async def extract_data(
    credentials: AiCredentials,
    input_text: str,
    extraction_schema: dict[str, Any],
    input_type: str = "custom",
) -> DataExtractionResponse:
    client = _build_client(credentials)
    model_name = credentials.model_name or settings.model_name

    prompt = DATA_EXTRACTION_PROMPT.format(
        input_type=input_type,
        extraction_schema=json.dumps(extraction_schema, ensure_ascii=False, indent=2),
        input_text=input_text,
    )

    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.0,
            max_output_tokens=settings.max_tokens,
            response_mime_type="application/json",
        ),
    )

    data = _parse_json_response(response.text)

    return DataExtractionResponse(
        analysis_id=str(uuid.uuid4()),
        extracted_data=data.get("extracted_data", {}),
        confidence=data.get("confidence", 0.8),
        warnings=data.get("warnings", []),
    )
