"""Tests for AI Agent connector — app endpoints."""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from src.app import app
from src.schemas import (
    AnalyzeResponse,
    CourierRecommendationResponse,
    DataExtractionResponse,
    PriorityClassificationResponse,
    PriorityLevel,
    Recommendation,
    RiskAnalysisResponse,
    RiskFactor,
    RiskLevel,
)

client = TestClient(app)

MOCK_CREDENTIALS = {
    "gemini_api_key": "test-key-123",
    "model_name": "gemini-2.5-flash",
}


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["version"] == "1.0.0"
    assert data["system"] == "ai-agent"


def test_readiness():
    response = client.get("/readiness")
    assert response.status_code == 200
    data = response.json()
    assert "checks" in data
    assert "model" in data


# ── Fixtures ─────────────────────────────────────────────────────

@pytest.fixture
def mock_analyze_response():
    return AnalyzeResponse(
        analysis_id="test-gen",
        result={"sentiment": "positive", "category": "electronics"},
        confidence=0.9,
        model_used="gemini-2.5-flash",
        tokens_used=150,
    )


@pytest.fixture
def mock_risk_response():
    return RiskAnalysisResponse(
        analysis_id="test-123",
        risk_score=25,
        risk_level=RiskLevel.LOW,
        recommendation=Recommendation.APPROVE,
        risk_factors=[
            RiskFactor(
                factor="normal_value",
                severity=RiskLevel.LOW,
                description="Order value within normal range",
            )
        ],
        reasoning="Standard order with no risk indicators",
        confidence=0.92,
    )


@pytest.fixture
def mock_courier_response():
    return CourierRecommendationResponse(
        analysis_id="test-456",
        recommended_courier="inpost",
        score=0.95,
        reasoning="Best price-to-speed ratio for small parcel in Poland",
        alternatives=[],
        estimated_cost_pln=12.99,
        estimated_delivery_days=2,
        confidence=0.88,
    )


@pytest.fixture
def mock_priority_response():
    return PriorityClassificationResponse(
        analysis_id="test-789",
        priority=PriorityLevel.HIGH,
        reasoning="VIP customer with express delivery request",
        suggested_actions=["Process within 1 hour", "Use express courier"],
        confidence=0.91,
    )


@pytest.fixture
def mock_extraction_response():
    return DataExtractionResponse(
        analysis_id="test-extract",
        extracted_data={
            "name": "Jan Kowalski",
            "street": "Marszalkowska 1",
            "city": "Warszawa",
            "zip": "00-001",
        },
        confidence=0.95,
        warnings=[],
    )


# ── Main action: /analyze ───────────────────────────────────────

