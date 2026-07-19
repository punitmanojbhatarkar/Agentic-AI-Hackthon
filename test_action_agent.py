"""
Test suite for action_agent.propose_action()

Verifies:
1. Reorder action generation from stockout findings
2. Supplier switch action generation from risk findings
3. Proper UUID and timestamp generation
4. Reasoning with specific numbers
5. Error handling for invalid inputs
"""

import sys
from datetime import datetime
import json
from uuid import UUID

sys.path.insert(0, '.')

from agents.action_agent import (
    propose_action,
    propose_actions_from_sweep,
)


def test_stockout_reorder_action():
    """Test reorder action proposal from stockout finding."""
    print("\n" + "="*80)
    print("TEST 1: Stockout Reorder Action")
    print("="*80)
    
    finding = {
        "sku_id": "SKU-WIDGET-100",
        "warehouse_id": "WH-MAIN",
        "current_stock": 250,
        "recommended_reorder_quantity": 1400,
        "days_until_stockout": 2.5,
        "risk_level": "critical"
    }
    
    action = propose_action(finding, "stockout")
    
    # Verify structure
    assert "action_id" in action, "Missing action_id"
    assert "action_type" in action, "Missing action_type"
    assert "details" in action, "Missing details"
    assert "status" in action, "Missing status"
    assert "created_by" in action, "Missing created_by"
    assert "reasoning" in action, "Missing reasoning"
    assert "created_at" in action, "Missing created_at"
    
    # Verify values
    assert action["action_type"] == "reorder", "Action type should be 'reorder'"
    assert action["status"] == "pending_approval", "Status should be 'pending_approval'"
    assert action["created_by"] == "agent", "Created by should be 'agent'"
    
    # Verify details
    details = action["details"]
    assert details["sku_id"] == "SKU-WIDGET-100"
    assert details["warehouse_id"] == "WH-MAIN"
    assert details["quantity"] == 1400
    assert details["urgency_level"] == "CRITICAL"
    
    # Verify reasoning contains specific numbers
    reasoning = action["reasoning"]
    assert "250" in reasoning or "250 units" in reasoning, "Reasoning should mention current stock"
    assert "1400" in reasoning, "Reasoning should mention reorder quantity"
    assert "2.5" in reasoning, "Reasoning should mention days until stockout"
    
    # Verify action_id is valid UUID
    try:
        UUID(action["action_id"])
        print("[OK] action_id is valid UUID")
    except ValueError:
        raise AssertionError("action_id is not a valid UUID")
    
    # Verify created_at is ISO timestamp
    try:
        datetime.fromisoformat(action["created_at"].replace("Z", "+00:00"))
        print("[OK] created_at is valid ISO timestamp")
    except ValueError:
        raise AssertionError("created_at is not ISO format")
    
    print(f"[OK] Reorder action generated")
    print(f"  - action_id: {action['action_id'][:8]}...")
    print(f"  - action_type: {action['action_type']}")
    print(f"  - urgency_level: {action['details']['urgency_level']}")
    print(f"  - quantity: {action['details']['quantity']} units")
    print(f"  - reasoning: {action['reasoning'][:80]}...")
    
    return True


def test_high_risk_urgency():
    """Test that high-risk finding gets HIGH urgency."""
    print("\n" + "="*80)
    print("TEST 2: High Risk Urgency Level")
    print("="*80)
    
    finding = {
        "sku_id": "SKU-GADGET-50",
        "warehouse_id": "WH-EAST",
        "current_stock": 500,
        "recommended_reorder_quantity": 1400,
        "days_until_stockout": 5.0,
        "risk_level": "high"
    }
    
    action = propose_action(finding, "stockout")
    
    assert action["details"]["urgency_level"] == "HIGH", "Should be HIGH for 5 days"
    print(f"[OK] 5 days until stockout -> urgency_level = HIGH")
    
    return True


