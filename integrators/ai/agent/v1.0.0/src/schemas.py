"""Pydantic schemas for AI Agent connector."""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

# ── Enums ────────────────────────────────────────────────────────


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Recommendation(str, Enum):
    APPROVE = "approve"
    REVIEW = "review"
    REJECT = "reject"


class PriorityLevel(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class CourierPreference(str, Enum):
    COST = "cost"
    SPEED = "speed"
    RELIABILITY = "reliability"


# ── Credentials ──────────────────────────────────────────────────


class AiCredentials(BaseModel):
    gemini_api_key: str = Field(..., description="Google Gemini API key")
    model_name: str = Field(default="gemini-2.5-flash")


# ── Main action: agent.analyze (prompt + data → result) ─────────


class AnalyzeRequest(BaseModel):
    credentials: AiCredentials
    prompt: str = Field(..., description="Instruction prompt for the AI agent")
    data: dict[str, Any] | str = Field(..., description="Data to analyze (JSON or text)")
    output_schema: dict[str, Any] | None = Field(
        default=None, description="Expected JSON output structure — AI will conform to it"
    )
    temperature: float | None = Field(default=None, ge=0.0, le=1.0)
    max_tokens: int | None = Field(default=None)


class AnalyzeResponse(BaseModel):
    analysis_id: str
    result: dict[str, Any] | str
    confidence: float = Field(ge=0.0, le=1.0)
    model_used: str
    tokens_used: int | None = None


# ── Template: Risk Analysis ─────────────────────────────────────


class RiskAnalysisRequest(BaseModel):
    credentials: AiCredentials
    order_data: dict[str, Any] = Field(..., description="Order data to analyze")
    customer_history: dict[str, Any] | None = Field(default=None, description="Past orders, returns, disputes")
    extra_context: str | None = Field(default=None, description="Additional context for the analysis")


class RiskFactor(BaseModel):
    factor: str
    severity: RiskLevel
    description: str


class RiskAnalysisResponse(BaseModel):
    analysis_id: str
    risk_score: int = Field(ge=0, le=100)
    risk_level: RiskLevel
    recommendation: Recommendation
    risk_factors: list[RiskFactor]
    reasoning: str
    confidence: float = Field(ge=0.0, le=1.0)


# ── Template: Courier Recommendation ────────────────────────────


class CourierPreferences(BaseModel):
    optimize_for: CourierPreference = CourierPreference.COST
    max_delivery_days: int | None = None
    max_cost_pln: float | None = None
    require_pickup_points: bool = False
    require_cod: bool = False


class CourierRecommendationRequest(BaseModel):
    credentials: AiCredentials
    order_data: dict[str, Any] = Field(..., description="Order data with dimensions/weight")
    available_couriers: list[str] | None = Field(default=None, description="Courier names to choose from")
    preferences: CourierPreferences | None = None
    destination_country: str = Field(default="PL")


class CourierAlternative(BaseModel):
    courier: str
    score: float = Field(ge=0.0, le=1.0)
    reasoning: str
    estimated_cost_pln: float | None = None
    estimated_delivery_days: int | None = None


class CourierRecommendationResponse(BaseModel):
    analysis_id: str
    recommended_courier: str
    score: float = Field(ge=0.0, le=1.0)
    reasoning: str
    alternatives: list[CourierAlternative]
    estimated_cost_pln: float | None = None
    estimated_delivery_days: int | None = None
    confidence: float = Field(ge=0.0, le=1.0)


# ── Template: Priority Classification ───────────────────────────


class PriorityClassificationRequest(BaseModel):
    credentials: AiCredentials
    order_data: dict[str, Any]
    customer_tier: str | None = Field(default=None, description="standard / premium / vip")
    sla_rules: dict[str, Any] | None = Field(default=None, description="Custom SLA rules")


class PriorityClassificationResponse(BaseModel):
    analysis_id: str
    priority: PriorityLevel
    reasoning: str
    suggested_actions: list[str]
    confidence: float = Field(ge=0.0, le=1.0)


# ── Template: Data Extraction ───────────────────────────────────


class DataExtractionRequest(BaseModel):
    credentials: AiCredentials
    input_text: str = Field(..., description="Unstructured text to extract data from")
    extraction_schema: dict[str, Any] = Field(..., description="JSON schema describing fields to extract")
    input_type: str = Field(default="custom", description="email / invoice / address / custom")


class DataExtractionResponse(BaseModel):
    analysis_id: str
    extracted_data: dict[str, Any]
    confidence: float = Field(ge=0.0, le=1.0)
    warnings: list[str] = Field(default_factory=list)