class TestAnalyze:
    @patch("src.app.ai_engine.analyze", new_callable=AsyncMock)
    def test_analyze_success(self, mock_fn, mock_analyze_response):
        mock_fn.return_value = mock_analyze_response

        response = client.post(
            "/analyze",
            json={
                "credentials": MOCK_CREDENTIALS,
                "prompt": "Classify this product review sentiment",
                "data": {"review": "Great product, fast delivery!"},
                "output_schema": {"sentiment": "string", "category": "string"},
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["result"]["sentiment"] == "positive"
        assert data["model_used"] == "gemini-2.5-flash"
        assert data["tokens_used"] == 150

    @patch("src.app.ai_engine.analyze", new_callable=AsyncMock)
    def test_analyze_without_schema(self, mock_fn):
        mock_fn.return_value = AnalyzeResponse(
            analysis_id="test-no-schema",
            result="The data looks consistent and valid.",
            confidence=0.85,
            model_used="gemini-2.5-flash",
            tokens_used=80,
        )

        response = client.post(
            "/analyze",
            json={
                "credentials": MOCK_CREDENTIALS,
                "prompt": "Summarize this data",
                "data": {"key": "value"},
            },
        )

        assert response.status_code == 200
        assert isinstance(response.json()["result"], str)

    @patch("src.app.ai_engine.analyze", new_callable=AsyncMock)
    def test_analyze_error(self, mock_fn):
        mock_fn.side_effect = Exception("API quota exceeded")

        response = client.post(
            "/analyze",
            json={
                "credentials": MOCK_CREDENTIALS,
                "prompt": "Test",
                "data": {"x": 1},
            },
        )

        assert response.status_code == 500
        assert "API quota exceeded" in response.json()["detail"]


# ── Template: Risk ───────────────────────────────────────────────

class TestRiskAnalysis:
    @patch("src.app.ai_engine.analyze_risk", new_callable=AsyncMock)
    def test_analyze_risk_success(self, mock_fn, mock_risk_response):
        mock_fn.return_value = mock_risk_response

        response = client.post(
            "/analyze/risk",
            json={
                "credentials": MOCK_CREDENTIALS,
                "order_data": {
                    "order_id": "ORD-001",
                    "total_value": 150.0,
                    "items": [{"name": "T-shirt", "quantity": 2}],
                },
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["risk_score"] == 25
        assert data["risk_level"] == "low"
        assert data["recommendation"] == "approve"

    @patch("src.app.ai_engine.analyze_risk", new_callable=AsyncMock)
    def test_analyze_risk_high_score(self, mock_fn):
        mock_fn.return_value = RiskAnalysisResponse(
            analysis_id="test-high",
            risk_score=75,
            risk_level=RiskLevel.HIGH,
            recommendation=Recommendation.REVIEW,
            risk_factors=[],
            reasoning="Suspicious patterns",
            confidence=0.85,
        )

        response = client.post(
            "/analyze/risk",
            json={
                "credentials": MOCK_CREDENTIALS,
                "order_data": {"order_id": "ORD-SUS"},
            },
        )

        assert response.status_code == 200
        assert response.json()["risk_score"] == 75


# ── Template: Courier ────────────────────────────────────────────

class TestCourierRecommendation:
    @patch("src.app.ai_engine.recommend_courier", new_callable=AsyncMock)
    def test_recommend_courier_success(self, mock_fn, mock_courier_response):
        mock_fn.return_value = mock_courier_response

        response = client.post(
            "/analyze/courier",
            json={
                "credentials": MOCK_CREDENTIALS,
                "order_data": {"weight_kg": 2.5, "destination": "Krakow"},
                "preferences": {"optimize_for": "cost"},
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["recommended_courier"] == "inpost"
        assert data["estimated_cost_pln"] == 12.99


# ── Template: Priority ──────────────────────────────────────────

class TestPriorityClassification:
    @patch("src.app.ai_engine.classify_priority", new_callable=AsyncMock)
    def test_classify_priority_success(self, mock_fn, mock_priority_response):
        mock_fn.return_value = mock_priority_response

        response = client.post(
            "/analyze/priority",
            json={
                "credentials": MOCK_CREDENTIALS,
                "order_data": {"order_id": "ORD-VIP", "total_value": 5000.0},
                "customer_tier": "vip",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["priority"] == "high"
        assert len(data["suggested_actions"]) > 0


# ── Template: Extraction ────────────────────────────────────────

class TestDataExtraction:
    @patch("src.app.ai_engine.extract_data", new_callable=AsyncMock)
    def test_extract_data_success(self, mock_fn, mock_extraction_response):
        mock_fn.return_value = mock_extraction_response

        response = client.post(
            "/analyze/extract",
            json={
                "credentials": MOCK_CREDENTIALS,
                "input_text": "Jan Kowalski, ul. Marszalkowska 1, 00-001 Warszawa",
                "extraction_schema": {
                    "name": "string",
                    "street": "string",
                    "city": "string",
                    "zip": "string",
                },
                "input_type": "address",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["extracted_data"]["name"] == "Jan Kowalski"
        assert data["extracted_data"]["city"] == "Warszawa"


# ── Generic action routing ──────────────────────────────────────

class TestGenericAction:
    @patch("src.app.ai_engine.analyze", new_callable=AsyncMock)
    def test_generic_analyze(self, mock_fn, mock_analyze_response):
        mock_fn.return_value = mock_analyze_response

        response = client.post(
            "/actions/agent.analyze",
            json={
                "gemini_api_key": "test-key",
                "prompt": "Analyze this",
                "data": {"key": "value"},
            },
        )

        assert response.status_code == 200
        assert response.json()["result"]["sentiment"] == "positive"

    @patch("src.app.ai_engine.analyze_risk", new_callable=AsyncMock)
    def test_generic_risk(self, mock_fn, mock_risk_response):
        mock_fn.return_value = mock_risk_response

        response = client.post(
            "/actions/agent.analyze_risk",
            json={
                "gemini_api_key": "test-key",
                "order_data": {"order_id": "ORD-001"},
            },
        )

        assert response.status_code == 200
        assert response.json()["risk_score"] == 25

    def test_generic_unknown_action(self):
        response = client.post(
            "/actions/unknown.action",
            json={"data": "test"},
        )

        assert response.status_code == 404
