"""
Tests for the response composer.

Verifies:
1. Bedrock API integration
2. JSON parsing (with and without markdown fences)
3. Response structure validation
4. Confidence level validation
5. Error handling and fallback answers
6. Execution trace formatting
7. Composition with realistic data
"""

import pytest
import json
from unittest.mock import Mock, patch
from composer import (
    compose_answer,
    _format_execution_trace,
    _parse_composed_response,
    _fallback_answer,
)


class TestFormatExecutionTrace:
    """Test execution trace formatting."""

    def test_format_single_step_trace(self):
        """Test formatting single-step execution trace."""
        trace = [
            {
                "step": 1,
                "tool": "forecast_demand",
                "result": {"sku_id": "SKU-123", "trend": "stable", "avg_forecasted_demand": 100}
            }
        ]
        result = _format_execution_trace(trace)
        assert isinstance(result, str)
        assert "forecast_demand" in result
        assert "100" in result

    def test_format_multi_step_trace(self):
        """Test formatting multi-step execution trace."""
        trace = [
            {
                "step": 1,
                "tool": "forecast_demand",
                "result": {"avg_forecasted_demand": 100}
            },
            {
                "step": 2,
                "tool": "predict_stockout",
                "result": {"days_until_stockout": 5.0, "risk_level": "high"}
            }
        ]
        result = _format_execution_trace(trace)
        assert "forecast_demand" in result
        assert "predict_stockout" in result
        assert "5.0" in result

    def test_format_empty_trace(self):
        """Test formatting empty trace."""
        result = _format_execution_trace([])
        assert result == "[]"

    def test_format_invalid_trace_type(self):
        """Test formatting with non-list trace."""
        result = _format_execution_trace("not-a-list")
        assert result == "[]"

    def test_format_trace_with_complex_results(self):
        """Test formatting trace with complex nested results."""
        trace = [
            {
                "step": 1,
                "tool": "supplier_risk_score",
                "result": {
                    "supplier_id": "SUP-001",
                    "score": 85.5,
                    "breakdown": {
                        "on_time_delivery_pct": 95.0,
                        "lead_time_variance_days": 2.1
                    }
                }
            }
        ]
        result = _format_execution_trace(trace)
        assert isinstance(result, str)
        assert "85.5" in result
        assert "SUP-001" in result


class TestParseComposedResponse:
    """Test parsing of composed responses."""

    def test_parse_plain_json(self):
        """Test parsing plain JSON response."""
        response = '{"answer": "SKU-123 is at risk.", "confidence": "high", "caveats": "based on 30-day forecast"}'
        result = _parse_composed_response(response)
        assert result is not None
        assert result["answer"] == "SKU-123 is at risk."
        assert result["confidence"] == "high"

    def test_parse_json_with_markdown_fences(self):
        """Test parsing JSON with markdown fences."""
        response = '''```json
{"answer": "Test answer", "confidence": "medium", "caveats": "Limited data"}
```'''
        result = _parse_composed_response(response)
        assert result is not None
        assert result["answer"] == "Test answer"

    def test_parse_json_with_triple_backticks(self):
        """Test parsing JSON with triple backticks."""
        response = '''```
{"answer": "Test answer", "confidence": "low", "caveats": "Data incomplete"}
```'''
        result = _parse_composed_response(response)
        assert result is not None
        assert result["confidence"] == "low"

    def test_parse_invalid_json(self):
        """Test parsing invalid JSON returns None."""
        result = _parse_composed_response("not valid json")
        assert result is None

    def test_parse_non_dict_json(self):
        """Test parsing non-dict JSON returns None."""
        result = _parse_composed_response("[1, 2, 3]")
        assert result is None

    def test_parse_non_string_input(self):
        """Test parsing non-string input returns None."""
        result = _parse_composed_response(123)
        assert result is None


