"""
SupplySense data layer.

Provides database schema, synthetic data generation, data access layer,
and query functions for the agentic supply chain intelligence system.

Main exports:
  Schema Layer:
    - schema.init_db() — Initialize SQLite database with all tables
    - schema.get_db_connection() — Get connection to initialized database

  Data Generation:
    - generator.generate_data() — Generate 2,500+ synthetic records

  Data Access (High-level):
    - store.SupplyChainDataStore — DAL with 30+ methods

  Direct Queries (Low-level):
    - queries.get_demand_history() — Fetch demand for forecasting
    - queries.get_current_stock() — Fetch inventory
    - queries.get_supplier_delivery_history() — Fetch supplier metrics
    - queries.get_shipment_data() — Fetch shipment status
    - queries.get_downstream_orders() — Fetch customer orders
    - queries.save_pending_action() — Store AI-proposed actions
    - (and 5+ more query functions)

Usage Examples:

  # One-time setup:
  from data.schema import init_db
  from data.generator import generate_data
  
  conn = init_db("data/supplysense.db")
  conn.close()
  summary = generate_data("data/supplysense.db")
  
  # Use queries in agents/backend functions:
  from data.queries import (
      get_demand_history,
      get_current_stock,
      get_supplier_delivery_history
  )
  from backend.forecasting import forecast_demand
  
  demand = get_demand_history("SKU001")  # [{"date": "...", "units_sold": int}, ...]
  forecast = forecast_demand("SKU001", demand)
  
  stock = get_current_stock("SKU001", "WH-MAIN")
  history = get_supplier_delivery_history("SUP001")
"""

from data.schema import init_db, get_db_connection, drop_all_tables
from data.generator import generate_data
from data.store import SupplyChainDataStore
from data.queries import (
    get_all_sku_ids,
    get_all_supplier_ids,
    get_all_warehouse_ids,
    get_demand_history,
    get_current_stock,
    get_sku_total_stock,
    get_supplier_delivery_history,
    get_shipment_data,
    get_downstream_orders,
    get_pending_orders,
    save_pending_action,
    get_pending_actions,
    update_action_status,
)

__all__ = [
    # Schema
    "init_db",
    "get_db_connection",
    "drop_all_tables",
    # Generation
    "generate_data",
    # High-level DAL
    "SupplyChainDataStore",
    # Low-level Queries
    "get_all_sku_ids",
    "get_all_supplier_ids",
    "get_all_warehouse_ids",
    "get_demand_history",
    "get_current_stock",
    "get_sku_total_stock",
    "get_supplier_delivery_history",
    "get_shipment_data",
    "get_downstream_orders",
    "get_pending_orders",
    "save_pending_action",
    "get_pending_actions",
    "update_action_status",
]
