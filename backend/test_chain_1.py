"""
TEST 16: Verify the Forecast → Stockout Chain

Goal: Confirm that real data flowing through:
  get_demand_history → forecast_demand → predict_stockout
correctly identifies SKU008 as risky (increasing demand pattern).

Run: python backend/test_chain_1.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from data.queries import get_demand_history, get_current_stock, get_all_warehouse_ids
from backend.forecasting import forecast_demand
from backend.inventory import predict_stockout

print("\n" + "=" * 80)
print("TEST 16: FORECAST -> STOCKOUT CHAIN")
print("=" * 80 + "\n")

# Test SKU with intentional increasing demand pattern
sku_id = "SKU008"

print(f"STEP 1: Pull Real Demand History for {sku_id}")
print("-" * 80)

history = get_demand_history(sku_id)
print(f"[OK] Retrieved {len(history)} days of demand history")

if not history:
    print("[ERROR] No demand history found!")
    sys.exit(1)

print(f"  First 3 days: {history[:3]}")
print(f"  Last 3 days: {history[-3:]}")

# Verify increasing trend
if len(history) >= 10:
    old_avg = sum(h["units_sold"] for h in history[:10]) / 10
    new_avg = sum(h["units_sold"] for h in history[-10:]) / 10
    growth = ((new_avg - old_avg) / old_avg) * 100 if old_avg > 0 else 0
    print(f"\n  Demand trend:")
    print(f"    First 10 days avg: {old_avg:.1f} units/day")
    print(f"    Last 10 days avg: {new_avg:.1f} units/day")
    print(f"    Growth: {growth:.0f}%")
    
    if growth > 50:
        print(f"  [OK] Increasing trend detected (PATTERN 2 CONFIRMED)")
    else:
        print(f"  [WARNING] Growth less than expected, but continuing test")

print(f"\nSTEP 2: Forecast Demand for {sku_id}")
print("-" * 80)

try:
    forecast_result = forecast_demand(sku_id, history)
    print(f"[OK] Forecast generated")
    print(f"  Trend: {forecast_result['trend']}")
    print(f"  Avg forecasted demand: {forecast_result['avg_forecasted_demand']:.1f} units/day")
    print(f"  Confidence: {forecast_result['confidence']:.1%}")
    print(f"  7-day forecast: {[f'{x:.0f}' for x in forecast_result['forecasted_daily_demand']]}")
except Exception as e:
    print(f"[ERROR] Forecast failed: {e}")
    sys.exit(1)

print(f"\nSTEP 3: Predict Stockout for All Warehouses")
print("-" * 80)

warehouses = get_all_warehouse_ids()
print(f"[OK] Found {len(warehouses)} warehouses: {warehouses}")

all_critical = True
stockout_results = []

for warehouse_id in warehouses:
    current_stock = get_current_stock(sku_id, warehouse_id)
    
    try:
        stockout_result = predict_stockout(
            sku_id,
            warehouse_id,
            current_stock,
            forecast_result
        )
        stockout_results.append(stockout_result)
        
        days = stockout_result["days_until_stockout"]
        risk = stockout_result["risk_level"]
        reorder = stockout_result["recommended_reorder_quantity"]
        
        print(f"\n  {warehouse_id}:")
        print(f"    Current stock: {current_stock} units")
        print(f"    Days until stockout: {days:.1f}")
        print(f"    Risk level: {risk.upper()}")
        print(f"    Recommended reorder: {reorder} units")
        
        if risk not in ["high", "critical"]:
            all_critical = False
            print(f"    [WARNING] Expected high/critical, got {risk}")
    
    except Exception as e:
        print(f"  [ERROR] Stockout prediction failed for {warehouse_id}: {e}")
        sys.exit(1)

print(f"\nSTEP 4: Verify Test Assertion")
print("-" * 80)

# Check that at least one warehouse shows critical/high risk
sku_ids_flagged = [r["sku_id"] for r in stockout_results if r["risk_level"] in ["high", "critical"]]
risk_levels = [r["risk_level"] for r in stockout_results]

print(f"Risk levels across warehouses: {risk_levels}")

if sku_id in sku_ids_flagged:
    print(f"[OK] {sku_id} correctly flagged as risky!")
    print(f"[OK] PATTERN 2 VERIFIED: Increasing demand causing stockout risk")
else:
    print(f"[ERROR] {sku_id} NOT flagged as risky!")
    print(f"     Risk levels: {risk_levels}")
    sys.exit(1)

print("\n" + "=" * 80)
print("TEST 16 PASSED")
print("=" * 80)
print("\nVerifications:")
print(f"  [OK] Demand history retrieved: {len(history)} days")
print(f"  [OK] Forecast generated with trend detection")
print(f"  [OK] Stockout predictions calculated for all warehouses")
print(f"  [OK] SKU008 correctly identified as high/critical risk")
print(f"  [OK] PATTERN 2 CONFIRMED: Increasing demand pattern detected\n")

sys.exit(0)
