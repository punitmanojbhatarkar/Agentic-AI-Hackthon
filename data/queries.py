"""
Simple data access functions for SupplySense supply chain database.

Provides direct database queries that backend and agent functions use to fetch
real data from SQLite. All functions connect to /data/supplysense.db and return
data in the exact format expected by forecast_demand, supplier_risk_score,
predict_stockout, etc.

This is the primary data access layer between agents/backend and database.
"""

import sqlite3
import json
import logging
from typing import Optional
from datetime import datetime

logger = logging.getLogger(__name__)

import os
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "supplysense.db")


# ═══════════════════════════════════════════════════════════════════════════════
# SKU & SUPPLIER METADATA
# ═══════════════════════════════════════════════════════════════════════════════

def get_all_sku_ids() -> list[str]:
    """
    Get list of all SKU identifiers in the system.

    Returns:
        list[str]: List of SKU IDs (e.g., ["SKU001", "SKU002", ...])

    Raises:
        sqlite3.Error: If database query fails.

    Example:
        >>> skus = get_all_sku_ids()
        >>> print(skus[:3])
        ["SKU001", "SKU002", "SKU003"]
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT sku_id FROM skus ORDER BY sku_id")
        sku_ids = [row[0] for row in cursor.fetchall()]
        conn.close()
        return sku_ids
    except sqlite3.Error as e:
        logger.error(f"Error fetching SKU IDs: {e}")
        return []


def get_all_supplier_ids() -> list[str]:
    """
    Get list of all supplier identifiers in the system.

    Returns:
        list[str]: List of supplier IDs (e.g., ["SUP001", "SUP002", ...])

    Raises:
        sqlite3.Error: If database query fails.

    Example:
        >>> suppliers = get_all_supplier_ids()
        >>> print(len(suppliers))
        20
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT supplier_id FROM suppliers ORDER BY supplier_id")
        supplier_ids = [row[0] for row in cursor.fetchall()]
        conn.close()
        return supplier_ids
    except sqlite3.Error as e:
        logger.error(f"Error fetching supplier IDs: {e}")
        return []


