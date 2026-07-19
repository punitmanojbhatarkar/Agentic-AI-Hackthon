from data.queries import get_supplier_delivery_history

history = get_supplier_delivery_history('SUP014')
print(f'Total orders: {len(history)}')
delivered = [h for h in history if h['actual_date']]
print(f'Delivered orders: {len(delivered)}')
print(f'Pending orders: {len(history) - len(delivered)}')

if history:
    print(f'\nSample order: {history[0]}')

from backend.suppliers import supplier_risk_score
risk = supplier_risk_score('SUP014', history)
print(f'\nRisk score: {risk["score"]}')
print(f'Risk category: {risk["risk_category"]}')
