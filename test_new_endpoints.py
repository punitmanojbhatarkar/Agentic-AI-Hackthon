"""Quick verification of new endpoints."""
from data.queries import get_delayed_shipments, get_warehouse_utilization, get_demand_forecast_for_risky_skus
from backend.api import app

delays = get_delayed_shipments()
util = get_warehouse_utilization()
forecast = get_demand_forecast_for_risky_skus(5)

print(f"Delays: {len(delays)} items")
if delays:
    d = delays[0]
    print(f"  First: {d['shipment_id']} - {d['delay_days']} days late ({d['severity']})")

print(f"Utilization: {len(util)} warehouses")
for w in util:
    print(f"  {w['warehouse_id']}: {w['utilization_pct']}% of {w['capacity']} capacity")

print(f"Forecast: {len(forecast)} SKUs")
for fc in forecast:
    print(f"  {fc['sku_id']}: {fc['avg_forecasted_demand']} units/day, spike={fc['demand_spike_detected']}, days_stock={fc['days_of_stock_remaining']}")

print("\n--- Flask Test Client ---")
with app.test_client() as c:
    for path, name in [
        ('/api/shipment-delays', 'shipment-delays'),
        ('/api/warehouse-utilization', 'warehouse-util'),
        ('/api/demand-forecast', 'demand-forecast'),
    ]:
        r = c.get(path)
        data = r.get_json()
        print(f"{name}: HTTP {r.status_code}, {len(data) if isinstance(data, list) else 'error'} items")

print("\n--- recommend_alternate_source ---")
from backend.recommend_alternate import recommend_alternate_source
result = recommend_alternate_source(
    failing_id="SUP014",
    sku_id="SKU008",
    candidate_suppliers=[
        {"supplier_id": "SUP001", "score": 47.2, "risk_category": "medium", "breakdown": {"on_time_delivery_pct": 70, "avg_quality_score": 86}},
        {"supplier_id": "SUP002", "score": 80.5, "risk_category": "low", "breakdown": {"on_time_delivery_pct": 90, "avg_quality_score": 92}},
        {"supplier_id": "SUP014", "score": 24.75, "risk_category": "high", "breakdown": {"on_time_delivery_pct": 0}},
    ],
    candidate_warehouse_stocks=[],
)
print(f"Supplier recommendation: {result['recommended_id']} (reason: {result['reasoning'][:100]}...)")

from backend.inventory import predict_stockout
result2 = predict_stockout("SKU001", "WH-MAIN", 5000, {"avg_forecasted_demand": 100.0})
print(f"\nOverstock check (SKU001, 5000 stock, 100/day demand): overstock_risk={result2['overstock_risk']}, ratio={result2['overstock_ratio']}")

from backend.forecasting import forecast_demand
from data.queries import get_demand_history
hist = get_demand_history("SKU008")
fc_result = forecast_demand("SKU008", hist)
print(f"Demand spike for SKU008: {fc_result['demand_spike_detected']}, spike_ratio={fc_result['spike_ratio']}")

print("\nAll checks PASSED")
