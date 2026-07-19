"""
Tests for the planning agent.

Verifies:
1. Bedrock API integration
2. JSON parsing (with and without markdown fences)
3. Tool name validation against registry
4. Step structure validation
5. Dependency chain validation
6. Error handling and robustness
7. Support for 1-4 step sequences
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from planner import (
    plan_investigation,
    _parse_json_response,
    _validate_step_dependencies,
)


class TestParseJsonResponse:
    """Test JSON parsing with various formats."""

    def test_parse_plain_json(self):
        """Test parsing plain JSON without fences."""
        json_str = '{"steps": [{"step": 1, "tool": "forecast_demand", "parameters": {}, "depends_on_previous": false, "reasoning": "test"}]}'
        result = _parse_json_response(json_str)
        assert result is not None
        assert "steps" in result
        assert len(result["steps"]) == 1

    def test_parse_json_with_markdown_fences(self):
        """Test parsing JSON wrapped in ```json ... ``` fences."""
        json_str = """```json
{"steps": [{"step": 1, "tool": "forecast_demand", "parameters": {}, "depends_on_previous": false, "reasoning": "test"}]}
```"""
        result = _parse_json_response(json_str)
        assert result is not None
        assert "steps" in result

    def test_parse_json_with_triple_backticks(self):
        """Test parsing JSON wrapped in ``` ... ``` fences."""
        json_str = """```
{"steps": [{"step": 1, "tool": "forecast_demand", "parameters": {}, "depends_on_previous": false, "reasoning": "test"}]}
```"""
        result = _parse_json_response(json_str)
        assert result is not None
        assert "steps" in result

    def test_parse_invalid_json(self):
        """Test parsing invalid JSON returns None."""
        result = _parse_json_response("not valid json")
        assert result is None

    def test_parse_empty_string(self):
        """Test parsing empty string returns None."""
        result = _parse_json_response("")
        assert result is None

    def test_parse_non_dict_json(self):
        """Test parsing JSON that's not a dict returns None."""
        result = _parse_json_response("[1, 2, 3]")  # Array, not dict
        assert result is None

    def test_parse_with_whitespace(self):
        """Test parsing JSON with surrounding whitespace."""
        json_str = """
        
        {"steps": [{"step": 1, "tool": "forecast_demand", "parameters": {}, "depends_on_previous": false, "reasoning": "test"}]}
        
        """
        result = _parse_json_response(json_str)
        assert result is not None


class TestValidateStepDependencies:
    """Test step dependency validation."""

    def test_valid_single_step(self):
        """Test valid single-step plan."""
        steps = [
            {
                "step": 1,
                "tool": "forecast_demand",
                "parameters": {},
                "depends_on_previous": False,
                "reasoning": "Get demand forecast"
            }
        ]
        assert _validate_step_dependencies(steps) is True

    def test_valid_two_step_chain(self):
        """Test valid two-step dependent chain."""
        steps = [
            {
                "step": 1,
                "tool": "forecast_demand",
                "parameters": {"sku_id": "SKU-001", "historical_demand": "FROM_CONTEXT"},
                "depends_on_previous": False,
                "reasoning": "Get demand forecast"
            },
            {
                "step": 2,
                "tool": "predict_stockout",
                "parameters": {"sku_id": "SKU-001", "forecast_result": "FROM_STEP_1"},
                "depends_on_previous": True,
                "reasoning": "Check stockout risk"
            }
        ]
        assert _validate_step_dependencies(steps) is True

    def test_valid_three_step_chain(self):
        """Test valid three-step chain."""
        steps = [
            {
                "step": 1,
                "tool": "forecast_demand",
                "parameters": {},
                "depends_on_previous": False,
                "reasoning": "Forecast"
            },
            {
                "step": 2,
                "tool": "predict_stockout",
                "parameters": {"forecast_result": "FROM_STEP_1"},
                "depends_on_previous": True,
                "reasoning": "Check stockout"
            },
            {
                "step": 3,
                "tool": "recommend_allocation",
                "parameters": {"sku_id": "FROM_STEP_2"},
                "depends_on_previous": True,
                "reasoning": "Allocate"
            }
        ]
        assert _validate_step_dependencies(steps) is True

    def test_invalid_step_1_depends_on_previous(self):
        """Test that step 1 cannot depend on previous."""
        steps = [
            {
                "step": 1,
                "tool": "forecast_demand",
                "parameters": {},
                "depends_on_previous": True,  # Invalid
                "reasoning": "test"
            }
        ]
        assert _validate_step_dependencies(steps) is False

    def test_invalid_forward_reference(self):
        """Test that steps cannot reference future steps."""
        steps = [
            {
                "step": 1,
                "tool": "forecast_demand",
                "parameters": {"data": "FROM_STEP_2"},  # Forward reference
                "depends_on_previous": False,
                "reasoning": "test"
            },
            {
                "step": 2,
                "tool": "predict_stockout",
                "parameters": {},
                "depends_on_previous": False,
                "reasoning": "test"
            }
        ]
        assert _validate_step_dependencies(steps) is False

    def test_invalid_zero_step_reference(self):
        """Test that steps cannot reference step 0."""
        steps = [
            {
                "step": 2,
                "tool": "forecast_demand",
                "parameters": {"data": "FROM_STEP_0"},  # Invalid step 0
                "depends_on_previous": False,
                "reasoning": "test"
            }
        ]
        assert _validate_step_dependencies(steps) is False


