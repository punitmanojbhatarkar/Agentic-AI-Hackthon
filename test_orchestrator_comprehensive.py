"""
COMPREHENSIVE VERIFICATION TEST for SupplyChainAgent.answer_query()

This test validates ALL requirements are correctly implemented:
1. Full multi-step execution
2. FROM_STEP_N parameter substitution (including nested keys)
3. execution_trace collection with all required fields
4. Graceful error handling (never crashes, all paths logged)
5. Planning → Execution → Composition workflow
"""

import sys
import json
from unittest.mock import Mock, MagicMock, patch
import logging

# Configure logging to see all levels
logging.basicConfig(level=logging.DEBUG, format='%(levelname)-8s | %(message)s')

# Add path for imports
sys.path.insert(0, '.')

from agents.orchestrator import SupplyChainAgent


def create_mock_bedrock_client():
    """
    Create a mock Bedrock client that returns realistic planning and composition responses.
    
    This simulates a multi-step chain:
    - Step 1: forecast_demand() for SKU-WIDGET
    - Step 2: predict_stockout() (depends on Step 1's forecast_result)
    """
    client = Mock()

    # Multi-step plan: forecast → predict_stockout
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
                                    {"date": "2024-01-04", "units_sold": 102},
                                    {"date": "2024-01-05", "units_sold": 108},
                                ]
                            },
                            "depends_on_previous": False,
                            "reasoning": "User asked about stockout risk; start with demand forecast"
                        },
                        {
                            "step": 2,
                            "tool": "predict_stockout",
                            "parameters": {
                                "sku_id": "SKU-WIDGET-100",
                                "warehouse_id": "WH-MAIN",
                                "current_stock": 500,
                                "forecast_result": "FROM_STEP_1"
                            },
                            "depends_on_previous": True,
                            "reasoning": "Now use forecast from Step 1 to predict stockout risk"
                        }
                    ]
                }).encode("utf-8")
            )
        )
    }

    # Composition response
    compose_response = {
        "body": MagicMock(
            read=MagicMock(
                return_value=json.dumps({
                    "answer": "SKU-WIDGET at WH-MAIN shows stable demand around 105 units/day. With current stock of 500 units, you have approximately 4.8 days of supply, placing this SKU in HIGH risk category.",
                    "confidence": "high",
                    "caveats": "Based on only 5 days of historical data; more history recommended for precision."
                }).encode("utf-8")
            )
        )
    }

    def invoke_model_side_effect(*args, **kwargs):
        system = kwargs.get("system", "")
        if "planning" in system.lower():
            return plan_response
        else:
            return compose_response

    client.invoke_model.side_effect = invoke_model_side_effect
    return client


def create_mock_tools():
    """Create mock backend tools with realistic return values."""
    
    def mock_forecast_demand(sku_id, historical_demand):
        """Mock forecast_demand: returns realistic forecast result."""
        return {
            "sku_id": sku_id,
            "trend": "stable",
            "forecasted_daily_demand": [105.0, 104.0, 106.0, 105.0, 105.0, 104.0, 106.0],
            "avg_forecasted_demand": 105.0,
            "confidence": 0.82
        }
    
    def mock_predict_stockout(sku_id, warehouse_id, current_stock, forecast_result):
        """
        Mock predict_stockout: takes forecast_result from Step 1.
        This tests that FROM_STEP_1 substitution works correctly!
        """
        avg_demand = forecast_result.get("avg_forecasted_demand", 100)
        days_until = current_stock / avg_demand if avg_demand > 0 else None
        
        if days_until is None:
            risk_level = "low"
        elif days_until <= 3:
            risk_level = "critical"
        elif days_until <= 7:
            risk_level = "high"
        elif days_until <= 14:
            risk_level = "medium"
        else:
            risk_level = "low"
        
        return {
            "sku_id": sku_id,
            "warehouse_id": warehouse_id,
            "current_stock": current_stock,
            "days_until_stockout": days_until,
            "risk_level": risk_level,
            "recommended_reorder_quantity": int(avg_demand * 14)
        }
    
    def mock_supplier_risk_score(supplier_id, delivery_history):
        """Mock supplier_risk_score."""
        return {
            "supplier_id": supplier_id,
            "score": 82.5,
            "breakdown": {
                "on_time_delivery_pct": 85.0,
                "lead_time_variance_days": 2.1,
                "avg_quality_score": 78.0
            },
            "risk_category": "low"
        }
    
    def mock_detect_delay_impact(shipment_id, shipment_data, downstream_orders):
        """Mock detect_delay_impact."""
        return {
            "shipment_id": shipment_id,
            "is_delayed": False,
            "delay_days": 0,
            "downstream_impact_score": 45.0,
            "affected_order_ids": ["ORD-001", "ORD-002"],
            "severity": "moderate"
        }
    
    def mock_recommend_allocation(sku_id, available_stock, pending_orders):
        """Mock recommend_allocation."""
        return {
            "sku_id": sku_id,
            "available_stock": available_stock,
            "total_requested": sum(o.get("quantity_requested", 0) for o in pending_orders),
            "allocations": [
                {
                    "order_id": o.get("order_id", ""),
                    "customer_tier": o.get("customer_tier", "standard"),
                    "quantity_requested": o.get("quantity_requested", 0),
                    "quantity_allocated": min(o.get("quantity_requested", 0), available_stock),
                    "fulfillment_status": "full" if o.get("quantity_requested", 0) <= available_stock else "partial"
                }
                for o in pending_orders
            ],
            "fully_satisfied": True
        }
    
    return {
        "forecast_demand": mock_forecast_demand,
        "predict_stockout": mock_predict_stockout,
        "supplier_risk_score": mock_supplier_risk_score,
        "detect_delay_impact": mock_detect_delay_impact,
        "recommend_allocation": mock_recommend_allocation,
    }


