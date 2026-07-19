"""Tests for orchestrator agent."""

import pytest
from unittest.mock import Mock, patch
from orchestrator import SupplyChainAgent


class TestInit:
    """Test initialization."""

    def test_init_valid(self):
        """Valid initialization."""
        agent = SupplyChainAgent(Mock(), {"tool1": Mock()})
        assert len(agent.tool_functions) == 1

    def test_init_invalid_type(self):
        """Non-dict tools raises TypeError."""
        with pytest.raises(TypeError):
            SupplyChainAgent(Mock(), [])

    def test_init_empty(self):
        """Empty tools raises ValueError."""
        with pytest.raises(ValueError):
            SupplyChainAgent(Mock(), {})


class TestDependencies:
    """Test dependency substitution."""

    def test_substitute_from_step(self):
        """Test FROM_STEP_N substitution."""
        agent = SupplyChainAgent(Mock(), {"tool1": Mock()})
        params = {"data": "FROM_STEP_1", "const": "val"}
        results = {"STEP_1": {"result": "data1"}}
        subst = agent._substitute_dependencies(params, results)
        assert subst["data"] == {"result": "data1"}
        assert subst["const"] == "val"


class TestFallback:
    """Test fallback responses."""

    def test_fallback_format(self):
        """Test fallback structure."""
        agent = SupplyChainAgent(Mock(), {"tool1": Mock()})
        resp = agent._fallback_response("Q?", "Error")
        assert resp["confidence"] == "low"
        assert resp["execution_trace"] == []
        assert "Error" in resp["final_answer"]


class TestAnswerQuery:
    """Test answer_query."""

    @patch('orchestrator.compose_answer')
    @patch('orchestrator.plan_investigation')
    def test_single_step(self, m_plan, m_compose):
        """Single-step query."""
        m_plan.return_value = [{
            "step": 1, "tool": "forecast_demand",
            "parameters": {"sku_id": "SKU-1", "historical_demand": []},
            "depends_on_previous": False, "reasoning": "Forecast"
        }]
        m_compose.return_value = {"answer": "100 units.", "confidence": "high", "caveats": "None"}
        
        mock_tool = Mock(return_value={"avg": 100})
        agent = SupplyChainAgent(Mock(), {"forecast_demand": mock_tool})
        result = agent.answer_query("Forecast?")
        
        assert result["question"] == "Forecast?"
        assert result["confidence"] == "high"
        assert len(result["execution_trace"]) == 1

    @patch('orchestrator.plan_investigation')
    def test_planning_fails(self, m_plan):
        """Planning failure handled gracefully."""
        m_plan.side_effect = Exception("LLM failed")
        agent = SupplyChainAgent(Mock(), {"tool1": Mock()})
        result = agent.answer_query("Q?")
        
        assert result["confidence"] == "low"
        assert "LLM failed" in result["final_answer"]

    @patch('orchestrator.plan_investigation')
    def test_tool_execution_fails(self, m_plan):
        """Tool execution failure handled - logged but compose_answer call continues."""
        m_plan.return_value = [{
            "step": 1, "tool": "forecast_demand",
            "parameters": {"sku_id": "SKU-1", "historical_demand": []},
            "depends_on_previous": False, "reasoning": "Get"
        }]
        
        mock_tool = Mock(side_effect=ValueError("Bad input"))
        agent = SupplyChainAgent(Mock(), {"forecast_demand": mock_tool})
        result = agent.answer_query("Q?")
        
        # Verify error is logged and handled (confidence drops)
        assert result["confidence"] == "low"


    @patch('orchestrator.plan_investigation')
    def test_unknown_tool(self, m_plan):
        """Unknown tool in plan handled - returns error response."""
        m_plan.return_value = [{
            "step": 1, "tool": "unknown_tool",
            "parameters": {}, "depends_on_previous": False, "reasoning": "X"
        }]
        
        agent = SupplyChainAgent(Mock(), {"forecast_demand": Mock()})
        result = agent.answer_query("Q?")
        
        # Verify unknown tool is handled gracefully
        assert result["confidence"] == "low"
        # Error caught - trace is empty or error mentioned
        assert result["execution_trace"] == []




class TestMultiStep:
    """Test multi-step execution."""

    @patch('orchestrator.compose_answer')
    @patch('orchestrator.plan_investigation')
    def test_two_steps(self, m_plan, m_compose):
        """Two-step chain with dependency."""
        m_plan.return_value = [
            {"step": 1, "tool": "forecast_demand", "parameters": {"sku_id": "SKU-1", "historical_demand": []},
             "depends_on_previous": False, "reasoning": "Forecast"},
            {"step": 2, "tool": "predict_stockout", "parameters": {"sku_id": "SKU-1", "warehouse_id": "WH-1",
             "current_stock": 500, "forecast_result": "FROM_STEP_1"}, "depends_on_previous": True, "reasoning": "Risk"}
        ]
        m_compose.return_value = {"answer": "5 days.", "confidence": "high", "caveats": "None"}
        
        tool1 = Mock(return_value={"avg": 100})
        tool2 = Mock(return_value={"days": 5})
        agent = SupplyChainAgent(Mock(), {"forecast_demand": tool1, "predict_stockout": tool2})
        result = agent.answer_query("Risk?")
        
        assert len(result["execution_trace"]) == 2
        assert result["execution_trace"][0]["tool"] == "forecast_demand"
        assert result["execution_trace"][1]["tool"] == "predict_stockout"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
