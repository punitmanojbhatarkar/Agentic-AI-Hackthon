"""
Integration test for SupplyChainAgent orchestrator.

Tests the complete workflow: planning → execution → composition.
Includes mock Bedrock client and backend tools.
"""

import sys
import json
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime
import os

# Force UTF-8 output on Windows
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.buffer)

# Add parent directory to path for imports
sys.path.insert(0, '.')


def mock_bedrock_client():
    """Create a mock Bedrock client that returns valid planning and composition responses."""
    client = Mock()

    # Mock planning response: simple single-tool plan
    plan_response = {
        "body": MagicMock(
            read=MagicMock(
                return_value=json.dumps({
                    "steps": [
                        {
                            "step": 1,
                            "tool": "forecast_demand",
                            "parameters": {
                                "sku_id": "SKU-WIDGET-100",
                                "historical_demand": [
                                    {"date": "2024-01-01", "units_sold": 100},
                                    {"date": "2024-01-02", "units_sold": 110},
                                    {"date": "2024-01-03", "units_sold": 105},
                                ]
                            },
                            "depends_on_previous": False,
                            "reasoning": "User asked about SKU-WIDGET inventory risk; need forecast first"
                        }
                    ]
                }).encode("utf-8")
            )
        )
    }

    # Mock composition response: answer with confidence
    compose_response = {
        "body": MagicMock(
            read=MagicMock(
                return_value=json.dumps({
                    "answer": "SKU-WIDGET shows stable demand trending around 105 units daily. Based on current inventory levels, it has approximately 8 days of supply remaining, placing it in the medium-risk category.",
                    "confidence": "high",
                    "caveats": "Forecast based on limited 3-day history; recommend collecting more historical data for confidence improvement."
                }).encode("utf-8")
            )
        )
    }

    # Create a side_effect function to return different responses based on modelId
    def invoke_model_side_effect(*args, **kwargs):
        model_id = kwargs.get("modelId", "")
        if "haiku" in model_id:
            # Check system prompt to determine if it's a planning or composition call
            system = kwargs.get("system", "")
            if "planning" in system.lower():
                return plan_response
            elif "analyst" in system.lower():
                return compose_response
        return plan_response  # Default

    client.invoke_model.side_effect = invoke_model_side_effect
    return client


def test_agent_initialization():
    """Test agent initialization with valid parameters."""
    from agents.orchestrator import SupplyChainAgent

    client = Mock()
    tools = {
        "forecast_demand": Mock(),
        "predict_stockout": Mock(),
    }

    agent = SupplyChainAgent(client, tools)
    assert agent.bedrock_client == client
    assert agent.tool_functions == tools
    assert agent.get_tool_count() == 2
    assert sorted(agent.get_available_tools()) == ["forecast_demand", "predict_stockout"]
    print("[OK] Agent initialization test passed")


def test_agent_initialization_errors():
    """Test agent initialization error handling."""
    from agents.orchestrator import SupplyChainAgent

    # Test None bedrock_client
    try:
        SupplyChainAgent(None, {"tool": Mock()})
        assert False, "Should raise TypeError for None bedrock_client"
    except TypeError:
        print("[OK] None bedrock_client correctly raises TypeError")

    # Test non-dict tool_functions
    try:
        SupplyChainAgent(Mock(), ["tool"])
        assert False, "Should raise TypeError for non-dict tool_functions"
    except TypeError:
        print("[OK] Non-dict tool_functions correctly raises TypeError")

    # Test empty tool_functions
    try:
        SupplyChainAgent(Mock(), {})
        assert False, "Should raise ValueError for empty tool_functions"
    except ValueError:
        print("[OK] Empty tool_functions correctly raises ValueError")