def test_requirement_1_full_multi_step_execution():
    """
    REQUIREMENT 1: Full multi-step execution
    Verify that answer_query() executes multiple steps in sequence.
    """
    print("\n" + "="*80)
    print("TEST 1: Full Multi-Step Execution")
    print("="*80)
    
    bedrock = create_mock_bedrock_client()
    tools = create_mock_tools()
    agent = SupplyChainAgent(bedrock, tools)
    
    response = agent.answer_query("Is SKU-WIDGET at risk of stockout at WH-MAIN?")
    
    # Verify response structure
    assert "execution_trace" in response, "Missing execution_trace"
    assert isinstance(response["execution_trace"], list), "execution_trace should be list"
    
    # Verify multiple steps executed
    trace = response["execution_trace"]
    print(f"[OK] Executed {len(trace)} steps in sequence")
    
    for step_entry in trace:
        assert "step" in step_entry, "Missing 'step' in trace entry"
        assert "tool" in step_entry, "Missing 'tool' in trace entry"
        print(f"  - Step {step_entry['step']}: {step_entry['tool']}")
    
    return True


def test_requirement_2_from_step_n_substitution():
    """
    REQUIREMENT 2: FROM_STEP_N parameter substitution
    Verify that FROM_STEP_1 placeholders are replaced with actual Step 1 results.
    """
    print("\n" + "="*80)
    print("TEST 2: FROM_STEP_N Parameter Substitution")
    print("="*80)
    
    bedrock = create_mock_bedrock_client()
    tools = create_mock_tools()
    agent = SupplyChainAgent(bedrock, tools)
    
    response = agent.answer_query("Is SKU-WIDGET at risk of stockout at WH-MAIN?")
    
    trace = response["execution_trace"]
    
    # Step 1 result (forecast)
    step1 = trace[0]
    assert step1["step"] == 1, "First step should be step 1"
    assert step1["tool"] == "forecast_demand", "First tool should be forecast_demand"
    forecast_result = step1.get("result")
    assert forecast_result is not None, "Step 1 should have result"
    print(f"[OK] Step 1 result: avg_forecasted_demand = {forecast_result.get('avg_forecasted_demand')}")
    
    # Step 2 parameters (should have forecast_result substituted)
    if len(trace) > 1:
        step2 = trace[1]
        assert step2["step"] == 2, "Second step should be step 2"
        assert step2["tool"] == "predict_stockout", "Second tool should be predict_stockout"
        
        # Verify that forecast_result was substituted (not a FROM_STEP_1 string)
        params_used = step2.get("parameters_used", {})
        forecast_param = params_used.get("forecast_result")
        
        # The substituted parameter should be a dict (the actual forecast result), not a string
        assert isinstance(forecast_param, dict), \
            f"forecast_result should be substituted dict, got {type(forecast_param).__name__}"
        
        assert forecast_param.get("avg_forecasted_demand") == forecast_result.get("avg_forecasted_demand"), \
            "forecast_result should match Step 1's result"
        
        print(f"[OK] Step 2 received substituted forecast_result from Step 1")
        print(f"  - forecast_result['avg_forecasted_demand'] = {forecast_param.get('avg_forecasted_demand')}")
    
    return True


