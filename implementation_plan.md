# SupplySense Full Implementation Plan

## Bug Fix #1: Supplier Risk Panel Empty

**Root cause:** sweep.py collects `risky_suppliers` but strips the `breakdown` dict before returning.
The frontend panel reads `supplier.breakdown.on_time_delivery_pct` — that key doesn't exist.

**Fix:** In `sweep.py` Phase 2, add `breakdown: result.get('breakdown', {})` to each risky_suppliers entry.

---

## Feature Build: Management Pages

### Backend (new endpoints in api.py)

**Inventory**
- GET  /api/inventory           – all SKUs with total stock across warehouses
- POST /api/inventory           – add new SKU (name, category, unit)
- PUT  /api/inventory/:sku_id   – edit SKU stock / details
- DELETE /api/inventory/:sku_id – remove SKU

**Suppliers**
- GET  /api/suppliers           – all suppliers
- POST /api/suppliers           – add supplier
- PUT  /api/suppliers/:id       – edit supplier
- DELETE /api/suppliers/:id     – remove supplier

**Action History**
- GET /api/actions/history      – all actions (any status), with timestamps

### Database (queries.py new functions)
- get_all_skus_with_stock() → joins skus + inventory
- add_sku(sku_id, name, category, unit_of_measure)
- update_sku(sku_id, updates)
- delete_sku(sku_id)
- get_all_suppliers_detail()
- add_supplier(supplier_id, name, country, contact_email, lead_time_days)
- update_supplier(supplier_id, updates)
- delete_supplier(supplier_id)
- get_all_actions() → all statuses

### Frontend (App.jsx rewrite)
- Sidebar navigation: Dashboard | Inventory | Suppliers | Action History
- InventoryPage: table with search + Add/Edit/Delete modals
- SuppliersPage: table with Add/Edit/Delete modals
- ActionHistoryPage: read-only table of all past actions
- Dashboard: unchanged content but now inside a tab/page