def test_substitute_dependencies():
    """Test FROM_STEP_N placeholder substitution."""
    from agents.orchestrator import SupplyChainAgent

    client = Mock()
    tools = {"forecast_demand": Mock()}
    agent = SupplyChainAgent(client, tools)

    # Test case 1: Simple FROM_STEP_1 substitution
    step_results = {
        1: {"avg_forecasted_demand": 100, "trend": "stable"}
    }
    parameters = {
        "forecast_result": "FROM_STEP_1",
        "sku_id": "SKU-123"
    }

    substituted = agent._substitute_dependencies(parameters, step_results)
    assert substituted["forecast_result"] == {"avg_forecasted_demand": 100, "trend": "stable"}
    assert substituted["sku_id"] == "SKU-123"
    print("[OK] Simple FROM_STEP_N substitution works")

    # Test case 2: Nested key extraction FROM_STEP_1['key']
    parameters = {
        "forecast_result": "FROM_STEP_1['avg_forecasted_demand']",
        "sku_id": "SKU-123"
    }

    substituted = agent._substitute_dependencies(parameters, step_results)
    assert substituted["forecast_result"] == 100
    print("[OK] Nested FROM_STEP_N['key'] substitution works")

    # Test case 3: Missing step reference
    parameters = {
        "forecast_result": "FROM_STEP_99",
        "sku_id": "SKU-123"
    }

    substituted = agent._substitute_dependencies(parameters, step_results)
    assert substituted["forecast_result"] is None
    print("[OK] Missing step reference correctly returns None")


def test_fallback_response():
    """Test fallback response generation."""
    from agents.orchestrator import SupplyChainAgent

    client = Mock()
    tools = {"tool": Mock()}
    agent = SupplyChainAgent(client, tools)

    fallback = agent._fallback_response("Test question?", "Test error reason")

    assert fallback["question"] == "Test question?"
    assert fallback["confidence"] == "low"
    assert fallback["error_summary"] == "Test error reason"
    assert fallback["execution_trace"] == []
    assert "error" in fallback["final_answer"].lower()
    print("[OK] Fallback response generated correctly")


def test_full_workflow():
    """Test complete answer_query workflow with mocked Bedrock."""
    from agents.orchestrator import SupplyChainAgent

    # Create mock tools
    mock_forecast = Mock(return_value={
        "sku_id": "SKU-WIDGET-100",
        "trend": "stable",
        "forecasted_daily_demand": [100, 105, 103, 102, 104, 101, 105],
        "avg_forecasted_demand": 103.0,
        "confidence": 0.85
    })

    bedrock_client = mock_bedrock_client()
    tools = {
        "forecast_demand": mock_forecast,
        "predict_stockout": Mock(),
    }

    agent = SupplyChainAgent(bedrock_client, tools)

    # Answer a query
    response = agent.answer_query("Is SKU-WIDGET at risk of stockout?")

    # Verify response structure
    assert "question" in response
    assert "execution_trace" in response
    assert "final_answer" in response
    assert "confidence" in response
    assert "caveats" in response

    assert response["question"] == "Is SKU-WIDGET at risk of stockout?"
    assert isinstance(response["execution_trace"], list)
    assert response["confidence"] in ["high", "medium", "low"]

    print("[OK] Full workflow test passed")
    print(f"  - Question: {response['question'][:50]}...")
    print(f"  - Confidence: {response['confidence']}")
    print(f"  - Trace steps: {len(response['execution_trace'])}")


def test_create_agent_factory():
    """Test create_agent factory function."""
    try:
        from agents.orchestrator import create_agent

        # Verify function exists and is callable
        assert callable(create_agent)
        print("[OK] create_agent factory function exists and is callable")

        # Note: Full test would require actual backend modules,
        # but we verify the function signature and docstring
        assert create_agent.__doc__ is not None
        assert "SupplyChainAgent" in create_agent.__doc__
        print("[OK] create_agent has complete docstring")

    except ImportError as e:
        print(f"⚠ create_agent import test skipped: {e}")


def run_all_tests():
    """Run all tests."""
    print("\n" + "=" * 70)
    print("SupplyChainAgent Orchestrator Integration Tests")
    print("=" * 70 + "\n")

    try:
        test_agent_initialization()
        test_agent_initialization_errors()
        test_substitute_dependencies()
        test_fallback_response()
        test_full_workflow()
        test_create_agent_factory()

        print("\n" + "=" * 70)
        print("ALL TESTS PASSED")
        print("=" * 70 + "\n")

    except Exception as e:
        print(f"\nTEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    run_all_tests()