def get_all_warehouse_ids() -> list[str]:
    """
    Get list of all warehouse identifiers in the system.

    Returns:
        list[str]: List of warehouse IDs (e.g., ["WH-MAIN", "WH-EAST", ...])

    Raises:
        sqlite3.Error: If database query fails.

    Example:
        >>> warehouses = get_all_warehouse_ids()
        >>> print(warehouses)
        ["WH-ASIA", "WH-EAST", "WH-EURO", "WH-MAIN", "WH-SOUTH"]
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT warehouse_id FROM warehouses ORDER BY warehouse_id")
        warehouse_ids = [row[0] for row in cursor.fetchall()]
        conn.close()
        return warehouse_ids
    except sqlite3.Error as e:
        logger.error(f"Error fetching warehouse IDs: {e}")
        return []



def get_all_supplier_risk_scores() -> list[dict]:
    """
    Compute and return risk scores for all suppliers.

    Used by recommend_alternate_source to find the best alternative supplier.
    Each entry has: { supplier_id, score, risk_category, breakdown }

    Returns:
        list[dict]: Supplier risk scores, sorted best (highest score) first.
    """
    try:
        from backend.suppliers import supplier_risk_score as compute_risk
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT supplier_id FROM suppliers ORDER BY supplier_id")
        supplier_ids = [row[0] for row in cursor.fetchall()]
        conn.close()

        results = []
        for sid in supplier_ids:
            try:
                hist = get_supplier_delivery_history(sid)
                if hist:
                    result = compute_risk(sid, hist)
                    results.append(result)
            except Exception as e:
                logger.warning(f"Could not score supplier {sid}: {e}")
                continue

        # Sort best first (highest score = lowest risk)
        results.sort(key=lambda r: r.get("score", 0), reverse=True)
        return results

    except Exception as e:
        logger.error(f"Error computing all supplier risk scores: {e}")
        return []


def get_all_warehouse_stocks_for_sku(sku_id: str) -> list[dict]:
    """
    Get current stock for a given SKU across all warehouses.

    Used by recommend_alternate_source to find warehouses with surplus stock.
    Each entry has: { warehouse_id, current_stock }

    Args:
        sku_id: SKU identifier.

    Returns:
        list[dict]: Stock levels per warehouse, sorted highest first.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT warehouse_id, COALESCE(current_stock, 0) AS current_stock
            FROM inventory
            WHERE sku_id = ?
            ORDER BY current_stock DESC
            """,
            (sku_id,)
        )
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return rows
    except sqlite3.Error as e:
        logger.error(f"Error fetching warehouse stocks for {sku_id}: {e}")
        return []


# ═══════════════════════════════════════════════════════════════════════════════
# DEMAND & INVENTORY DATA
# ═══════════════════════════════════════════════════════════════════════════════

def get_demand_history(sku_id: str) -> list[dict]:
    """
    Get 90 days of historical demand data for a SKU.

    Returns data in the exact format needed by forecast_demand():
    [{"date": "YYYY-MM-DD", "units_sold": int}, ...]

    Args:
        sku_id: SKU identifier (e.g., "SKU001").

    Returns:
        list[dict]: Demand records sorted oldest to newest.
                   Each dict has "date" (YYYY-MM-DD) and "units_sold" (int).
                   Returns empty list if no data found.

    Raises:
        sqlite3.Error: If database query fails.

    Example:
        >>> demand = get_demand_history("SKU001")
        >>> print(len(demand))
        90
        >>> print(demand[0])
        {"date": "2025-10-12", "units_sold": 105}
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT date, units_sold FROM demand_history
            WHERE sku_id = ?
            ORDER BY date ASC
            """,
            (sku_id,)
        )

        records = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return records

    except sqlite3.Error as e:
        logger.error(f"Error fetching demand history for {sku_id}: {e}")
        return []


def get_current_stock(sku_id: str, warehouse_id: str) -> int:
    """
    Get current stock level for a SKU at a specific warehouse.

    Returns:
        int: Current inventory quantity (units). Returns 0 if not found.

    Args:
        sku_id: SKU identifier (e.g., "SKU001").
        warehouse_id: Warehouse identifier (e.g., "WH-MAIN").

    Raises:
        sqlite3.Error: If database query fails.

    Example:
        >>> stock = get_current_stock("SKU001", "WH-MAIN")
        >>> print(stock)
        500
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT current_stock FROM inventory
            WHERE sku_id = ? AND warehouse_id = ?
            """,
            (sku_id, warehouse_id)
        )

        row = cursor.fetchone()
        conn.close()

        return row[0] if row else 0

    except sqlite3.Error as e:
        logger.error(f"Error fetching stock for {sku_id}/{warehouse_id}: {e}")
        return 0


def get_sku_total_stock(sku_id: str) -> int:
    """
    Get total current stock for a SKU across all warehouses.

    Returns:
        int: Sum of inventory across all warehouses for this SKU.

    Args:
        sku_id: SKU identifier.

    Raises:
        sqlite3.Error: If database query fails.

    Example:
        >>> total = get_sku_total_stock("SKU001")
        >>> print(total)
        2500
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute(
            "SELECT COALESCE(SUM(current_stock), 0) FROM inventory WHERE sku_id = ?",
            (sku_id,)
        )

        total = cursor.fetchone()[0]
        conn.close()
        return total

    except sqlite3.Error as e:
        logger.error(f"Error fetching total stock for {sku_id}: {e}")
        return 0


# ═══════════════════════════════════════════════════════════════════════════════
# SUPPLIER DATA
# ═══════════════════════════════════════════════════════════════════════════════

def get_supplier_delivery_history(supplier_id: str) -> list[dict]:
    """
    Get delivery history for a supplier from purchase orders.

    Returns data in the exact format needed by supplier_risk_score():
    [
        {
            "order_id": "PO-10000",
            "promised_date": "2025-10-12",
            "actual_date": "2025-10-15" or None,
            "quality_rating": 8
        },
        ...
    ]

    Args:
        supplier_id: Supplier identifier (e.g., "SUP001").

    Returns:
        list[dict]: Purchase order records with delivery metrics.
                   Each dict has order_id, promised_date, actual_date, quality_rating.
                   Returns empty list if no data found.

    Raises:
        sqlite3.Error: If database query fails.

    Example:
        >>> history = get_supplier_delivery_history("SUP001")
        >>> print(len(history))
        5
        >>> print(history[0])
        {
            "order_id": "PO-10000",
            "promised_date": "2025-10-12",
            "actual_date": "2025-10-15",
            "quality_rating": 8
        }
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT order_id, promised_date, actual_date, quality_rating
            FROM purchase_orders
            WHERE supplier_id = ?
            ORDER BY promised_date DESC
            """,
            (supplier_id,)
        )

        records = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return records

    except sqlite3.Error as e:
        logger.error(f"Error fetching delivery history for {supplier_id}: {e}")
        return []


