"""
Test suite for run_intelligence_sweep().

Verifies:
1. Scans all SKUs for stockout risk
2. Scans all suppliers for reliability risk
3. Collects findings efficiently
4. Single Groq call for executive summary
5. Returns proper structure with timestamp
"""

import sys
import json
from unittest.mock import Mock, MagicMock
from datetime import datetime

sys.path.insert(0, '.')

from agents.sweep import run_intelligence_sweep, create_sweep_scheduler


def create_mock_data_store():
    """Create mock data store with realistic supply chain data."""
    
    def get_warehouse_ids():
        return ["WH-MAIN", "WH-EAST", "WH-WEST"]
    
    def get_forecast(sku_id):
        return {
            "sku_id": sku_id,
            "avg_forecasted_demand": 100.0,
            "trend": "stable",
            "confidence": 0.85
        }
    
    def get_current_stock(sku_id, warehouse_id):
        # Simulate some SKUs being low stock
        if "WIDGET" in sku_id and warehouse_id == "WH-MAIN":
            return 250  # 2.5 days of stock (critical)
        elif "GADGET" in sku_id and warehouse_id == "WH-EAST":
            return 500  # 5 days of stock (high)
        else:
            return 1500  # Healthy stock
    
    def get_delivery_history(supplier_id):
        if "RELIABLE" in supplier_id:
            return [
                {"order_id": f"ORD-{i}", "promised_date": "2024-01-15",
                 "actual_date": "2024-01-15", "quality_rating": 9}
                for i in range(1, 6)
            ]
        else:
            # Low performer
            return [
                {"order_id": f"ORD-{i}", "promised_date": "2024-01-15",
                 "actual_date": "2024-01-17" if i % 2 == 0 else "2024-01-15",
                 "quality_rating": 6}
                for i in range(1, 6)
            ]
    
    def get_all_skus():
        return ["SKU-WIDGET-100", "SKU-GADGET-50", "SKU-DOOHICKEY-200"]
    
    def get_all_suppliers():
        return ["SUP-RELIABLE-001", "SUP-VENDOR-B"]
    
    store = Mock()
    store.get_warehouse_ids = get_warehouse_ids
    store.get_forecast = get_forecast
    store.get_current_stock = get_current_stock
    store.get_delivery_history = get_delivery_history
    store.get_all_skus = get_all_skus
    store.get_all_suppliers = get_all_suppliers
    return store


def create_mock_tools():
    """Create mock backend tools."""
    
    def predict_stockout(sku_id, warehouse_id, current_stock, forecast_result):
        avg_demand = forecast_result.get("avg_forecasted_demand", 100)
        days = current_stock / avg_demand if avg_demand > 0 else None
        
        if days and days <= 3:
            risk = "critical"
        elif days and days <= 7:
            risk = "high"
        else:
            risk = "low"
        
        return {
            "sku_id": sku_id,
            "warehouse_id": warehouse_id,
            "current_stock": current_stock,
            "days_until_stockout": days,
            "risk_level": risk,
            "recommended_reorder_quantity": int(avg_demand * 14)
        }
    
    def supplier_risk_score(supplier_id, delivery_history):
        if "RELIABLE" in supplier_id:
            return {
                "supplier_id": supplier_id,
                "score": 88.0,
                "risk_category": "low",
                "breakdown": {
                    "on_time_delivery_pct": 95.0,
                    "lead_time_variance_days": 0.5,
                    "avg_quality_score": 85.0
                }
            }
        else:
            return {
                "supplier_id": supplier_id,
                "score": 35.0,
                "risk_category": "high",
                "breakdown": {
                    "on_time_delivery_pct": 60.0,
                    "lead_time_variance_days": 3.2,
                    "avg_quality_score": 60.0
                }
            }
    
    return {
        "predict_stockout": predict_stockout,
        "supplier_risk_score": supplier_risk_score,
    }


def create_mock_groq_client():
    """Create mock Groq client for summary generation."""
    
    client = Mock()
    
    summary_response = {
        "body": MagicMock(
            read=MagicMock(
                return_value=json.dumps({
                    "content": [
                        {
                            "text": "1. CRITICAL: SKU-WIDGET-100 at WH-MAIN has only 2.5 days inventory remaining. Urgent restock of 1400 units required within 24 hours.\n2. HIGH: SKU-GADGET-50 at WH-EAST shows 5 days supply. Recommend placing order for 1400 units within 48 hours.\n3. SUPPLIER RISK: SUP-VENDOR-B has 60% on-time delivery rate. Consider diversifying suppliers or adding backup sourcing for critical SKUs."
                        }
                    ]
                }).encode("utf-8")
            )
        )
    }
    
    client.invoke_model.return_value = summary_response
    return client