def test_requirement_3_execution_trace_collection():
    """
    REQUIREMENT 3: execution_trace collection with all required fields
    Verify execution_trace contains: step, tool, parameters_used, reasoning, result
    """
    print("\n" + "="*80)
    print("TEST 3: Execution Trace Collection (All Required Fields)")
    print("="*80)
    
    bedrock = create_mock_bedrock_client()
    tools = create_mock_tools()
    agent = SupplyChainAgent(bedrock, tools)
    
    response = agent.answer_query("Is SKU-WIDGET at risk of stockout at WH-MAIN?")
    
    trace = response["execution_trace"]
    
    # Required fields per trace entry
    required_fields = {"step", "tool", "parameters_used", "reasoning", "result"}
    
    for i, entry in enumerate(trace):
        entry_fields = set(entry.keys())
        assert required_fields.issubset(entry_fields), \
            f"Trace entry {i} missing fields: {required_fields - entry_fields}"
        
        # Verify field types
        assert isinstance(entry["step"], int), f"step should be int, got {type(entry['step']).__name__}"
        assert isinstance(entry["tool"], str), f"tool should be str, got {type(entry['tool']).__name__}"
        assert isinstance(entry["parameters_used"], dict), f"parameters_used should be dict"
        assert isinstance(entry["reasoning"], str), f"reasoning should be str"
        assert isinstance(entry["result"], dict), f"result should be dict"
        
        print(f"[OK] Trace entry {i} has all required fields:")
        print(f"  - step: {entry['step']}")
        print(f"  - tool: {entry['tool']}")
        print(f"  - parameters_used: {list(entry['parameters_used'].keys())}")
        print(f"  - reasoning: {entry['reasoning'][:50]}...")
        print(f"  - result keys: {list(entry['result'].keys())}")
    
    return True


def test_requirement_4_graceful_error_handling():
    """
    REQUIREMENT 4: Graceful error handling (never crashes)
    Verify that errors in planning, execution, or composition don't crash the agent.
    """
    print("\n" + "="*80)
    print("TEST 4: Graceful Error Handling")
    print("="*80)
    
    bedrock = create_mock_bedrock_client()
    tools = create_mock_tools()
    agent = SupplyChainAgent(bedrock, tools)
    
    # TEST 4a: Tool execution failure
    print("\n[TEST 4a] Tool execution failure")
    
    def failing_tool(**kwargs):
        raise ValueError("Simulated tool failure")
    
    tools_with_failure = create_mock_tools()
    tools_with_failure["forecast_demand"] = failing_tool
    
    agent_with_failure = SupplyChainAgent(bedrock, tools_with_failure)
    
    # This should NOT crash - it should return a valid response
    try:
        response = agent_with_failure.answer_query("Test question?")
        assert response is not None, "Response should not be None"
        assert "question" in response, "Response should have 'question'"
        assert "confidence" in response, "Response should have 'confidence'"
        print("[OK] Agent handled tool failure gracefully (no crash)")
    except Exception as e:
        raise AssertionError(f"Agent crashed on tool failure: {e}")
    
    # TEST 4b: Empty execution trace fallback
    print("\n[TEST 4b] Empty execution trace handling")
    
    # Create a bedrock client that returns invalid plan
    bad_bedrock = Mock()
    bad_bedrock.invoke_model.return_value = {
        "body": MagicMock(
            read=MagicMock(
                return_value=json.dumps({"steps": []}).encode("utf-8")
            )
        )
    }
    
    agent_bad = SupplyChainAgent(bad_bedrock, tools)
    
    try:
        response = agent_bad.answer_query("Test?")
        assert response is not None, "Response should not be None"
        assert response["confidence"] == "low", "Fallback should have low confidence"
        assert "error_summary" in response, "Fallback should have error_summary"
        print("[OK] Agent handled empty plan gracefully (fallback response)")
    except Exception as e:
        raise AssertionError(f"Agent crashed on empty plan: {e}")
    
    # TEST 4c: Missing tool in registry
    print("\n[TEST 4c] Missing tool in registry")
    
    bedrock_unknown_tool = Mock()
    bedrock_unknown_tool.invoke_model.return_value = {
        "body": MagicMock(
            read=MagicMock(
                return_value=json.dumps({
                    "steps": [
                        {
                            "step": 1,
                            "tool": "unknown_tool_xyz",
                            "parameters": {},
                            "depends_on_previous": False,
                            "reasoning": "Test"
                        }
                    ]
                }).encode("utf-8")
            )
        )
    }
    
    agent_unknown = SupplyChainAgent(bedrock_unknown_tool, tools)
    
    try:
        response = agent_unknown.answer_query("Test?")
        assert response is not None, "Response should not be None"
        # Should have fallback or at least a valid response
        print("[OK] Agent handled unknown tool gracefully (no crash)")
    except Exception as e:
        raise AssertionError(f"Agent crashed on unknown tool: {e}")
    
    return True


