"""
Example usage and integration test for predict_stockout.

This demonstrates the inventory module working with realistic supply chain data.
"""

from inventory import predict_stockout
import json


def demo_stockout_prediction():
    """Run live examples of stockout prediction."""
    
    # Example 1: Critical risk (urgent restock)
    print("=" * 70)
    print("EXAMPLE 1: Critical Risk — Urgent Restock Needed")
    print("=" * 70)
    
    forecast_high_demand = {"avg_forecasted_demand": 100.0, "trend": "increasing"}
    result_critical = predict_stockout(
        "SKU-WIDGET-100",
        "WH-MAIN",
        200,  # Only 200 units, with 100/day demand = 2 days
        forecast_high_demand,
    )
    print(json.dumps(result_critical, indent=2))
    print()
    
    # Example 2: High risk (restock soon)
    print("=" * 70)
    print("EXAMPLE 2: High Risk — Restock Within a Week")
    print("=" * 70)
    
    forecast_medium_demand = {"avg_forecasted_demand": 75.0, "trend": "stable"}
    result_high = predict_stockout(
        "SKU-GADGET-200",
        "WH-EAST",
        400,  # 400 units / 75 per day ≈ 5.3 days
        forecast_medium_demand,
    )
    print(json.dumps(result_high, indent=2))
    print()
    
    # Example 3: Medium risk (plan ahead)
    print("=" * 70)
    print("EXAMPLE 3: Medium Risk — Plan Restock in 1-2 Weeks")
    print("=" * 70)
    
    forecast_low_demand = {"avg_forecasted_demand": 50.0, "trend": "stable"}
    result_medium = predict_stockout(
        "SKU-COMPONENT-300",
        "WH-WEST",
        700,  # 700 units / 50 per day = 14 days (exactly at threshold)
        forecast_low_demand,
    )
    print(json.dumps(result_medium, indent=2))
    print()
    
    # Example 4: Low risk (adequate stock)
    print("=" * 70)
    print("EXAMPLE 4: Low Risk — Adequate Stock Level")
    print("=" * 70)
    
    forecast_stable_demand = {"avg_forecasted_demand": 60.0, "trend": "stable"}
    result_low = predict_stockout(
        "SKU-PART-400",
        "WH-CENTRAL",
        1500,  # 1500 units / 60 per day = 25 days
        forecast_stable_demand,
    )
    print(json.dumps(result_low, indent=2))
    print()
    
    # Example 5: Zero demand (no restock needed)
    print("=" * 70)
    print("EXAMPLE 5: No Demand — Stock Will Not Deplete")
    print("=" * 70)
    
    forecast_no_demand = {"avg_forecasted_demand": 0.0, "trend": "stable"}
    result_no_demand = predict_stockout(
        "SKU-OBSOLETE-500",
        "WH-SOUTH",
        1000,
        forecast_no_demand,
    )
    print(json.dumps(result_no_demand, indent=2))
    print()
    
    # Example 6: Stock already exceeds 14-day target
    print("=" * 70)
    print("EXAMPLE 6: Overstocked — No Reorder Needed")
    print("=" * 70)
    
    forecast_overstocked = {"avg_forecasted_demand": 50.0, "trend": "stable"}
    result_overstock = predict_stockout(
        "SKU-BULK-600",
        "WH-NORTH",
        1200,  # 1200 units >> 50*14=700 target
        forecast_overstocked,
    )
    print(json.dumps(result_overstock, indent=2))
    print(f"\nNote: Recommended reorder is 0 because current stock ({result_overstock['current_stock']} units) ")
    print(f"      already exceeds 14-day target ({int(50 * 14)} units).")
    print()


if __name__ == "__main__":
    demo_stockout_prediction()
