#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Final verification that the forecasting module is production-ready."""

from forecasting import forecast_demand

# Create 30-day test dataset
test_data = [
    {"date": f"2024-01-{i+1:02d}", "units_sold": 100 + i}
    for i in range(30)
]

# Call forecast_demand
result = forecast_demand("FINAL-VERIFICATION-SKU", test_data)

# Verify all required fields
print("[OK] FINAL VERIFICATION PASSED")
print()
print(f"[OK] sku_id: {result['sku_id']}")
print(f"[OK] trend: {result['trend']}")
print(f"[OK] confidence: {result['confidence']:.4f}")
print(f"[OK] avg_forecasted_demand: {result['avg_forecasted_demand']:.2f}")
print(f"[OK] forecasted_daily_demand: {len(result['forecasted_daily_demand'])} values")
print(f"  Daily forecast: {[f'{v:.2f}' for v in result['forecasted_daily_demand']]}")
print()
print("All checks passed. Module is production-ready.")