class TestPlanInvestigation:
    """Test planning agent integration."""

    @patch('tool_registry.validate_tool_exists')
    def test_plan_single_step_question(self, mock_validate):
        """Test planning for simple single-step question."""
        mock_validate.return_value = True

        # Mock Bedrock response
        mock_client = Mock()
        mock_response_body = Mock()
        mock_response_body.read.return_value = json.dumps({
            "steps": [
                {
                    "step": 1,
                    "tool": "forecast_demand",
                    "parameters": {"sku_id": "SKU-123", "historical_demand": []},
                    "depends_on_previous": False,
                    "reasoning": "Get demand forecast for inventory assessment"
                }
            ]
        }).encode("utf-8")
        mock_client.invoke_model.return_value = {"body": mock_response_body}

        result = plan_investigation(
            "What's the demand forecast for SKU-123?",
            "Available tools...",
            mock_client
        )

        assert len(result) == 1
        assert result[0]["tool"] == "forecast_demand"
        assert result[0]["step"] == 1

    @patch('tool_registry.validate_tool_exists')
    def test_plan_multi_step_investigation(self, mock_validate):
        """Test planning for complex root-cause question."""
        mock_validate.return_value = True

        mock_client = Mock()
        mock_response_body = Mock()
        mock_response_body.read.return_value = json.dumps({
            "steps": [
                {
                    "step": 1,
                    "tool": "detect_delay_impact",
                    "parameters": {"shipment_id": "SHIP-123"},
                    "depends_on_previous": False,
                    "reasoning": "Assess delay impact"
                },
                {
                    "step": 2,
                    "tool": "supplier_risk_score",
                    "parameters": {"supplier_id": "FROM_STEP_1"},
                    "depends_on_previous": True,
                    "reasoning": "Evaluate supplier reliability"
                }
            ]
        }).encode("utf-8")
        mock_client.invoke_model.return_value = {"body": mock_response_body}

        result = plan_investigation(
            "What's causing today's biggest supply disruption?",
            "Available tools...",
            mock_client
        )

        assert len(result) == 2
        assert result[0]["tool"] == "detect_delay_impact"
        assert result[1]["tool"] == "supplier_risk_score"
        assert result[1]["depends_on_previous"] is True

    @patch('tool_registry.validate_tool_exists')
    def test_plan_invalid_tool_name(self, mock_validate):
        """Test that invalid tool names are rejected."""
        mock_validate.return_value = False  # Tool doesn't exist

        mock_client = Mock()
        mock_response_body = Mock()
        mock_response_body.read.return_value = json.dumps({
            "steps": [
                {
                    "step": 1,
                    "tool": "nonexistent_tool",
                    "parameters": {},
                    "depends_on_previous": False,
                    "reasoning": "test"
                }
            ]
        }).encode("utf-8")
        mock_client.invoke_model.return_value = {"body": mock_response_body}

        result = plan_investigation(
            "Test question",
            "Available tools...",
            mock_client
        )

        assert result == []

    def test_plan_bedrock_error(self):
        """Test error handling when Bedrock call fails."""
        mock_client = Mock()
        mock_client.invoke_model.side_effect = Exception("Bedrock API error")

        result = plan_investigation(
            "Test question",
            "Available tools...",
            mock_client
        )

        assert result == []

    def test_plan_malformed_response(self):
        """Test error handling for malformed JSON response."""
        mock_client = Mock()
        mock_response_body = Mock()
        mock_response_body.read.return_value = "not valid json".encode("utf-8")
        mock_client.invoke_model.return_value = {"body": mock_response_body}

        result = plan_investigation(
            "Test question",
            "Available tools...",
            mock_client
        )

        assert result == []

    def test_plan_no_response_body(self):
        """Test error handling when response has no body."""
        mock_client = Mock()
        mock_client.invoke_model.return_value = {"body": None}

        result = plan_investigation(
            "Test question",
            "Available tools...",
            mock_client
        )

        assert result == []

    @patch('tool_registry.validate_tool_exists')
    def test_plan_missing_step_fields(self, mock_validate):
        """Test that steps with missing fields are rejected."""
        mock_validate.return_value = True

        mock_client = Mock()
        mock_response_body = Mock()
        mock_response_body.read.return_value = json.dumps({
            "steps": [
                {
                    "step": 1,
                    "tool": "forecast_demand",
                    # Missing "parameters", "depends_on_previous", "reasoning"
                }
            ]
        }).encode("utf-8")
        mock_client.invoke_model.return_value = {"body": mock_response_body}

        result = plan_investigation(
            "Test question",
            "Available tools...",
            mock_client
        )

        assert result == []

    @patch('tool_registry.validate_tool_exists')
    def test_plan_truncates_at_4_steps(self, mock_validate):
        """Test that plans with >4 steps are truncated."""
        mock_validate.return_value = True

        mock_client = Mock()
        steps_list = [
            {
                "step": i,
                "tool": "forecast_demand",
                "parameters": {},
                "depends_on_previous": False,
                "reasoning": f"Step {i}"
            }
            for i in range(1, 6)  # 5 steps
        ]
        mock_response_body = Mock()
        mock_response_body.read.return_value = json.dumps({
            "steps": steps_list
        }).encode("utf-8")
        mock_client.invoke_model.return_value = {"body": mock_response_body}

        result = plan_investigation(
            "Test question",
            "Available tools...",
            mock_client
        )

        assert len(result) == 4  # Truncated to 4

    @patch('tool_registry.validate_tool_exists')
    def test_plan_empty_steps_list(self, mock_validate):
        """Test handling of empty steps list."""
        mock_validate.return_value = True

        mock_client = Mock()
        mock_response_body = Mock()
        mock_response_body.read.return_value = json.dumps({
            "steps": []  # Empty
        }).encode("utf-8")
        mock_client.invoke_model.return_value = {"body": mock_response_body}

        result = plan_investigation(
            "Test question",
            "Available tools...",
            mock_client
        )

        assert result == []


