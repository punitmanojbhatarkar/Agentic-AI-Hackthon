"""
Example usage and integration test for supplier_risk_score.

This demonstrates the supplier risk module working with realistic supply chain data.
"""

from suppliers import supplier_risk_score
import json


def demo_supplier_risk_scoring():
    """Run live examples of supplier risk scoring."""
    
    # Example 1: Highly reliable supplier
    print("=" * 70)
    print("EXAMPLE 1: Highly Reliable Supplier (Low Risk)")
    print("=" * 70)
    
    reliable_supplier = [
        {
            "order_id": f"ORD-{i:04d}",
            "promised_date": f"2024-01-{10+i:02d}",
            "actual_date": f"2024-01-{10+i:02d}",  # Always on time
            "quality_rating": 9
        }
        for i in range(10)
    ]
    
    result_reliable = supplier_risk_score("SUP-RELIABLE-001", reliable_supplier)
    print(json.dumps(result_reliable, indent=2))
    print()
    
    # Example 2: Mediocre supplier
    print("=" * 70)
    print("EXAMPLE 2: Mediocre Supplier (Medium Risk)")
    print("=" * 70)
    
    mediocre_supplier = [
        {
            "order_id": f"ORD-{i:04d}",
            "promised_date": f"2024-01-{10+i:02d}",
            "actual_date": f"2024-01-{10+i+2:02d}",  # 2 days late consistently
            "quality_rating": 6
        }
        for i in range(8)
    ]
    
    result_mediocre = supplier_risk_score("SUP-MEDIOCRE-100", mediocre_supplier)
    print(json.dumps(result_mediocre, indent=2))
    print()
    
    # Example 3: Unreliable supplier
    print("=" * 70)
    print("EXAMPLE 3: Unreliable Supplier (High Risk)")
    print("=" * 70)
    
    unreliable_supplier = [
        {
            "order_id": f"ORD-{i:04d}",
            "promised_date": f"2024-01-{10+i:02d}",
            "actual_date": f"2024-01-{20+i:02d}",  # 10 days late
            "quality_rating": 3
        }
        for i in range(6)
    ]
    
    result_unreliable = supplier_risk_score("SUP-UNRELIABLE-200", unreliable_supplier)
    print(json.dumps(result_unreliable, indent=2))
    print()
    
    # Example 4: Supplier with mixed performance
    print("=" * 70)
    print("EXAMPLE 4: Mixed Performance Supplier (Variable Risk)")
    print("=" * 70)
    
    mixed_supplier = [
        {"order_id": "ORD-0001", "promised_date": "2024-01-10", "actual_date": "2024-01-09", "quality_rating": 9},
        {"order_id": "ORD-0002", "promised_date": "2024-01-15", "actual_date": "2024-01-17", "quality_rating": 6},
        {"order_id": "ORD-0003", "promised_date": "2024-01-20", "actual_date": "2024-01-20", "quality_rating": 8},
        {"order_id": "ORD-0004", "promised_date": "2024-01-25", "actual_date": "2024-01-25", "quality_rating": 7},
        {"order_id": "ORD-0005", "promised_date": "2024-02-01", "actual_date": None, "quality_rating": 8},  # Pending
    ]
    
    result_mixed = supplier_risk_score("SUP-MIXED-300", mixed_supplier)
    print(json.dumps(result_mixed, indent=2))
    print()
    
    # Example 5: New supplier (no delivery history)
    print("=" * 70)
    print("EXAMPLE 5: New Supplier (No History - Unknown Risk)")
    print("=" * 70)
    
    result_new = supplier_risk_score("SUP-NEW-400", [])
    print(json.dumps(result_new, indent=2))
    print()
    
    # Example 6: Supplier with pending orders only
    print("=" * 70)
    print("EXAMPLE 6: Supplier with Only Pending Orders")
    print("=" * 70)
    
    pending_supplier = [
        {
            "order_id": f"ORD-{i:04d}",
            "promised_date": f"2024-02-{10+i:02d}",
            "actual_date": None,  # All pending
            "quality_rating": 7
        }
        for i in range(5)
    ]
    
    result_pending = supplier_risk_score("SUP-PENDING-500", pending_supplier)
    print(json.dumps(result_pending, indent=2))
    print()


if __name__ == "__main__":
    demo_supplier_risk_scoring()
