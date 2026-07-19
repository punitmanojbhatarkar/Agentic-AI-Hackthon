"""
FINAL INTEGRATION TEST: SupplyChainAgent End-to-End Demo

This test demonstrates the complete agentic system working together
with realistic multi-step execution and dependency resolution.
"""

import sys
import json
from unittest.mock import Mock, MagicMock
from datetime import datetime, timedelta

sys.path.insert(0, '.')

from agents.orchestrator import SupplyChainAgent


def create_realistic_bedrock_client():
    """
    Create a Bedrock client that simulates a realistic multi-step supply chain
    investigation: forecast demand -> check stockout risk -> check supplier reliability
    """
    client = Mock()

    # Realistic 3-step plan for: "What's the critical issue with SKU-WIDGET?"
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
                                    {"date": (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d"), 
                                     "units_sold": 90 + (i % 20)}
                                    for i in range(30, 0, -1)
                                ]
                            },
                            "depends_on_previous": False,
                            "reasoning": "Need to forecast demand to understand inventory risk"
                        },
                        {
                            "step": 2,
                            "tool": "predict_stockout",
                            "parameters": {
                                "sku_id": "SKU-WIDGET-100",
                                "warehouse_id": "WH-MAIN",
                                "current_stock": 750,
                                "forecast_result": "FROM_STEP_1"
                            },
                            "depends_on_previous": True,
                            "reasoning": "Using forecast from Step 1, assess stockout risk at main warehouse"
                        },
                        {
                            "step": 3,
                            "tool": "supplier_risk_score",
                            "parameters": {
                                "supplier_id": "SUP-RELIABLE-001",
                                "delivery_history": [
                                    {"order_id": f"ORD-{i}", "promised_date": "2024-01-15", 
                                     "actual_date": "2024-01-14" if i % 3 == 0 else "2024-01-15",
                                     "quality_rating": 8 + (i % 2)}
                                    for i in range(1, 11)
                                ]
                            },
                            "depends_on_previous": False,
                            "reasoning": "Assess supplier reliability for potential restock"
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
                    "answer": "SKU-WIDGET faces a CRITICAL situation: forecast shows 100 units/day demand, current WH-MAIN inventory of 750 units provides only 7.5 days of supply (HIGH RISK). Primary supplier SUP-RELIABLE-001 has 85% on-time delivery reliability, which is acceptable but concerning given tight inventory window. IMMEDIATE ACTION REQUIRED: Place urgent restock order within 48 hours to maintain supply continuity.",
                    "confidence": "high",
                    "caveats": "Analysis assumes constant demand; supply chain disruptions could accelerate stockout. Supplier reliability data is historical and may not reflect current capacity."
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


def create_realistic_tools():
    """Create backend tools with realistic supply chain data."""
    
    def forecast_demand(sku_id, historical_demand):
        return {
            "sku_id": sku_id,
            "trend": "stable",
            "forecasted_daily_demand": [100.0, 99.0, 101.0, 98.0, 102.0, 99.0, 100.0],
            "avg_forecasted_demand": 100.0,
            "confidence": 0.88
        }
    
    def predict_stockout(sku_id, warehouse_id, current_stock, forecast_result):
        avg_demand = forecast_result.get("avg_forecasted_demand", 50)
        days = current_stock / avg_demand if avg_demand > 0 else None
        return {
            "sku_id": sku_id,
            "warehouse_id": warehouse_id,
            "current_stock": current_stock,
            "days_until_stockout": days,
            "risk_level": "high" if days and days <= 7 else "low",
            "recommended_reorder_quantity": int(avg_demand * 14) if avg_demand > 0 else 0
        }
    
    def supplier_risk_score(supplier_id, delivery_history):
        return {
            "supplier_id": supplier_id,
            "score": 85.0,
            "breakdown": {
                "on_time_delivery_pct": 85.0,
                "lead_time_variance_days": 1.5,
                "avg_quality_score": 85.0
            },
            "risk_category": "low"
        }
    
    def detect_delay_impact(shipment_id, shipment_data, downstream_orders):
        return {
            "shipment_id": shipment_id,
            "is_delayed": False,
            "delay_days": 0,
            "downstream_impact_score": 0.0,
            "affected_order_ids": [],
            "severity": "minor"
        }
    
    def recommend_allocation(sku_id, available_stock, pending_orders):
        return {
            "sku_id": sku_id,
            "available_stock": available_stock,
            "total_requested": 1000,
            "allocations": [],
            "fully_satisfied": False
        }
    
    return {
        "forecast_demand": forecast_demand,
        "predict_stockout": predict_stockout,
        "supplier_risk_score": supplier_risk_score,
        "detect_delay_impact": detect_delay_impact,
        "recommend_allocation": recommend_allocation,
    }


def demo_realistic_scenario():
    """
    DEMO: Realistic supply chain scenario
    
    Question: "What's the critical issue with SKU-WIDGET?"
    
    Expected: 3-step investigation
      Step 1: Forecast demand for SKU-WIDGET (30 days of history)
      Step 2: Check stockout risk at WH-MAIN (using Step 1's forecast)
      Step 3: Check supplier reliability for emergency restock
      
    Result: Multi-step trace showing dependency resolution
    """
    print("\n" + "="*80)
    print("REALISTIC DEMO: Supply Chain Risk Investigation")
    print("="*80)
    print("\nQuestion: What's the critical issue with SKU-WIDGET?")
    print("\nAgent Strategy:")
    print("  1. Forecast demand for SKU-WIDGET (historical data)")
    print("  2. Check stockout risk using forecast (Step 1 dependency)")
    print("  3. Check supplier reliability for potential emergency restock")
    print("\n" + "-"*80)
    
    bedrock = create_realistic_bedrock_client()
    tools = create_realistic_tools()
    agent = SupplyChainAgent(bedrock, tools)
    
    response = agent.answer_query("What's the critical issue with SKU-WIDGET?")
    
    # Display results
    print("\nEXECUTION TRACE:")
    print("-"*80)
    
    for step in response["execution_trace"]:
        print(f"\nStep {step['step']}: {step['tool'].upper()}")
        print(f"  Reasoning: {step['reasoning']}")
        print(f"  Parameters used:")
        for key, value in step['parameters_used'].items():
            if isinstance(value, dict):
                print(f"    - {key}: <dict with {len(value)} fields>")
            elif isinstance(value, list):
                print(f"    - {key}: <list with {len(value)} items>")
            else:
                print(f"    - {key}: {value}")
        
        if "result" in step:
            result = step["result"]
            print(f"  Result:")
            for key, value in result.items():
                if not isinstance(value, (dict, list)):
                    print(f"    - {key}: {value}")
    
    print("\n" + "-"*80)
    print("\nFINAL ANSWER:")
    print("-"*80)
    print(f"\nQuestion: {response['question']}")
    print(f"\nAnswer:\n{response['final_answer']}")
    print(f"\nConfidence: {response['confidence'].upper()}")
    print(f"Caveats: {response['caveats']}")
    
    # Validate all requirements met
    print("\n" + "="*80)
    print("VALIDATION CHECKLIST:")
    print("="*80)
    
    checks = [
        ("Multi-step execution", len(response["execution_trace"]) >= 2),
        ("Execution trace structure", all(
            set(e.keys()).issuperset({"step", "tool", "parameters_used", "reasoning", "result"})
            for e in response["execution_trace"]
        )),
        ("FROM_STEP_N substitution", any(
            "forecast_result" in e.get("parameters_used", {}) and 
            isinstance(e["parameters_used"]["forecast_result"], dict)
            for e in response["execution_trace"]
        )),
        ("Final answer present", len(response["final_answer"]) > 0),
        ("Confidence level", response["confidence"] in ["high", "medium", "low"]),
        ("Caveats present", len(response["caveats"]) > 0),
    ]
    
    for check_name, result in checks:
        status = "PASS" if result else "FAIL"
        print(f"  [{status}] {check_name}")
    
    all_passed = all(result for _, result in checks)
    
    print("\n" + "="*80)
    if all_passed:
        print("OK: ALL REQUIREMENTS VALIDATED")
        print("="*80 + "\n")
        return True
    else:
        print("FAIL: Some requirements failed")
        print("="*80 + "\n")
        return False


if __name__ == "__main__":
    success = demo_realistic_scenario()
    sys.exit(0 if success else 1)
