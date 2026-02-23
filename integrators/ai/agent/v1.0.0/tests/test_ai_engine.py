"""Tests for AI Engine — prompt construction and response parsing."""

import json
from unittest.mock import MagicMock, patch

import pytest

from src.ai_engine import _parse_json_response
from src.schemas import AiCredentials


MOCK_CREDS = AiCredentials(gemini_api_key="test-key", model_name="gemini-2.5-flash")


class TestParseJsonResponse:
    def test_plain_json(self):
        result = _parse_json_response('{"key": "value"}')
        assert result == {"key": "value"}

    def test_json_with_code_fence(self):
        text = '```json\n{"key": "value"}\n```'
        result = _parse_json_response(text)
        assert result == {"key": "value"}

    def test_json_with_plain_code_fence(self):
        text = '```\n{"score": 42}\n```'
        result = _parse_json_response(text)
        assert result == {"score": 42}

    def test_nested_json(self):
        data = {"risk_score": 75, "factors": [{"name": "high_value", "weight": 0.8}]}
        result = _parse_json_response(json.dumps(data))
        assert result == data

    def test_invalid_json_raises(self):
        with pytest.raises(json.JSONDecodeError):
            _parse_json_response("not json at all")


class TestAnalyze:
    @patch("src.ai_engine._build_client")
    @pytest.mark.asyncio
    async def test_analyze_with_schema(self, mock_build):
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = json.dumps({"category": "electronics", "urgency": "high"})
        mock_response.usage_metadata = MagicMock(total_token_count=200)
        mock_client.models.generate_content.return_value = mock_response
        mock_build.return_value = mock_client

        from src.ai_engine import analyze

        result = await analyze(
            credentials=MOCK_CREDS,
            prompt="Categorize this order",
            data={"product": "iPhone 15", "note": "Need ASAP"},
            output_schema={"category": "string", "urgency": "string"},
        )

        assert result.result["category"] == "electronics"
        assert result.tokens_used == 200
        assert result.model_used == "gemini-2.5-flash"

    @patch("src.ai_engine._build_client")
    @pytest.mark.asyncio
    async def test_analyze_plain_text_response(self, mock_build):
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "This is a summary of the data."
        mock_response.usage_metadata = None
        mock_client.models.generate_content.return_value = mock_response
        mock_build.return_value = mock_client

        from src.ai_engine import analyze

        result = await analyze(
            credentials=MOCK_CREDS,
            prompt="Summarize this",
            data="Some order data",
        )

        assert isinstance(result.result, str)
        assert result.tokens_used is None

    @patch("src.ai_engine._build_client")
    @pytest.mark.asyncio
    async def test_analyze_passes_temperature(self, mock_build):
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = json.dumps({"answer": "creative"})
        mock_response.usage_metadata = MagicMock(total_token_count=50)
        mock_client.models.generate_content.return_value = mock_response
        mock_build.return_value = mock_client

        from src.ai_engine import analyze

        await analyze(
            credentials=MOCK_CREDS,
            prompt="Be creative",
            data={"input": "test"},
            temperature=0.9,
        )

        call_kwargs = mock_client.models.generate_content.call_args
        config = call_kwargs.kwargs.get("config") or call_kwargs[1].get("config")
        assert config.temperature == 0.9


class TestAnalyzeRisk:
    @patch("src.ai_engine._build_client")
    @pytest.mark.asyncio
    async def test_risk_analysis_builds_correct_prompt(self, mock_build):
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = json.dumps({
            "risk_score": 30,
            "risk_level": "low",
            "recommendation": "approve",
            "risk_factors": [],
            "reasoning": "Normal order",
            "confidence": 0.9,
        })
        mock_client.models.generate_content.return_value = mock_response
        mock_build.return_value = mock_client

        from src.ai_engine import analyze_risk

        result = await analyze_risk(
            credentials=MOCK_CREDS,
            order_data={"order_id": "TEST-1", "value": 100},
            customer_history={"total_orders": 5},
            extra_context="Returning customer",
        )

        assert result.risk_score == 30
        assert result.risk_level.value == "low"
        assert result.recommendation.value == "approve"

        call_args = mock_client.models.generate_content.call_args
        prompt = call_args.kwargs.get("contents") or call_args[1].get("contents")
        assert "TEST-1" in prompt
        assert "Returning customer" in prompt


class TestRecommendCourier:
    @patch("src.ai_engine._build_client")
    @pytest.mark.asyncio
    async def test_courier_recommendation(self, mock_build):
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = json.dumps({
            "recommended_courier": "inpost",
            "score": 0.92,
            "reasoning": "Best for small parcels in PL",
            "alternatives": [
                {
                    "courier": "dhl",
                    "score": 0.80,
                    "reasoning": "Good alternative",
                    "estimated_cost_pln": 18.0,
                    "estimated_delivery_days": 2,
                }
            ],
            "estimated_cost_pln": 12.99,
            "estimated_delivery_days": 1,
            "confidence": 0.88,
        })
        mock_client.models.generate_content.return_value = mock_response
        mock_build.return_value = mock_client

        from src.ai_engine import recommend_courier

        result = await recommend_courier(
            credentials=MOCK_CREDS,
            order_data={"weight_kg": 1.5, "destination": "Krakow"},
            available_couriers=["inpost", "dhl", "dpd"],
        )

        assert result.recommended_courier == "inpost"
        assert len(result.alternatives) == 1
        assert result.alternatives[0].courier == "dhl"