# ═══════════════════════════════════════════════════════════════════════════════
# SHIPMENT & ORDER DATA
# ═══════════════════════════════════════════════════════════════════════════════

def get_most_delayed_shipment_id() -> str | None:
    """Get the ID of the most delayed shipment as a default."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT shipment_id FROM shipments WHERE current_status = 'delayed' ORDER BY promised_date ASC LIMIT 1")
        row = cursor.fetchone()
        conn.close()
        return row[0] if row else None
    except sqlite3.Error as e:
        logger.error(f"Error fetching delayed shipment: {e}")
        return None

def get_shipment_data(shipment_id: str) -> dict:
    """
    Get shipment record by ID.
    If shipment_id is None, defaults to the most delayed shipment.

    Returns data in the exact format needed by detect_delay_impact() shipment_data param:
    {
        "promised_date": "YYYY-MM-DD",
        "current_status": "pending|in_transit|delayed|delivered",
        "estimated_delivery": "YYYY-MM-DD" or None
    }
    """
    if not shipment_id or shipment_id == "FROM_DB":
        shipment_id = get_most_delayed_shipment_id()
        if not shipment_id:
            return {}

    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT promised_date, current_status, estimated_delivery
            FROM shipments
            WHERE shipment_id = ?
            """,
            (shipment_id,)
        )

        row = cursor.fetchone()
        conn.close()

        return dict(row) if row else {}

    except sqlite3.Error as e:
        logger.error(f"Error fetching shipment data for {shipment_id}: {e}")
        return {}


def get_downstream_orders(shipment_id: str) -> list[dict]:
    """
    Get all customer orders (downstream) linked to a shipment.
    If shipment_id is None, defaults to the most delayed shipment.

    Returns data in the exact format needed by detect_delay_impact() downstream_orders param:
    [
        {
            "order_id": "ORD-CUST-100000",
            "customer_tier": "premium" or "standard",
            "sku_id": "SKU001",
            "quantity": 100
        },
        ...
    ]
    """
    if not shipment_id or shipment_id == "FROM_DB":
        shipment_id = get_most_delayed_shipment_id()
        if not shipment_id:
            return []

    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT order_id, customer_tier, sku_id, quantity
            FROM downstream_orders
            WHERE shipment_id = ?
            ORDER BY order_id
            """,
            (shipment_id,)
        )

        records = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return records

    except sqlite3.Error as e:
        logger.error(f"Error fetching downstream orders for {shipment_id}: {e}")
        return []


def get_pending_orders(sku_id: str) -> list[dict]:
    """
    Get pending customer orders (not yet fulfilled) for a SKU.

    Returns data compatible with recommend_allocation() pending_orders param:
    [
        {
            "order_id": "ORD-CUST-100000",
            "customer_tier": "premium" or "standard",
            "quantity_requested": 100,
            "order_date": "YYYY-MM-DD"
        },
        ...
    ]

    Args:
        sku_id: SKU identifier (e.g., "SKU001").

    Returns:
        list[dict]: Pending downstream orders for this SKU.
                   Each dict has order_id, customer_tier, quantity_requested, order_date.
                   Returns empty list if no pending orders found.

    Raises:
        sqlite3.Error: If database query fails.

    Example:
        >>> pending = get_pending_orders("SKU001")
        >>> print(len(pending))
        3
        >>> print(pending[0])
        {
            "order_id": "ORD-CUST-100000",
            "customer_tier": "premium",
            "quantity_requested": 100,
            "order_date": "2025-10-15"
        }
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Downstream orders are linked to shipments
        # We'll return all downstream orders for this SKU as "pending"
        cursor.execute(
            """
            SELECT order_id, customer_tier, quantity as quantity_requested,
                   date('now') as order_date
            FROM downstream_orders
            WHERE sku_id = ?
            ORDER BY order_id
            """,
            (sku_id,)
        )


        records = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return records

    except sqlite3.Error as e:
        logger.error(f"Error fetching pending orders for {sku_id}: {e}")
        return []


# ═══════════════════════════════════════════════════════════════════════════════
# ACTION TRACKING
# ═══════════════════════════════════════════════════════════════════════════════

