"""
Example usage and integration test for recommend_allocation.

This demonstrates inventory allocation with realistic fulfillment scenarios.
"""

from allocation import recommend_allocation
import json


def demo_allocation_recommendations():
    """Run live examples of inventory allocation."""
    
    # Example 1: Full fulfillment - abundant stock
    print("=" * 70)
    print("EXAMPLE 1: Full Fulfillment (Abundant Stock)")
    print("=" * 70)
    
    orders_full = [
        {"order_id": "ORD-PREM-001", "customer_tier": "premium", "quantity_requested": 100, "order_date": "2024-01-10"},
        {"order_id": "ORD-PREM-002", "customer_tier": "premium", "quantity_requested": 80, "order_date": "2024-01-11"},
        {"order_id": "ORD-STD-001", "customer_tier": "standard", "quantity_requested": 150, "order_date": "2024-01-12"},
    ]
    
    result_full = recommend_allocation("SKU-WIDGET-FULL", 500, orders_full)
    print(json.dumps(result_full, indent=2))
    print()
    
    # Example 2: Priority allocation - limited stock
    print("=" * 70)
    print("EXAMPLE 2: Priority Allocation (Limited Stock)")
    print("=" * 70)
    
    orders_priority = [
        {"order_id": "ORD-STD-001", "customer_tier": "standard", "quantity_requested": 150, "order_date": "2024-01-10"},
        {"order_id": "ORD-PREM-001", "customer_tier": "premium", "quantity_requested": 100, "order_date": "2024-01-15"},
        {"order_id": "ORD-STD-002", "customer_tier": "standard", "quantity_requested": 200, "order_date": "2024-01-11"},
    ]
    
    result_priority = recommend_allocation("SKU-COMPONENT-LIMITED", 200, orders_priority)
    print(json.dumps(result_priority, indent=2))
    print()
    
    # Example 3: Shortage - partial allocations
    print("=" * 70)
    print("EXAMPLE 3: Shortage (Partial Allocations)")
    print("=" * 70)
    
    orders_shortage = [
        {"order_id": "ORD-PREM-001", "customer_tier": "premium", "quantity_requested": 75, "order_date": "2024-01-08"},
        {"order_id": "ORD-PREM-002", "customer_tier": "premium", "quantity_requested": 100, "order_date": "2024-01-10"},
        {"order_id": "ORD-STD-001", "customer_tier": "standard", "quantity_requested": 300, "order_date": "2024-01-09"},
    ]
    
    result_shortage = recommend_allocation("SKU-SCARCE", 120, orders_shortage)
    print(json.dumps(result_shortage, indent=2))
    print()
    
    # Example 4: Zero stock - no allocation
    print("=" * 70)
    print("EXAMPLE 4: Zero Stock (No Allocation)")
    print("=" * 70)
    
    orders_zero = [
        {"order_id": "ORD-PREM-001", "customer_tier": "premium", "quantity_requested": 50, "order_date": "2024-01-10"},
        {"order_id": "ORD-STD-001", "customer_tier": "standard", "quantity_requested": 100, "order_date": "2024-01-11"},
    ]
    
    result_zero = recommend_allocation("SKU-OUTOFSTOCK", 0, orders_zero)
    print(json.dumps(result_zero, indent=2))
    print()
    
    # Example 5: Mixed tier with FIFO within tiers
    print("=" * 70)
    print("EXAMPLE 5: Mixed Tier (FIFO Within Each Tier)")
    print("=" * 70)
    
    orders_mixed = [
        {"order_id": "ORD-PREM-002", "customer_tier": "premium", "quantity_requested": 60, "order_date": "2024-01-15"},
        {"order_id": "ORD-STD-001", "customer_tier": "standard", "quantity_requested": 80, "order_date": "2024-01-10"},
        {"order_id": "ORD-PREM-001", "customer_tier": "premium", "quantity_requested": 50, "order_date": "2024-01-12"},
        {"order_id": "ORD-STD-002", "customer_tier": "standard", "quantity_requested": 120, "order_date": "2024-01-14"},
    ]
    
    result_mixed = recommend_allocation("SKU-MIXED-ORDERS", 200, orders_mixed)
    print(json.dumps(result_mixed, indent=2))
    print()


if __name__ == "__main__":
    demo_allocation_recommendations()
