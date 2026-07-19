"""
Example usage and integration test for forecast_demand.

This demonstrates the forecasting module working with realistic supply chain data.
"""

from forecasting import forecast_demand
import json


def demo_forecast():
    """Run a live example of demand forecasting."""
    
    # Example 1: Increasing demand trend (90 days)
    print("=" * 70)
    print("EXAMPLE 1: Increasing Demand Trend (90 days)")
    print("=" * 70)
    
    increasing_demand = [
        {"date": f"2024-{1:02d}-{i % 28 + 1:02d}", "units_sold": 100 + i}
        for i in range(90)
    ]
    
    result_increasing = forecast_demand("SKU-WIDGET-100", increasing_demand)
    print(json.dumps(result_increasing, indent=2))
    print()
    
    # Example 2: Decreasing demand trend (90 days)
    print("=" * 70)
    print("EXAMPLE 2: Decreasing Demand Trend (90 days)")
    print("=" * 70)
    
    decreasing_demand = [
        {"date": f"2024-{1:02d}-{i % 28 + 1:02d}", "units_sold": 200 - i}
        for i in range(90)
    ]
    
    result_decreasing = forecast_demand("SKU-GADGET-200", decreasing_demand)
    print(json.dumps(result_decreasing, indent=2))
    print()
    
    # Example 3: Stable demand (90 days)
    print("=" * 70)
    print("EXAMPLE 3: Stable Demand (90 days)")
    print("=" * 70)
    
    stable_demand = [
        {"date": f"2024-{1:02d}-{i % 28 + 1:02d}", "units_sold": 150 + (i % 5)}
        for i in range(90)
    ]
    
    result_stable = forecast_demand("SKU-COMPONENT-300", stable_demand)
    print(json.dumps(result_stable, indent=2))
    print()
    
    # Example 4: Short dataset (<14 days)
    print("=" * 70)
    print("EXAMPLE 4: Short Dataset (<14 days) - Low Confidence")
    print("=" * 70)
    
    short_demand = [
        {"date": f"2024-01-{i+1:02d}", "units_sold": 100 + i*5}
        for i in range(10)
    ]
    
    result_short = forecast_demand("SKU-NEW-ITEM", short_demand)
    print(json.dumps(result_short, indent=2))
    print(f"\nNote: Confidence is {result_short['confidence']} (low) due to short dataset.")
    print()


if __name__ == "__main__":
    demo_forecast()