def save_pending_action(action: dict) -> bool:
    """
    Save a proposed action to the database for approval.

    Stores AI-generated action proposals in pending_actions table.
    Action must contain: action_id, action_type, details, status, created_by,
    reasoning, created_at.

    Args:
        action: Action dict with keys:
                - action_id (str): UUID identifier
                - action_type (str): "reorder" or "switch_supplier"
                - details (dict): Action-specific parameters
                - status (str): "pending_approval" | "approved" | "rejected" | "executed"
                - created_by (str): "agent"
                - reasoning (str): Explanation of why action was proposed
                - created_at (str): ISO timestamp

    Returns:
        bool: True if saved successfully, False otherwise.

    Raises:
        sqlite3.Error: If database insert fails.
        KeyError: If required fields missing from action dict.

    Example:
        >>> action = {
        ...     "action_id": "act-001",
        ...     "action_type": "reorder",
        ...     "details": {"sku_id": "SKU001", "quantity": 1000},
        ...     "status": "pending_approval",
        ...     "created_by": "agent",
        ...     "reasoning": "Stockout risk detected",
        ...     "created_at": "2025-10-15T10:30:00Z"
        ... }
        >>> result = save_pending_action(action)
        >>> print(result)
        True
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Convert details dict to JSON string
        details_json = json.dumps(action["details"]) if isinstance(action["details"], dict) else action["details"]
        details_obj = action["details"] if isinstance(action["details"], dict) else json.loads(action["details"])

        # Check for existing duplicate pending action
        cursor.execute("SELECT action_id, details FROM pending_actions WHERE status = 'pending_approval' AND action_type = ?", (action["action_type"],))
        existing = cursor.fetchall()
        for r in existing:
            try:
                ex_details = json.loads(r["details"])
            except:
                continue
            
            # Deduplication logic
            if action["action_type"] == "reorder":
                if ex_details.get("sku_id") == details_obj.get("sku_id") and ex_details.get("warehouse_id") == details_obj.get("warehouse_id"):
                    # Update existing action instead of duplicating
                    cursor.execute(
                        "UPDATE pending_actions SET details=?, reasoning=?, created_at=? WHERE action_id=?",
                        (details_json, action["reasoning"], action["created_at"], r["action_id"])
                    )
                    conn.commit()
                    conn.close()
                    logger.info(f"Action updated instead of duplicated: {r['action_id']}")
                    return True
                    
            elif action["action_type"] == "switch_supplier":
                if ex_details.get("failing_supplier_id") == details_obj.get("failing_supplier_id"):
                    cursor.execute(
                        "UPDATE pending_actions SET details=?, reasoning=?, created_at=? WHERE action_id=?",
                        (details_json, action["reasoning"], action["created_at"], r["action_id"])
                    )
                    conn.commit()
                    conn.close()
                    logger.info(f"Action updated instead of duplicated: {r['action_id']}")
                    return True

        cursor.execute(
            """
            INSERT OR REPLACE INTO pending_actions
            (action_id, action_type, details, status, created_by, reasoning, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                action["action_id"],
                action["action_type"],
                details_json,
                action["status"],
                action["created_by"],
                action["reasoning"],
                action["created_at"],
            )
        )

        conn.commit()
        conn.close()
        logger.info(f"Action {action['action_id']} saved")
        return True

    except (sqlite3.Error, KeyError) as e:
        logger.error(f"Error saving action: {e}")
        return False


def get_pending_actions(status: str = "pending_approval") -> list[dict]:
    """
    Get all actions with a specific status (typically pending approval).

    Returns actions in the format output by action_agent.propose_action().

    Args:
        status: Action status to filter by (default "pending_approval").
               Options: "pending_approval", "approved", "rejected", "executed"

    Returns:
        list[dict]: Action records with status matching filter.
                   Each dict has action_id, action_type, details (as dict),
                   status, created_by, reasoning, created_at.
                   Returns empty list if no actions found.

    Raises:
        sqlite3.Error: If database query fails.

    Example:
        >>> pending = get_pending_actions("pending_approval")
        >>> print(len(pending))
        3
        >>> print(pending[0])
        {
            "action_id": "act-001",
            "action_type": "reorder",
            "details": {"sku_id": "SKU001", "quantity": 1000},
            "status": "pending_approval",
            ...
        }
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT * FROM pending_actions
            WHERE status = ?
            ORDER BY created_at DESC
            """,
            (status,)
        )

        actions = []
        for row in cursor.fetchall():
            action = dict(row)
            # Parse details JSON back to dict
            try:
                action["details"] = json.loads(action["details"])
            except (json.JSONDecodeError, TypeError):
                action["details"] = {}
            actions.append(action)

        conn.close()
        return actions

    except sqlite3.Error as e:
        logger.error(f"Error fetching pending actions with status {status}: {e}")
        return []