def test_supplier_risk_action():
    """Test supplier switch action proposal."""
    print("\n" + "="*80)
    print("TEST 3: Supplier Risk Switch Action")
    print("="*80)
    
    finding = {
        "supplier_id": "SUP-VENDOR-B",
        "score": 35.0,
        "risk_category": "high",
        "breakdown": {
            "on_time_delivery_pct": 60.0,
            "lead_time_variance_days": 3.2,
            "avg_quality_score": 60.0
        }
    }
    
    action = propose_action(finding, "supplier_risk")
    
    # Verify structure
    assert action["action_type"] == "switch_supplier", "Action type should be 'switch_supplier'"
    assert action["status"] == "pending_approval"
    assert action["created_by"] == "agent"
    
    # Verify details
    details = action["details"]
    assert details["supplier_id"] == "SUP-VENDOR-B"
    assert details["risk_score"] == 35.0
    assert details["on_time_delivery_pct"] == 60.0
    assert details["lead_time_variance_days"] == 3.2
    
    # Verify reasoning contains specific numbers
    reasoning = action["reasoning"]
    assert "35" in reasoning, "Reasoning should mention risk score"
    assert "60" in reasoning, "Reasoning should mention on-time percentage"
    assert "3.2" in reasoning, "Reasoning should mention lead time variance"
    
    print(f"[OK] Supplier switch action generated")
    print(f"  - action_type: {action['action_type']}")
    print(f"  - supplier_id: {action['details']['supplier_id']}")
    print(f"  - risk_score: {action['details']['risk_score']:.1f}")
    print(f"  - reasoning: {action['reasoning'][:80]}...")
    
    return True


def test_error_handling_invalid_type():
    """Test error handling for invalid finding_type."""
    print("\n" + "="*80)
    print("TEST 4: Error Handling - Invalid Finding Type")
    print("="*80)
    
    finding = {"sku_id": "SKU-123"}
    
    try:
        propose_action(finding, "invalid_type")
        assert False, "Should raise ValueError"
    except ValueError as e:
        assert "finding_type must be" in str(e)
        print("[OK] ValueError raised for invalid finding_type")
    
    return True


def test_error_handling_missing_fields():
    """Test error handling for missing required fields."""
    print("\n" + "="*80)
    print("TEST 5: Error Handling - Missing Fields")
    print("="*80)
    
    # Missing days_until_stockout
    incomplete_finding = {
        "sku_id": "SKU-123",
        "warehouse_id": "WH-MAIN",
        "current_stock": 500,
        "recommended_reorder_quantity": 1400,
        "risk_level": "high"
    }
    
    try:
        propose_action(incomplete_finding, "stockout")
        assert False, "Should raise KeyError"
    except KeyError as e:
        assert "missing required fields" in str(e)
        print("[OK] KeyError raised for missing fields")
    
    return True


def test_error_handling_wrong_type():
    """Test error handling for non-dict finding."""
    print("\n" + "="*80)
    print("TEST 6: Error Handling - Wrong Type")
    print("="*80)
    
    try:
        propose_action("not a dict", "stockout")
        assert False, "Should raise TypeError"
    except TypeError as e:
        assert "must be dict" in str(e)
        print("[OK] TypeError raised for non-dict finding")
    
    return True