def test_basic_sweep():
    """Test basic sweep execution."""
    print("\n" + "="*80)
    print("TEST 1: Basic Sweep Execution")
    print("="*80)
    
    # Create mock agent
    agent = Mock()
    agent.groq_client = create_mock_groq_client()
    
    # Run sweep
    result = run_intelligence_sweep(
        agent=agent,
        tool_functions=create_mock_tools(),
        all_skus=["SKU-WIDGET-100", "SKU-GADGET-50"],
        all_suppliers=["SUP-RELIABLE-001", "SUP-VENDOR-B"],
        data_store=create_mock_data_store(),
    )
    
    # Verify structure
    assert "critical_stockouts" in result, "Missing critical_stockouts"
    assert "risky_suppliers" in result, "Missing risky_suppliers"
    assert "executive_summary" in result, "Missing executive_summary"
    assert "timestamp" in result, "Missing timestamp"
    assert "scan_stats" in result, "Missing scan_stats"
    
    print("[OK] Response structure valid")
    print(f"  - critical_stockouts: {len(result['critical_stockouts'])} items")
    print(f"  - risky_suppliers: {len(result['risky_suppliers'])} items")
    print(f"  - timestamp: {result['timestamp']}")
    
    return True


def test_stockout_detection():
    """Test that critical and high stockouts are detected."""
    print("\n" + "="*80)
    print("TEST 2: Stockout Risk Detection")
    print("="*80)
    
    agent = Mock()
    agent.groq_client = create_mock_groq_client()
    
    result = run_intelligence_sweep(
        agent=agent,
        tool_functions=create_mock_tools(),
        all_skus=["SKU-WIDGET-100", "SKU-GADGET-50", "SKU-DOOHICKEY-200"],
        all_suppliers=["SUP-RELIABLE-001"],
        data_store=create_mock_data_store(),
    )
    
    stockouts = result["critical_stockouts"]
    
    # Verify critical item found
    critical = [s for s in stockouts if s["risk_level"] == "critical"]
    high = [s for s in stockouts if s["risk_level"] == "high"]
    
    print(f"[OK] Detected {len(critical)} critical, {len(high)} high risk SKUs")
    
    for item in stockouts:
        print(f"  - {item['sku_id']} at {item['warehouse_id']}: "
              f"{item['risk_level'].upper()} ({item['days_until_stockout']:.1f} days)")
    
    assert len(critical) > 0 or len(high) > 0, "Should detect at least one risk"
    return True


def test_supplier_detection():
    """Test that high-risk suppliers are detected."""
    print("\n" + "="*80)
    print("TEST 3: Supplier Risk Detection")
    print("="*80)
    
    agent = Mock()
    agent.groq_client = create_mock_groq_client()
    
    result = run_intelligence_sweep(
        agent=agent,
        tool_functions=create_mock_tools(),
        all_skus=["SKU-WIDGET-100"],
        all_suppliers=["SUP-RELIABLE-001", "SUP-VENDOR-B"],
        data_store=create_mock_data_store(),
    )
    
    suppliers = result["risky_suppliers"]
    
    print(f"[OK] Detected {len(suppliers)} high-risk suppliers")
    
    for item in suppliers:
        print(f"  - {item['supplier_id']}: score={item['score']:.1f}, "
              f"on_time={item['on_time_delivery_pct']}%")
    
    assert len(suppliers) > 0, "Should detect high-risk supplier"
    return True


def test_executive_summary():
    """Test executive summary generation."""
    print("\n" + "="*80)
    print("TEST 4: Executive Summary Generation")
    print("="*80)
    
    agent = Mock()
    agent.groq_client = create_mock_groq_client()
    
    result = run_intelligence_sweep(
        agent=agent,
        tool_functions=create_mock_tools(),
        all_skus=["SKU-WIDGET-100", "SKU-GADGET-50"],
        all_suppliers=["SUP-VENDOR-B"],
        data_store=create_mock_data_store(),
    )
    
    summary = result["executive_summary"]
    
    print(f"[OK] Executive summary generated")
    print(f"     Length: {len(summary)} characters")
    print(f"\n     Summary:")
    for line in summary.split("\n"):
        if line.strip():
            print(f"     {line}")
    
    assert len(summary) > 0, "Summary should not be empty"
    assert "CRITICAL" in summary or "URGENT" in summary or "risk" in summary.lower(), \
        "Summary should mention risks"
    
    return True