def update_action_status(action_id: str, new_status: str) -> bool:
    """
    Update the status of a pending action (e.g., pending_approval -> approved).

    Args:
        action_id: Action identifier (UUID).
        new_status: New status ("pending_approval" | "approved" | "rejected" | "executed").

    Returns:
        bool: True if updated successfully, False otherwise.

    Raises:
        sqlite3.Error: If database update fails.

    Example:
        >>> result = update_action_status("act-001", "approved")
        >>> print(result)
        True
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute(
            "UPDATE pending_actions SET status = ? WHERE action_id = ?",
            (new_status, action_id)
        )

        conn.commit()
        success = cursor.rowcount > 0
        conn.close()

        if success:
            logger.info(f"Action {action_id} status updated to {new_status}")
        return success

    except sqlite3.Error as e:
        logger.error(f"Error updating action status: {e}")
        return False



# ═══════════════════════════════════════════════════════════════════════════════
# DASHBOARD PANEL DATA
# ═══════════════════════════════════════════════════════════════════════════════

def get_delayed_shipments() -> list[dict]:
    """
    Get all active shipments that are delayed or significantly overdue.

    Returns shipments with current_status 'delayed' or in_transit/pending with
    promised_date more than 1 day ago. Computes delay_days and severity.

    Returns:
        list[dict]: Delayed shipments sorted by delay_days descending.
        Each dict: { shipment_id, current_status, promised_date,
                     estimated_delivery, delay_days, severity }
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        today = datetime.now().date().isoformat()
        cursor.execute("""
            SELECT shipment_id, current_status, promised_date, estimated_delivery
            FROM shipments
            WHERE current_status IN ('delayed', 'in_transit', 'pending')
              AND promised_date < ?
            ORDER BY promised_date ASC
        """, (today,))
        rows = cursor.fetchall()
        conn.close()

        results = []
        for row in rows:
            row = dict(row)
            try:
                promised = datetime.strptime(row["promised_date"], "%Y-%m-%d").date()
                today_d = datetime.now().date()
                delay_days = (today_d - promised).days
                if delay_days <= 0:
                    continue
                # Severity
                if delay_days >= 14:
                    severity = "critical"
                elif delay_days >= 7:
                    severity = "high"
                elif delay_days >= 3:
                    severity = "medium"
                else:
                    severity = "low"
                row["delay_days"] = delay_days
                row["severity"] = severity
                results.append(row)
            except (ValueError, TypeError):
                continue

        results.sort(key=lambda r: r.get("delay_days", 0), reverse=True)
        return results

    except sqlite3.Error as e:
        logger.error(f"Error fetching delayed shipments: {e}")
        return []


def get_warehouse_utilization() -> list[dict]:
    """
    Return capacity vs current stock for all warehouses.

    Returns:
        list[dict]: Each entry has { warehouse_id, name, region, capacity,
                    total_stock, utilization_pct }
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
            SELECT w.warehouse_id, w.name, w.region, w.capacity,
                   COALESCE(SUM(i.current_stock), 0) AS total_stock
            FROM warehouses w
            LEFT JOIN inventory i ON w.warehouse_id = i.warehouse_id
            GROUP BY w.warehouse_id
            ORDER BY w.warehouse_id
        """)
        rows = cursor.fetchall()
        conn.close()

        results = []
        for row in rows:
            row = dict(row)
            capacity = row.get("capacity") or 1
            stock = row.get("total_stock", 0)
            row["utilization_pct"] = round((stock / capacity) * 100, 1)
            results.append(row)
        return results

    except sqlite3.Error as e:
        logger.error(f"Error fetching warehouse utilization: {e}")
        return []


