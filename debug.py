import json
from data.queries import get_all_suppliers_detail, get_delayed_shipments

print('--- SUPPLIERS ---')
suppliers = get_all_suppliers_detail()
for s in suppliers:
    if s['supplier_id'] in ('SUP003', 'SUP014'):
        print(f"{s['supplier_id']}: {s.get('risk_category')} / {s.get('risk_level')} / Score: {s.get('risk_score')}")

print('\n--- SHIPMENTS ---')
delays = get_delayed_shipments()
for d in delays:
    if d['shipment_id'] == 'SHIP-20004':
        print(f"Shipment: {d['shipment_id']}")
        print(f"  promised_date: {d['promised_date']}")
        print(f"  estimated_delivery: {d['estimated_delivery']}")
        print(f"  delay_days: {d['delay_days']}")