class TestPlanningExamples:
    """Test realistic planning scenarios."""

    @patch('tool_registry.validate_tool_exists')
    def test_scenario_demand_assessment(self, mock_validate):
        """Scenario: Assess demand and inventory risk."""
        mock_validate.return_value = True

        mock_client = Mock()
        mock_response_body = Mock()
        mock_response_body.read.return_value = json.dumps({
            "steps": [
                {
                    "step": 1,
                    "tool": "forecast_demand",
                    "parameters": {"sku_id": "SKU-WIDGET", "historical_demand": []},
                    "depends_on_previous": False,
                    "reasoning": "Generate demand forecast"
                },
                {
                    "step": 2,
                    "tool": "predict_stockout",
                    "parameters": {
                        "sku_id": "SKU-WIDGET",
                        "warehouse_id": "WH-MAIN",
                        "current_stock": 500,
                        "forecast_result": "FROM_STEP_1"
                    },
                    "depends_on_previous": True,
                    "reasoning": "Check stockout risk"
                }
            ]
        }).encode("utf-8")
        mock_client.invoke_model.return_value = {"body": mock_response_body}

        result = plan_investigation(
            "Is SKU-WIDGET at WH-MAIN running low on stock?",
            "Available tools...",
            mock_client
        )

        assert len(result) == 2
        assert result[0]["tool"] == "forecast_demand"
        assert result[1]["tool"] == "predict_stockout"

    @patch('tool_registry.validate_tool_exists')
    def test_scenario_root_cause_investigation(self, mock_validate):
        """Scenario: Full root-cause analysis of disruption."""
        mock_validate.return_value = True

        mock_client = Mock()
        mock_response_body = Mock()
        mock_response_body.read.return_value = json.dumps({
            "steps": [
                {
                    "step": 1,
                    "tool": "detect_delay_impact",
                    "parameters": {"shipment_id": "SHIP-123"},
                    "depends_on_previous": False,
                    "reasoning": "Assess shipment delay impact"
                },
                {
                    "step": 2,
                    "tool": "supplier_risk_score",
                    "parameters": {"supplier_id": "FROM_STEP_1"},
                    "depends_on_previous": True,
                    "reasoning": "Evaluate source reliability"
                },
                {
                    "step": 3,
                    "tool": "recommend_allocation",
                    "parameters": {"affected_orders": "FROM_STEP_1"},
                    "depends_on_previous": True,
                    "reasoning": "Plan fulfillment workaround"
                }
            ]
        }).encode("utf-8")
        mock_client.invoke_model.return_value = {"body": mock_response_body}

        result = plan_investigation(
            "What's the root cause of today's disruption and how should we respond?",
            "Available tools...",
            mock_client
        )

        assert len(result) == 3
        assert result[0]["tool"] == "detect_delay_impact"
        assert result[1]["tool"] == "supplier_risk_score"
        assert result[2]["tool"] == "recommend_allocation"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