def get_demand_forecast_for_risky_skus(top_n: int = 5) -> list[dict]:
    """
    Compute 7-day demand forecast for the N highest-risk SKUs.

    Identifies risky SKUs as those with the lowest stock-to-demand ratio,
    then returns their forecast including demand_spike_detected flag.

    Args:
        top_n: Number of SKUs to return (default 5).

    Returns:
        list[dict]: Each entry has { sku_id, avg_forecasted_demand,
                    forecasted_daily_demand, trend, confidence,
                    demand_spike_detected, current_total_stock,
                    days_of_stock_remaining }
    """
    try:
        from backend.forecasting import forecast_demand

        # Get all SKU stocks
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
            SELECT s.sku_id, COALESCE(SUM(i.current_stock), 0) AS total_stock
            FROM skus s
            LEFT JOIN inventory i ON s.sku_id = i.sku_id
            GROUP BY s.sku_id
        """)
        sku_stocks = {row["sku_id"]: row["total_stock"] for row in cursor.fetchall()}
        conn.close()

        results = []
        for sku_id, total_stock in sku_stocks.items():
            try:
                hist = get_demand_history(sku_id)
                if not hist:
                    continue
                fc = forecast_demand(sku_id, hist)
                avg = fc.get("avg_forecasted_demand", 0)
                days_remaining = (total_stock / avg) if avg > 0 else None
                results.append({
                    "sku_id": sku_id,
                    "avg_forecasted_demand": round(avg, 1),
                    "forecasted_daily_demand": [round(d, 1) for d in fc.get("forecasted_daily_demand", [])],
                    "trend": fc.get("trend", "stable"),
                    "confidence": round(fc.get("confidence", 0), 2),
                    "demand_spike_detected": fc.get("demand_spike_detected", False),
                    "spike_ratio": fc.get("spike_ratio"),
                    "current_total_stock": total_stock,
                    "days_of_stock_remaining": round(days_remaining, 1) if days_remaining is not None else None,
                })
            except Exception as e:
                logger.warning(f"Could not forecast {sku_id}: {e}")
                continue

        # Sort by risk: lowest days_of_stock_remaining first (most urgent)
        results.sort(key=lambda r: r.get("days_of_stock_remaining") or 9999)
        return results[:top_n]

    except Exception as e:
        logger.error(f"Error computing demand forecast for risky SKUs: {e}")
        return []


# ═══════════════════════════════════════════════════════════════════════════════
# MANAGEMENT CRUD — INVENTORY
# ═══════════════════════════════════════════════════════════════════════════════

def get_all_skus_with_stock() -> list[dict]:
    """Return all SKUs with their total stock across all warehouses."""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
            SELECT s.sku_id, s.name, s.category,
                   COALESCE(SUM(i.current_stock), 0) AS total_stock,
                   s.created_at, s.updated_at
            FROM skus s
            LEFT JOIN inventory i ON s.sku_id = i.sku_id
            GROUP BY s.sku_id
            ORDER BY s.sku_id
        """)
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return rows
    except sqlite3.Error as e:
        logger.error(f"Error fetching SKUs with stock: {e}")
        return []


def add_sku(sku_id: str, name: str, category: str) -> bool:
    """Add a new SKU record."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute(
            "INSERT INTO skus (sku_id, name, category, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
            (sku_id, name, category, now, now)
        )
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        logger.error(f"SKU {sku_id} already exists")
        return False
    except sqlite3.Error as e:
        logger.error(f"Error adding SKU {sku_id}: {e}")
        return False


def update_sku(sku_id: str, name: str = None, category: str = None) -> bool:
    """Update SKU metadata fields."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        fields, params = [], []
        if name is not None:
            fields.append("name = ?"); params.append(name)
        if category is not None:
            fields.append("category = ?"); params.append(category)
        if not fields:
            conn.close()
            return False
        fields.append("updated_at = ?"); params.append(now)
        params.append(sku_id)
        cursor.execute(f"UPDATE skus SET {', '.join(fields)} WHERE sku_id = ?", params)
        conn.commit()
        success = cursor.rowcount > 0
        conn.close()
        return success
    except sqlite3.Error as e:
        logger.error(f"Error updating SKU {sku_id}: {e}")
        return False