class TestFallbackAnswer:
    """Test fallback answer generation."""

    def test_fallback_answer_structure(self):
        """Test that fallback answer has required structure."""
        result = _fallback_answer("test reason")
        assert "answer" in result
        assert "confidence" in result
        assert "caveats" in result

    def test_fallback_answer_is_low_confidence(self):
        """Test that fallback is marked as low confidence."""
        result = _fallback_answer("test reason")
        assert result["confidence"] == "low"

    def test_fallback_answer_includes_reason(self):
        """Test that fallback caveats include the reason."""
        reason = "specific error message"
        result = _fallback_answer(reason)
        assert reason in result["caveats"]


class TestComposeAnswer:
    """Test main composition function."""

    def test_compose_simple_answer(self):
        """Test composing answer from single-step execution."""
        mock_client = Mock()
        mock_response_body = Mock()
        mock_response_body.read.return_value = json.dumps({
            "answer": "SKU-WIDGET is at risk of stockout in 2 days based on current demand.",
            "confidence": "high",
            "caveats": "Assumes demand remains stable"
        }).encode("utf-8")
        mock_client.invoke_model.return_value = {"body": mock_response_body}

        trace = [
            {
                "step": 1,
                "tool": "predict_stockout",
                "result": {"days_until_stockout": 2.0, "risk_level": "critical"}
            }
        ]

        result = compose_answer("Is SKU-WIDGET at risk?", trace, mock_client)

        assert result["confidence"] == "high"
        assert "2" in result["answer"]
        assert "stockout" in result["answer"].lower()

    def test_compose_multi_step_answer(self):
        """Test composing answer from multi-step execution."""
        mock_client = Mock()
        mock_response_body = Mock()
        mock_response_body.read.return_value = json.dumps({
            "answer": "SHIP-123 delay affects 8 premium customers; SUP-RELIABLE has 97.0 reliability.",
            "confidence": "high",
            "caveats": "Assumes no more delays"
        }).encode("utf-8")
        mock_client.invoke_model.return_value = {"body": mock_response_body}

        trace = [
            {
                "step": 1,
                "tool": "detect_delay_impact",
                "result": {"delay_days": 5, "downstream_impact_score": 90}
            },
            {
                "step": 2,
                "tool": "supplier_risk_score",
                "result": {"score": 97.0, "risk_category": "low"}
            }
        ]

        result = compose_answer("What's the disruption status?", trace, mock_client)

        assert result["confidence"] == "high"
        assert "97" in result["answer"]

    def test_compose_with_markdown_response(self):
        """Test composition with markdown-wrapped JSON."""
        mock_client = Mock()
        mock_response_body = Mock()
        mock_response_body.read.return_value = '''```json
{
  "answer": "Test answer with markdown",
  "confidence": "medium",
  "caveats": "partial data"
}
```'''.encode("utf-8")
        mock_client.invoke_model.return_value = {"body": mock_response_body}

        trace = [{"step": 1, "tool": "forecast_demand", "result": {}}]
        result = compose_answer("Question?", trace, mock_client)

        assert result["confidence"] == "medium"
        assert "markdown" in result["answer"]

    def test_compose_bedrock_error(self):
        """Test error handling when Bedrock fails."""
        mock_client = Mock()
        mock_client.invoke_model.side_effect = Exception("Bedrock error")

        trace = [{"step": 1, "tool": "forecast_demand", "result": {}}]
        result = compose_answer("Question?", trace, mock_client)

        assert result["confidence"] == "low"
        assert "Unable to synthesize" in result["answer"]

    def test_compose_malformed_response(self):
        """Test error handling for malformed JSON."""
        mock_client = Mock()
        mock_response_body = Mock()
        mock_response_body.read.return_value = b"not valid json"
        mock_client.invoke_model.return_value = {"body": mock_response_body}

        trace = [{"step": 1, "tool": "forecast_demand", "result": {}}]
        result = compose_answer("Question?", trace, mock_client)

        assert result["confidence"] == "low"
        assert "Unable to synthesize" in result["answer"]

    def test_compose_missing_response_body(self):
        """Test error handling when response has no body."""
        mock_client = Mock()
        mock_client.invoke_model.return_value = {"body": None}

        trace = [{"step": 1, "tool": "forecast_demand", "result": {}}]
        result = compose_answer("Question?", trace, mock_client)

        assert result["confidence"] == "low"

    def test_compose_invalid_confidence_value(self):
        """Test handling of invalid confidence value in response."""
        mock_client = Mock()
        mock_response_body = Mock()
        mock_response_body.read.return_value = json.dumps({
            "answer": "Test answer",
            "confidence": "very_high",  # Invalid
            "caveats": "test"
        }).encode("utf-8")
        mock_client.invoke_model.return_value = {"body": mock_response_body}

        trace = [{"step": 1, "tool": "forecast_demand", "result": {}}]
        result = compose_answer("Question?", trace, mock_client)

        assert result["confidence"] == "low"
        assert "Unable to synthesize" in result["answer"]

    def test_compose_valid_confidence_levels(self):
        """Test all valid confidence levels."""
        for conf_level in ["high", "medium", "low"]:
            mock_client = Mock()
            mock_response_body = Mock()
            mock_response_body.read.return_value = json.dumps({
                "answer": f"Answer with {conf_level} confidence",
                "confidence": conf_level,
                "caveats": "test"
            }).encode("utf-8")
            mock_client.invoke_model.return_value = {"body": mock_response_body}

            trace = [{"step": 1, "tool": "forecast_demand", "result": {}}]
            result = compose_answer("Question?", trace, mock_client)

            assert result["confidence"] == conf_level

    def test_compose_empty_trace(self):
        """Test composition with empty execution trace."""
        mock_client = Mock()
        mock_response_body = Mock()
        mock_response_body.read.return_value = json.dumps({
            "answer": "No data available",
            "confidence": "low",
            "caveats": "empty trace"
        }).encode("utf-8")
        mock_client.invoke_model.return_value = {"body": mock_response_body}

        result = compose_answer("Question?", [], mock_client)

        assert result["confidence"] == "low"