def test_scan_stats():
    """Test that scan statistics are tracked."""
    print("\n" + "="*80)
    print("TEST 5: Scan Statistics Tracking")
    print("="*80)
    
    agent = Mock()
    agent.groq_client = create_mock_groq_client()
    
    result = run_intelligence_sweep(
        agent=agent,
        tool_functions=create_mock_tools(),
        all_skus=["SKU-WIDGET-100", "SKU-GADGET-50", "SKU-DOOHICKEY-200"],
        all_suppliers=["SUP-RELIABLE-001", "SUP-VENDOR-B"],
        data_store=create_mock_data_store(),
    )
    
    stats = result["scan_stats"]
    
    print(f"[OK] Scan statistics:")
    print(f"  - SKUs scanned: {stats['skus_scanned']}")
    print(f"  - Suppliers scanned: {stats['suppliers_scanned']}")
    print(f"  - Critical issues: {stats['critical_count']}")
    print(f"  - High issues: {stats['high_count']}")
    print(f"  - Risky suppliers: {stats['risky_supplier_count']}")
    print(f"  - Groq calls: {stats['groq_calls']}")
    
    assert stats["groq_calls"] == 1, "Should use exactly 1 Groq call for summary"
    return True


def test_scheduled_sweep():
    """Test sweep scheduler wrapper."""
    print("\n" + "="*80)
    print("TEST 6: Scheduled Sweep Wrapper")
    print("="*80)
    
    agent = Mock()
    agent.groq_client = create_mock_groq_client()
    
    # Create scheduler
    sweep_fn = create_sweep_scheduler(
        agent=agent,
        tool_functions=create_mock_tools(),
        data_store=create_mock_data_store(),
    )
    
    # Call as scheduled task (no parameters)
    result = sweep_fn()
    
    assert "critical_stockouts" in result, "Scheduler should return sweep result"
    assert "executive_summary" in result, "Scheduler should return summary"
    
    print("[OK] Scheduled sweep wrapper works")
    print(f"  - Can be called with no parameters: sweep_fn()")
    print(f"  - Returns full sweep result: {list(result.keys())}")
    
    return True


def test_efficiency():
    """Test that sweep is efficient (single Groq call regardless of SKU/supplier count)."""
    print("\n" + "="*80)
    print("TEST 7: Efficiency (Single Groq Call)")
    print("="*80)
    
    agent = Mock()
    groq_client = create_mock_groq_client()
    agent.groq_client = groq_client
    
    # Mock to track call count
    original_invoke = groq_client.invoke_model
    call_count = [0]
    
    def tracked_invoke(*args, **kwargs):
        call_count[0] += 1
        return original_invoke(*args, **kwargs)
    
    groq_client.invoke_model = tracked_invoke
    
    # Run sweep with many SKUs/suppliers
    result = run_intelligence_sweep(
        agent=agent,
        tool_functions=create_mock_tools(),
        all_skus=["SKU-" + str(i) for i in range(20)],  # 20 SKUs
        all_suppliers=["SUP-" + str(i) for i in range(5)],  # 5 suppliers
        data_store=create_mock_data_store(),
    )
    
    print(f"[OK] Efficiency test with 20 SKUs + 5 suppliers")
    print(f"  - Groq calls: {call_count[0]}")
    print(f"  - Expected: 1 (summary only)")
    
    assert call_count[0] == 1, f"Should use only 1 Groq call, used {call_count[0]}"
    return True


def run_all_tests():
    """Run all tests."""
    print("\n" + "="*80)
    print("INTELLIGENCE SWEEP TEST SUITE")
    print("="*80)
    
    tests = [
        ("Basic Sweep Execution", test_basic_sweep),
        ("Stockout Risk Detection", test_stockout_detection),
        ("Supplier Risk Detection", test_supplier_detection),
        ("Executive Summary Generation", test_executive_summary),
        ("Scan Statistics Tracking", test_scan_stats),
        ("Scheduled Sweep Wrapper", test_scheduled_sweep),
        ("Efficiency (Single Groq Call)", test_efficiency),
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
        print("OK - ALL TESTS PASSED - run_intelligence_sweep() is ready!\n")
        return True
    else:
        print(f"FAIL - {failed} tests failed\n")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