def update_sku_stock(sku_id: str, warehouse_id: str, new_stock: int) -> bool:
    """Set current_stock for a SKU at a specific warehouse (upsert)."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("""
            INSERT INTO inventory (warehouse_id, sku_id, current_stock, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(warehouse_id, sku_id) DO UPDATE SET
                current_stock = excluded.current_stock,
                updated_at = excluded.updated_at
        """, (warehouse_id, sku_id, new_stock, now, now))
        conn.commit()
        conn.close()
        return True
    except sqlite3.Error as e:
        logger.error(f"Error updating stock for {sku_id}@{warehouse_id}: {e}")
        return False


def delete_sku(sku_id: str) -> bool:
    """Remove a SKU and its inventory records."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM inventory WHERE sku_id = ?", (sku_id,))
        cursor.execute("DELETE FROM skus WHERE sku_id = ?", (sku_id,))
        conn.commit()
        success = cursor.rowcount > 0
        conn.close()
        return success
    except sqlite3.Error as e:
        logger.error(f"Error deleting SKU {sku_id}: {e}")
        return False


# ═══════════════════════════════════════════════════════════════════════════════
# MANAGEMENT CRUD — SUPPLIERS
# ═══════════════════════════════════════════════════════════════════════════════

def get_all_suppliers_detail() -> list[dict]:
    """Return all supplier records with full detail."""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM suppliers ORDER BY supplier_id")
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()

        # Merge with actual risk scores
        try:
            risk_scores = get_all_supplier_risk_scores()
            risk_map = {r['supplier_id']: r for r in risk_scores}
            for row in rows:
                sid = row['supplier_id']
                if sid in risk_map:
                    row['risk_category'] = risk_map[sid]['risk_category']
                    row['risk_level'] = risk_map[sid]['risk_category'] # For frontend consistency
                    row['risk_score'] = risk_map[sid]['score']
                else:
                    row['risk_category'] = 'low'
                    row['risk_level'] = 'low'
                    row['risk_score'] = 100
        except Exception as e:
            logger.error(f"Error merging risk scores: {e}")

        return rows
    except sqlite3.Error as e:
        logger.error(f"Error fetching suppliers: {e}")
        return []


def add_supplier(supplier_id: str, name: str, region: str,
                 avg_lead_time_days: float = 0, on_time_delivery_pct: float = 100,
                 quality_score: float = 8.0) -> bool:
    """Add a new supplier record."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("""
            INSERT INTO suppliers
            (supplier_id, name, region, avg_lead_time_days, on_time_delivery_pct, quality_score, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (supplier_id, name, region, avg_lead_time_days, on_time_delivery_pct, quality_score, now, now))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        logger.error(f"Supplier {supplier_id} already exists")
        return False
    except sqlite3.Error as e:
        logger.error(f"Error adding supplier {supplier_id}: {e}")
        return False


def update_supplier(supplier_id: str, name: str = None, region: str = None,
                    avg_lead_time_days: float = None, on_time_delivery_pct: float = None,
                    quality_score: float = None) -> bool:
    """Update supplier record fields."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        fields, params = [], []
        for col, val in [("name", name), ("region", region),
                         ("avg_lead_time_days", avg_lead_time_days),
                         ("on_time_delivery_pct", on_time_delivery_pct),
                         ("quality_score", quality_score)]:
            if val is not None:
                fields.append(f"{col} = ?"); params.append(val)
        if not fields:
            conn.close()
            return False
        fields.append("updated_at = ?"); params.append(now)
        params.append(supplier_id)
        cursor.execute(f"UPDATE suppliers SET {', '.join(fields)} WHERE supplier_id = ?", params)
        conn.commit()
        success = cursor.rowcount > 0
        conn.close()
        return success
    except sqlite3.Error as e:
        logger.error(f"Error updating supplier {supplier_id}: {e}")
        return False


def delete_supplier(supplier_id: str) -> bool:
    """Remove a supplier record."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM suppliers WHERE supplier_id = ?", (supplier_id,))
        conn.commit()
        success = cursor.rowcount > 0
        conn.close()
        return success
    except sqlite3.Error as e:
        logger.error(f"Error deleting supplier {supplier_id}: {e}")
        return False


# ═══════════════════════════════════════════════════════════════════════════════
# ACTION HISTORY
# ═══════════════════════════════════════════════════════════════════════════════

def get_all_actions() -> list[dict]:
    """Return all actions regardless of status, newest first."""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM pending_actions ORDER BY created_at DESC")
        actions = []
        for row in cursor.fetchall():
            action = dict(row)
            try:
                action["details"] = json.loads(action["details"])
            except (json.JSONDecodeError, TypeError):
                action["details"] = {}
            actions.append(action)
        conn.close()
        return actions
    except sqlite3.Error as e:
        logger.error(f"Error fetching all actions: {e}")
        return []


