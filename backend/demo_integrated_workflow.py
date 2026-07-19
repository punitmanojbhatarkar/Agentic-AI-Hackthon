#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Integration demonstration: Forecasting → Inventory Risk Assessment

Shows both layers working together in a realistic supply chain workflow.
"""

import sys
sys.path.insert(0, '.')

from backend.forecasting import forecast_demand
from backend.inventory import predict_stockout
import json


def demo_integrated_workflow():
    """Demonstrate end-to-end supply chain intelligence workflow."""
    
    print("=" * 80)
    print("SUPPLYSENSE: INTEGRATED WORKFLOW DEMONSTRATION")
    print("Demand Forecasting > Inventory Risk Assessment")
    print("=" * 80)
    print()
    
    # =========================================================================
    # Step 1: Generate 90 days of historical demand
    # =========================================================================
    print("STEP 1: Loading 90-day historical demand data")
    print("-" * 80)
    
    # Simulate realistic demand pattern: increasing trend
    historical_demand = [
        {"date": f"2024-01-{i+1:02d}", "units_sold": 80 + i}
        for i in range(90)
    ]
    print(f"  SKU: WIDGET-PRO-100")
    print(f"  Data points: {len(historical_demand)} days")
    print(f"  Date range: 2024-01-01 to 2024-03-31")
    print(f"  Demand range: {historical_demand[0]['units_sold']} to {historical_demand[-1]['units_sold']} units/day")
    print()
    
    # =========================================================================
    # Step 2: Forecast demand for next 7 days
    # =========================================================================
    print("STEP 2: Forecasting demand for next 7 days")
    print("-" * 80)
    
    forecast = forecast_demand("WIDGET-PRO-100", historical_demand)
    print(json.dumps({
        "sku_id": forecast["sku_id"],
        "trend": forecast["trend"],
        "avg_forecasted_demand": forecast["avg_forecasted_demand"],
        "confidence": forecast["confidence"],
        "next_7_days": forecast["forecasted_daily_demand"],
    }, indent=2))
    print()
    
    # =========================================================================
    # Step 3: Assess stockout risk at each warehouse
    # =========================================================================
    print("STEP 3: Assessing stockout risk across warehouses")
    print("-" * 80)
    
    warehouses = [
        {
            "warehouse_id": "WH-MAIN",
            "current_stock": 300,
            "description": "Main distribution center"
        },
        {
            "warehouse_id": "WH-EAST",
            "current_stock": 600,
            "description": "Eastern region hub"
        },
        {
            "warehouse_id": "WH-WEST",
            "current_stock": 1500,
            "description": "Western region hub"
        },
        {
            "warehouse_id": "WH-NORTH",
            "current_stock": 50,
            "description": "Northern outpost (low stock)"
        },
    ]
    
    inventory_results = []
    for warehouse in warehouses:
        result = predict_stockout(
            "WIDGET-PRO-100",
            warehouse["warehouse_id"],
            warehouse["current_stock"],
            forecast
        )
        inventory_results.append(result)
        
        # Format output
        status_icon = {
            "critical": "[!!!]",
            "high": "[!!! ]",
            "medium": "[!!  ]",
            "low": "[OK  ]"
        }[result["risk_level"]]
        
        days_str = f"{result['days_until_stockout']:.1f}" if result["days_until_stockout"] else "N/A"
        
        print(f"{status_icon} {result['warehouse_id']:12} | "
              f"Stock: {result['current_stock']:5} | "
              f"Days: {days_str:>5} | "
              f"Risk: {result['risk_level']:8} | "
              f"Reorder: {result['recommended_reorder_quantity']:5}")
    print()
    
    # =========================================================================
    # Step 4: Generate actionable insights
    # =========================================================================
    print("STEP 4: Actionable Insights & Recommendations")
    print("-" * 80)
    
    critical_warehouses = [r for r in inventory_results if r["risk_level"] == "critical"]
    high_risk_warehouses = [r for r in inventory_results if r["risk_level"] == "high"]
    medium_risk_warehouses = [r for r in inventory_results if r["risk_level"] == "medium"]
    total_reorder = sum(r["recommended_reorder_quantity"] for r in inventory_results)
    
    print(f"  Total SKUs at risk: {len([r for r in inventory_results if r['risk_level'] != 'low'])}/4")
    print(f"  Critical stockout risk: {len(critical_warehouses)} warehouse(s)")
    print(f"  High risk: {len(high_risk_warehouses)} warehouse(s)")
    print(f"  Medium risk: {len(medium_risk_warehouses)} warehouse(s)")
    print(f"  Total recommended reorder: {total_reorder} units")
    print()
    
    if critical_warehouses:
        print("  [URGENT] Critical Risk Warehouses:")
        for wh in critical_warehouses:
            print(f"    > {wh['warehouse_id']}: {wh['days_until_stockout']:.1f} days remaining")
            print(f"      Recommend immediate order of {wh['recommended_reorder_quantity']} units")
    print()
    
    # =========================================================================
    # Step 5: Summary for agent
    # =========================================================================
    print("STEP 5: Summary for Agent Decision Making")
    print("-" * 80)
    
    summary = {
        "sku": "WIDGET-PRO-100",
        "forecast": {
            "avg_daily_demand": forecast["avg_forecasted_demand"],
            "trend": forecast["trend"],
            "confidence": forecast["confidence"],
        },
        "warehouse_summary": {
            "total_warehouses": len(warehouses),
            "at_risk": len([r for r in inventory_results if r["risk_level"] != "low"]),
            "critical": len(critical_warehouses),
            "high": len(high_risk_warehouses),
        },
        "actions_required": {
            "urgent_restock": [r["warehouse_id"] for r in critical_warehouses],
            "total_units_to_order": total_reorder,
        }
    }
    
    print(json.dumps(summary, indent=2))
    print()
    
    print("=" * 80)
    print("End-to-end workflow complete. Ready for agent orchestration layer.")
    print("=" * 80)


if __name__ == "__main__":
    demo_integrated_workflow()
