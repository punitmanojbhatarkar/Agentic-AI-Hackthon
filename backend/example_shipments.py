"""
Example usage and integration test for detect_delay_impact.

This demonstrates shipment delay impact detection with realistic scenarios.
"""

from shipments import detect_delay_impact
import json


def demo_delay_impact_detection():
    """Run live examples of shipment delay impact detection."""
    
    # Example 1: Critical delay with multiple premium customers
    print("=" * 70)
    print("EXAMPLE 1: Critical Delay (Multiple Premium Customers)")
    print("=" * 70)
    
    critical_shipment = {
        "promised_date": "2024-01-10",
        "current_status": "delayed",
        "estimated_delivery": "2024-01-17"  # 7 days late
    }
    
    critical_orders = [
        {"order_id": f"ORD-PREMIUM-{i:03d}", "customer_tier": "premium", "sku_id": "SKU-WIDGET", "quantity": 500}
        for i in range(8)  # 8 premium = 16 weighted = 80 score
    ]
    
    result_critical = detect_delay_impact("SHIP-CRITICAL-001", critical_shipment, critical_orders)
    print(json.dumps(result_critical, indent=2))
    print()
    
    # Example 2: Moderate delay with mixed customers
    print("=" * 70)
    print("EXAMPLE 2: Moderate Delay (Mixed Premium & Standard)")
    print("=" * 70)
    
    moderate_shipment = {
        "promised_date": "2024-01-15",
        "current_status": "delayed",
        "estimated_delivery": "2024-01-17"  # 2 days late
    }
    
    moderate_orders = [
        {"order_id": "ORD-PREM-001", "customer_tier": "premium", "sku_id": "SKU-COMPONENT-A", "quantity": 300},
        {"order_id": "ORD-PREM-002", "customer_tier": "premium", "sku_id": "SKU-COMPONENT-A", "quantity": 200},
        {"order_id": "ORD-STD-001", "customer_tier": "standard", "sku_id": "SKU-COMPONENT-B", "quantity": 1000},
        {"order_id": "ORD-STD-002", "customer_tier": "standard", "sku_id": "SKU-COMPONENT-B", "quantity": 500},
        {"order_id": "ORD-STD-003", "customer_tier": "standard", "sku_id": "SKU-COMPONENT-C", "quantity": 750},
    ]
    
    result_moderate = detect_delay_impact("SHIP-MODERATE-100", moderate_shipment, moderate_orders)
    print(json.dumps(result_moderate, indent=2))
    print()
    
    # Example 3: Minor delay with single standard order
    print("=" * 70)
    print("EXAMPLE 3: Minor Delay (Single Standard Customer)")
    print("=" * 70)
    
    minor_shipment = {
        "promised_date": "2024-01-20",
        "current_status": "delayed",
        "estimated_delivery": "2024-01-21"  # 1 day late
    }
    
    minor_orders = [
        {"order_id": "ORD-STANDARD-001", "customer_tier": "standard", "sku_id": "SKU-PART-001", "quantity": 100}
    ]
    
    result_minor = detect_delay_impact("SHIP-MINOR-200", minor_shipment, minor_orders)
    print(json.dumps(result_minor, indent=2))
    print()
    
    # Example 4: On-time delivery
    print("=" * 70)
    print("EXAMPLE 4: On-Time Delivery (No Delay)")
    print("=" * 70)
    
    ontime_shipment = {
        "promised_date": "2024-01-25",
        "current_status": "in_transit",
        "estimated_delivery": "2024-01-25"
    }
    
    ontime_orders = [
        {"order_id": "ORD-URGENT-001", "customer_tier": "premium", "sku_id": "SKU-CRITICAL", "quantity": 1000},
        {"order_id": "ORD-URGENT-002", "customer_tier": "premium", "sku_id": "SKU-CRITICAL", "quantity": 500},
    ]
    
    result_ontime = detect_delay_impact("SHIP-ONTIME-300", ontime_shipment, ontime_orders)
    print(json.dumps(result_ontime, indent=2))
    print()
    
    # Example 5: Pending shipment (no estimated delivery yet)
    print("=" * 70)
    print("EXAMPLE 5: Pending Shipment (Unknown ETA)")
    print("=" * 70)
    
    pending_shipment = {
        "promised_date": "2024-02-01",
        "current_status": "at_warehouse",
        "estimated_delivery": None
    }
    
    pending_orders = [
        {"order_id": f"ORD-{i:04d}", "customer_tier": "premium", "sku_id": "SKU-NEW-001", "quantity": 200}
        for i in range(5)
    ]
    
    result_pending = detect_delay_impact("SHIP-PENDING-400", pending_shipment, pending_orders)
    print(json.dumps(result_pending, indent=2))
    print()


if __name__ == "__main__":
    demo_delay_impact_detection()