def test_batch_actions_from_sweep():
    """Test batch action generation from sweep results."""
    print("\n" + "="*80)
    print("TEST 7: Batch Actions from Sweep")
    print("="*80)
    
    stockouts = [
        {
            "sku_id": "SKU-WIDGET-100",
            "warehouse_id": "WH-MAIN",
            "current_stock": 250,
            "recommended_reorder_quantity": 1400,
            "days_until_stockout": 2.5,
            "risk_level": "critical"
        },
        {
            "sku_id": "SKU-GADGET-50",
            "warehouse_id": "WH-EAST",
            "current_stock": 500,
            "recommended_reorder_quantity": 1400,
            "days_until_stockout": 5.0,
            "risk_level": "high"
        }
    ]
    
    suppliers = [
        {
            "supplier_id": "SUP-VENDOR-B",
            "score": 35.0,
            "risk_category": "high",
            "breakdown": {
                "on_time_delivery_pct": 60.0,
                "lead_time_variance_days": 3.2,
                "avg_quality_score": 60.0
            }
        }
    ]
    
    batch = propose_actions_from_sweep(stockouts, suppliers)
    
    assert batch["total_actions"] == 3, "Should have 3 total actions"
    assert len(batch["stockout_actions"]) == 2, "Should have 2 stockout actions"
    assert len(batch["supplier_actions"]) == 1, "Should have 1 supplier action"
    
    print(f"[OK] Batch actions generated")
    print(f"  - stockout_actions: {len(batch['stockout_actions'])}")
    print(f"  - supplier_actions: {len(batch['supplier_actions'])}")
    print(f"  - total_actions: {batch['total_actions']}")
    
    # Verify all actions are properly formed
    for action in batch["stockout_actions"] + batch["supplier_actions"]:
        assert "action_id" in action
        assert "status" in action and action["status"] == "pending_approval"
    
    print("[OK] All actions properly formed")
    
    return True


def test_reasoning_quality():
    """Test that reasoning includes specific numbers and context."""
    print("\n" + "="*80)
    print("TEST 8: Reasoning Quality")
    print("="*80)
    
    # Test stockout reasoning
    stockout = {
        "sku_id": "SKU-WIDGET-100",
        "warehouse_id": "WH-MAIN",
        "current_stock": 250,
        "recommended_reorder_quantity": 1400,
        "days_until_stockout": 2.5,
        "risk_level": "critical"
    }
    
    action = propose_action(stockout, "stockout")
    reasoning = action["reasoning"]
    
    print(f"Stockout reasoning:")
    print(f"  {reasoning}")
    
    # Verify reasoning quality
    assert "CRITICAL" in reasoning or "critical" in reasoning.lower()
    assert "250" in reasoning  # current stock
    assert "1400" in reasoning  # reorder qty
    assert "2.5" in reasoning  # days
    assert "14-day" in reasoning  # buffer period
    
    print("[OK] Stockout reasoning includes all specific numbers\n")
    
    # Test supplier reasoning
    supplier = {
        "supplier_id": "SUP-VENDOR-B",
        "score": 35.0,
        "risk_category": "high",
        "breakdown": {
            "on_time_delivery_pct": 60.0,
            "lead_time_variance_days": 3.2,
            "avg_quality_score": 60.0
        }
    }
    
    action = propose_action(supplier, "supplier_risk")
    reasoning = action["reasoning"]
    
    print(f"Supplier reasoning:")
    print(f"  {reasoning}")
    
    assert "35" in reasoning  # score
    assert "60" in reasoning  # on-time pct
    assert "3.2" in reasoning  # variance
    
    print("[OK] Supplier reasoning includes all specific metrics")
    
    return True


def run_all_tests():
    """Run all tests."""
    print("\n" + "="*80)
    print("ACTION AGENT TEST SUITE")
    print("="*80)
    
    tests = [
        ("Stockout Reorder Action", test_stockout_reorder_action),
        ("High Risk Urgency Level", test_high_risk_urgency),
        ("Supplier Risk Switch Action", test_supplier_risk_action),
        ("Error Handling - Invalid Type", test_error_handling_invalid_type),
        ("Error Handling - Missing Fields", test_error_handling_missing_fields),
        ("Error Handling - Wrong Type", test_error_handling_wrong_type),
        ("Batch Actions from Sweep", test_batch_actions_from_sweep),
        ("Reasoning Quality", test_reasoning_quality),
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
        print("OK - ALL TESTS PASSED - propose_action() is ready!\n")
        return True
    else:
        print(f"FAIL - {failed} tests failed\n")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