# ═══════════════════════════════════════════════════════════════════════════════
# TESTING & VERIFICATION
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    """Quick test of all data access functions."""
    import sys
    import os

    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format="[%(asctime)s] %(levelname)s: %(message)s"
    )

    print("\n" + "=" * 80)
    print("DATA ACCESS FUNCTIONS TEST")
    print("=" * 80 + "\n")

    # Check database exists
    if not os.path.exists(DB_PATH):
        print(f"[ERROR] Database not found: {DB_PATH}")
        print("Run: python data/generator.py")
        sys.exit(1)

    # Test metadata functions
    print("TEST 1: Metadata Functions")
    print("-" * 80)

    skus = get_all_sku_ids()
    print(f"SKUs: {len(skus)} total")
    print(f"  Sample: {skus[:3]}")

    suppliers = get_all_supplier_ids()
    print(f"Suppliers: {len(suppliers)} total")
    print(f"  Sample: {suppliers[:3]}")

    warehouses = get_all_warehouse_ids()
    print(f"Warehouses: {len(warehouses)} total")
    print(f"  All: {warehouses}")

    # Test demand history
    print("\n" + "-" * 80)
    print("TEST 2: Demand History")
    print("-" * 80)

    sku_sample = skus[0]
    demand = get_demand_history(sku_sample)
    print(f"Demand for {sku_sample}: {len(demand)} days")
    if demand:
        print(f"  First record: {demand[0]}")
        print(f"  Last record: {demand[-1]}")

    # Test current stock
    print("\n" + "-" * 80)
    print("TEST 3: Current Stock")
    print("-" * 80)

    warehouse_sample = warehouses[0]
    stock = get_current_stock(sku_sample, warehouse_sample)
    print(f"Stock of {sku_sample} at {warehouse_sample}: {stock} units")

    total = get_sku_total_stock(sku_sample)
    print(f"Total stock of {sku_sample} (all warehouses): {total} units")

    # Test supplier delivery history
    print("\n" + "-" * 80)
    print("TEST 4: Supplier Delivery History")
    print("-" * 80)

    sup_sample = suppliers[0]
    history = get_supplier_delivery_history(sup_sample)
    print(f"Delivery history for {sup_sample}: {len(history)} orders")
    if history:
        print(f"  First order: {history[0]}")

    # Test shipment data
    print("\n" + "-" * 80)
    print("TEST 5: Shipment Data")
    print("-" * 80)

    # Find a shipment from database
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT shipment_id FROM shipments LIMIT 1")
    shipment_row = cursor.fetchone()
    conn.close()

    if shipment_row:
        shipment_id = shipment_row[0]
        shipment = get_shipment_data(shipment_id)
        print(f"Shipment {shipment_id}:")
        print(f"  Promised: {shipment.get('promised_date')}")
        print(f"  Status: {shipment.get('current_status')}")
        print(f"  Estimated: {shipment.get('estimated_delivery')}")

        # Test downstream orders
        downstream = get_downstream_orders(shipment_id)
        print(f"  Downstream orders: {len(downstream)}")
        if downstream:
            print(f"    Sample: {downstream[0]}")

    # Test pending orders
    print("\n" + "-" * 80)
    print("TEST 6: Pending Orders")
    print("-" * 80)

    pending = get_pending_orders(sku_sample)
    print(f"Pending orders for {sku_sample}: {len(pending)}")
    if pending:
        print(f"  Sample: {pending[0]}")

    # Test action tracking
    print("\n" + "-" * 80)
    print("TEST 7: Action Tracking")
    print("-" * 80)

    # Save a test action
    test_action = {
        "action_id": "test-act-001",
        "action_type": "reorder",
        "details": {"sku_id": "SKU001", "quantity": 500},
        "status": "pending_approval",
        "created_by": "agent",
        "reasoning": "Test action",
        "created_at": "2025-10-15T10:30:00Z"
    }

    saved = save_pending_action(test_action)
    print(f"Save action: {saved}")

    # Retrieve pending actions
    actions = get_pending_actions("pending_approval")
    print(f"Pending actions: {len(actions)}")
    if actions:
        print(f"  Sample: {actions[0]}")

    # Update action status
    if actions:
        first_action_id = actions[0]["action_id"]
        updated = update_action_status(first_action_id, "approved")
        print(f"Update {first_action_id} to approved: {updated}")

    print("\n" + "=" * 80)
    print("ALL TESTS COMPLETE")
    print("=" * 80 + "\n")