class TestRealWorldScenarios:
    """Test realistic composition scenarios."""

    def test_scenario_demand_risk_assessment(self):
        """Scenario: Compose answer for demand + stockout assessment."""
        mock_client = Mock()
        mock_response_body = Mock()
        mock_response_body.read.return_value = json.dumps({
            "answer": "SKU-WIDGET shows stable demand at 166 units/day with 1.8 days of stock remaining at WH-MAIN; immediate restock needed.",
            "confidence": "high",
            "caveats": "Assumes 14-day safety buffer; actual dynamics may vary"
        }).encode("utf-8")
        mock_client.invoke_model.return_value = {"body": mock_response_body}

        trace = [
            {
                "step": 1,
                "tool": "forecast_demand",
                "result": {"sku_id": "SKU-WIDGET", "trend": "stable", "avg_forecasted_demand": 166}
            },
            {
                "step": 2,
                "tool": "predict_stockout",
                "result": {"days_until_stockout": 1.8, "risk_level": "critical", "warehouse_id": "WH-MAIN"}
            }
        ]

        result = compose_answer("Is SKU-WIDGET at risk at WH-MAIN?", trace, mock_client)

        assert result["confidence"] == "high"
        assert "166" in result["answer"]
        assert "1.8" in result["answer"]

    def test_scenario_root_cause_investigation(self):
        """Scenario: Compose answer for multi-step root-cause analysis."""
        mock_client = Mock()
        mock_response_body = Mock()
        mock_response_body.read.return_value = json.dumps({
            "answer": "SHIP-123 (5 days late) impacts 90/100 severity affecting 8 premium customers; supplier SUP-UNRELIABLE scores only 39/100 reliability.",
            "confidence": "high",
            "caveats": "Score based on historical data; current supplier status may have improved"
        }).encode("utf-8")
        mock_client.invoke_model.return_value = {"body": mock_response_body}

        trace = [
            {
                "step": 1,
                "tool": "detect_delay_impact",
                "result": {"shipment_id": "SHIP-123", "delay_days": 5, "downstream_impact_score": 90}
            },
            {
                "step": 2,
                "tool": "supplier_risk_score",
                "result": {"supplier_id": "SUP-UNRELIABLE", "score": 39, "risk_category": "high"}
            }
        ]

        result = compose_answer("What caused our disruption?", trace, mock_client)

        assert result["confidence"] == "high"
        assert "SHIP-123" in result["answer"]
        assert "39" in result["answer"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