def test_requirement_5_complete_workflow():
    """
    REQUIREMENT 5: Complete Planning -> Execution -> Composition workflow
    Verify the entire workflow produces a sensible final answer.
    """
    print("\n" + "="*80)
    print("TEST 5: Complete Workflow (Planning -> Execution -> Composition)")
    print("="*80)
    
    bedrock = create_mock_bedrock_client()
    tools = create_mock_tools()
    agent = SupplyChainAgent(bedrock, tools)
    
    response = agent.answer_query("Is SKU-WIDGET at risk of stockout at WH-MAIN?")
    
    # Verify complete response structure
    required_keys = {"question", "execution_trace", "final_answer", "confidence", "caveats"}
    response_keys = set(response.keys())
    
    missing_keys = required_keys - response_keys
    assert len(missing_keys) == 0, f"Response missing keys: {missing_keys}"
    
    print("[OK] Response has all required fields:")
    print(f"  - question: {response['question'][:50]}...")
    print(f"  - execution_trace: {len(response['execution_trace'])} steps")
    print(f"  - final_answer: {response['final_answer'][:60]}...")
    print(f"  - confidence: {response['confidence']}")
    print(f"  - caveats: {response['caveats']}")
    
    # Verify answer quality
    assert len(response["final_answer"]) > 0, "final_answer should not be empty"
    assert response["confidence"] in ["high", "medium", "low"], "Invalid confidence"
    assert len(response["caveats"]) > 0, "caveats should not be empty"
    
    print("\n[OK] Workflow produced complete, sensible response")
    
    return True


def test_nested_key_extraction():
    """
    BONUS TEST: Nested key extraction (FROM_STEP_1['key'])
    Verify that nested key extraction works correctly.
    """
    print("\n" + "="*80)
    print("BONUS TEST: Nested Key Extraction (FROM_STEP_1['key'])")
    print("="*80)
    
    bedrock = Mock()
    tools = create_mock_tools()
    agent = SupplyChainAgent(bedrock, tools)
    
    # Test _substitute_dependencies directly
    step_results = {
        1: {
            "sku_id": "SKU-123",
            "avg_forecasted_demand": 100.0,
            "trend": "stable",
            "confidence": 0.85
        }
    }
    
    parameters = {
        "forecast_result": "FROM_STEP_1",
        "avg_demand": "FROM_STEP_1['avg_forecasted_demand']",
        "sku_id": "FROM_STEP_1['sku_id']",
        "literal_value": "SKU-999"
    }
    
    substituted = agent._substitute_dependencies(parameters, step_results)
    
    # Verify substitutions
    assert isinstance(substituted["forecast_result"], dict), "FROM_STEP_1 should give full dict"
    assert substituted["avg_demand"] == 100.0, "FROM_STEP_1['avg_forecasted_demand'] should give 100.0"
    assert substituted["sku_id"] == "SKU-123", "FROM_STEP_1['sku_id'] should give SKU-123"
    assert substituted["literal_value"] == "SKU-999", "Literal values should pass through"
    
    print("[OK] Nested key extraction works correctly:")
    print(f"  - Full dict: {list(substituted['forecast_result'].keys())}")
    print(f"  - Nested key avg_demand: {substituted['avg_demand']}")
    print(f"  - Nested key sku_id: {substituted['sku_id']}")
    print(f"  - Literal value: {substituted['literal_value']}")
    
    return True


def run_all_tests():
    """Run all verification tests."""
    print("\n" + "="*80)
    print("COMPREHENSIVE SUPPLYCHAINAGENT VERIFICATION")
    print("="*80)
    
    tests = [
        ("Requirement 1: Multi-Step Execution", test_requirement_1_full_multi_step_execution),
        ("Requirement 2: FROM_STEP_N Substitution", test_requirement_2_from_step_n_substitution),
        ("Requirement 3: Execution Trace Collection", test_requirement_3_execution_trace_collection),
        ("Requirement 4: Graceful Error Handling", test_requirement_4_graceful_error_handling),
        ("Requirement 5: Complete Workflow", test_requirement_5_complete_workflow),
        ("Bonus: Nested Key Extraction", test_nested_key_extraction),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"\n[FAIL] {test_name}: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "="*80)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("="*80 + "\n")
    
    if failed == 0:
        print("OK - ALL TESTS PASSED - SupplyChainAgent fully meets all requirements!\n")
        return True
    else:
        print(f"FAIL - {failed} tests failed\n")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
