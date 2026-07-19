"""
Data store interface for SupplySense supply chain database.

Provides high-level access to database data for agents, sweep functions, and
other downstream consumers. Acts as a data access layer (DAL) between the
database schema and business logic.
"""

import sqlite3
import logging
from typing import Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class SupplyChainDataStore:
    """
    Data access layer for SupplySense supply chain database.

    This class provides methods to retrieve data needed by the agent layer
    (forecasting, stockout prediction, supplier risk scoring, etc.) without
    requiring direct SQL knowledge from agents.

    Attributes:
        db_path: Path to SQLite database file.
        conn: Active sqlite3.Connection (lazy-loaded on first use).
    """

    def __init__(self, db_path: str) -> None:
        """
        Initialize data store connection.

        Args:
            db_path: Path to SQLite database file (should already be initialized).
        """
        self.db_path = db_path
        self.conn: Optional[sqlite3.Connection] = None

    def _get_connection(self) -> sqlite3.Connection:
        """
        Get or create database connection (lazy initialization).

        Returns:
            sqlite3.Connection: Active database connection.
        """
        if self.conn is None:
            try:
                self.conn = sqlite3.connect(self.db_path)
                self.conn.row_factory = sqlite3.Row
                logger.debug(f"Database connection opened: {self.db_path}")
            except sqlite3.Error as e:
                logger.error(f"Failed to connect to database: {e}")
                raise
        return self.conn

    def close(self) -> None:
        """Close database connection if open."""
        if self.conn:
            try:
                self.conn.close()
                self.conn = None
                logger.debug("Database connection closed")
            except sqlite3.Error as e:
                logger.error(f"Error closing database connection: {e}")

    # =========================================================================
    # SUPPLIER METHODS
    # =========================================================================

    def get_all_suppliers(self) -> list[str]:
        """
        Get list of all supplier IDs.

        Returns:
            list[str]: List of supplier_id values.
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT supplier_id FROM suppliers ORDER BY supplier_id")
            return [row[0] for row in cursor.fetchall()]
        except sqlite3.Error as e:
            logger.error(f"Error fetching supplier list: {e}")
            return []

    def get_supplier(self, supplier_id: str) -> Optional[dict]:
        """
        Get supplier record by ID.

        Args:
            supplier_id: Supplier identifier.

        Returns:
            dict: Supplier record with all fields, or None if not found.
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM suppliers WHERE supplier_id = ?", (supplier_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
        except sqlite3.Error as e:
            logger.error(f"Error fetching supplier {supplier_id}: {e}")
            return None

    def get_delivery_history(self, supplier_id: str) -> list[dict]:
        """
        Get delivery history for a supplier (from purchase orders).

        Args:
            supplier_id: Supplier identifier.

        Returns:
            list[dict]: List of delivery records with fields:
                       order_id, promised_date, actual_date, quality_rating
        """
        try:
            conn = self._get_connection()
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
            return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            logger.error(f"Error fetching delivery history for {supplier_id}: {e}")
            return []

    # =========================================================================
    # SKU METHODS
    # =========================================================================

    def get_all_skus(self) -> list[str]:
        """
        Get list of all SKU IDs.

        Returns:
            list[str]: List of sku_id values.
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT sku_id FROM skus ORDER BY sku_id")
            return [row[0] for row in cursor.fetchall()]
        except sqlite3.Error as e:
            logger.error(f"Error fetching SKU list: {e}")
            return []

    def get_sku(self, sku_id: str) -> Optional[dict]:
        """
        Get SKU record by ID.

        Args:
            sku_id: SKU identifier.

        Returns:
            dict: SKU record with all fields, or None if not found.
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM skus WHERE sku_id = ?", (sku_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
        except sqlite3.Error as e:
            logger.error(f"Error fetching SKU {sku_id}: {e}")
            return None

    # =========================================================================
    # WAREHOUSE METHODS
    # =========================================================================

    def get_all_warehouses(self) -> list[str]:
        """
        Get list of all warehouse IDs.

        Returns:
            list[str]: List of warehouse_id values.
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT warehouse_id FROM warehouses ORDER BY warehouse_id")
            return [row[0] for row in cursor.fetchall()]
        except sqlite3.Error as e:
            logger.error(f"Error fetching warehouse list: {e}")
            return []

    def get_warehouse_ids(self) -> list[str]:
        """
        Alias for get_all_warehouses() (used by sweep agent).

        Returns:
            list[str]: List of warehouse IDs.
        """
        return self.get_all_warehouses()

    def get_warehouse(self, warehouse_id: str) -> Optional[dict]:
        """
        Get warehouse record by ID.

        Args:
            warehouse_id: Warehouse identifier.

        Returns:
            dict: Warehouse record with all fields, or None if not found.
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM warehouses WHERE warehouse_id = ?", (warehouse_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
        except sqlite3.Error as e:
            logger.error(f"Error fetching warehouse {warehouse_id}: {e}")
            return None

    # =========================================================================
    # INVENTORY METHODS
    # =========================================================================

    def get_current_stock(self, sku_id: str, warehouse_id: str) -> int:
        """
        Get current stock level for a SKU at a warehouse.

        Args:
            sku_id: SKU identifier.
            warehouse_id: Warehouse identifier.

        Returns:
            int: Current stock quantity (0 if not found).
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT current_stock FROM inventory WHERE sku_id = ? AND warehouse_id = ?",
                (sku_id, warehouse_id)
            )
            row = cursor.fetchone()
            return row[0] if row else 0
        except sqlite3.Error as e:
            logger.error(f"Error fetching stock for {sku_id}/{warehouse_id}: {e}")
            return 0

    def get_warehouse_inventory(self, warehouse_id: str) -> dict:
        """
        Get all inventory for a warehouse (SKU -> stock level).

        Args:
            warehouse_id: Warehouse identifier.

        Returns:
            dict: Mapping {sku_id: current_stock}
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT sku_id, current_stock FROM inventory WHERE warehouse_id = ?",
                (warehouse_id,)
            )
            return {row[0]: row[1] for row in cursor.fetchall()}
        except sqlite3.Error as e:
            logger.error(f"Error fetching warehouse inventory for {warehouse_id}: {e}")
            return {}

    def update_stock(self, sku_id: str, warehouse_id: str, new_quantity: int) -> bool:
        """
        Update stock level (useful for simulation or post-fulfillment updates).

        Args:
            sku_id: SKU identifier.
            warehouse_id: Warehouse identifier.
            new_quantity: New stock quantity.

        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE inventory SET current_stock = ? 
                WHERE sku_id = ? AND warehouse_id = ?
                """,
                (new_quantity, sku_id, warehouse_id)
            )
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            logger.error(f"Error updating stock: {e}")
            return False

    # =========================================================================
    # DEMAND HISTORY METHODS
    # =========================================================================

    def get_forecast(self, sku_id: str, days: int = 90) -> Optional[dict]:
        """
        Get historical demand data for demand forecasting.

        This method retrieves the last N days of demand history for a SKU
        and calls forecast_demand to compute the forecast result (with
        avg_forecasted_demand, trend, confidence).

        Args:
            sku_id: SKU identifier.
            days: Number of historical days to retrieve (default 90).

        Returns:
            dict: Output dict from forecast_demand() containing:
                  {
                      "sku_id": str,
                      "trend": str,
                      "forecasted_daily_demand": [float, ...],
                      "avg_forecasted_demand": float,
                      "confidence": float
                  }
                  Or None if no data found.
        """
        try:
            from backend.forecasting import forecast_demand as forecast_func
            
            conn = self._get_connection()
            cursor = conn.cursor()

            # Get last N days of demand
            cursor.execute(
                """
                SELECT date, units_sold FROM demand_history
                WHERE sku_id = ?
                ORDER BY date ASC
                LIMIT ?
                """,
                (sku_id, days)
            )

            demand_data = [
                {"date": row[0], "units_sold": row[1]}
                for row in cursor.fetchall()
            ]

            if not demand_data:
                logger.warning(f"No demand history found for {sku_id}")
                return None

            # Call forecast_demand to compute forecast
            try:
                forecast_result = forecast_func(sku_id, demand_data)
                return forecast_result
            except Exception as e:
                logger.error(f"Error computing forecast for {sku_id}: {e}")
                return None

        except sqlite3.Error as e:
            logger.error(f"Error fetching forecast data for {sku_id}: {e}")
            return None

    def get_demand_history(self, sku_id: str, days: int = 90) -> list[dict]:
        """
        Get raw demand history data (alias for internal use).

        Args:
            sku_id: SKU identifier.
            days: Number of historical days.

        Returns:
            list[dict]: List of {date, units_sold} dicts.
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT date, units_sold FROM demand_history
                WHERE sku_id = ?
                ORDER BY date ASC
                LIMIT ?
                """,
                (sku_id, days)
            )
            return [{"date": row[0], "units_sold": row[1]} for row in cursor.fetchall()]
        except sqlite3.Error as e:
            logger.error(f"Error fetching demand history for {sku_id}: {e}")
            return []

    def add_demand_record(self, sku_id: str, date: str, units_sold: int) -> bool:
        """
        Add a demand record (for simulation or manual entry).

        Args:
            sku_id: SKU identifier.
            date: Date in YYYY-MM-DD format.
            units_sold: Units sold on that date.

        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT OR REPLACE INTO demand_history (sku_id, date, units_sold)
                VALUES (?, ?, ?)
                """,
                (sku_id, date, units_sold)
            )
            conn.commit()
            return True
        except sqlite3.Error as e:
            logger.error(f"Error adding demand record: {e}")
            return False

    # =========================================================================
    # PURCHASE ORDER METHODS
    # =========================================================================

    def get_purchase_order(self, order_id: str) -> Optional[dict]:
        """
        Get a purchase order by ID.

        Args:
            order_id: Purchase order identifier.

        Returns:
            dict: Purchase order record, or None if not found.
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM purchase_orders WHERE order_id = ?", (order_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
        except sqlite3.Error as e:
            logger.error(f"Error fetching purchase order {order_id}: {e}")
            return None

    def get_pending_purchase_orders(self, supplier_id: Optional[str] = None) -> list[dict]:
        """
        Get undelivered purchase orders (actual_date IS NULL).

        Args:
            supplier_id: Optional filter by supplier.

        Returns:
            list[dict]: List of pending purchase order records.
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            if supplier_id:
                cursor.execute(
                    """
                    SELECT * FROM purchase_orders
                    WHERE actual_date IS NULL AND supplier_id = ?
                    ORDER BY promised_date ASC
                    """,
                    (supplier_id,)
                )
            else:
                cursor.execute(
                    """
                    SELECT * FROM purchase_orders
                    WHERE actual_date IS NULL
                    ORDER BY promised_date ASC
                    """
                )

            return [dict(row) for row in cursor.fetchall()]

        except sqlite3.Error as e:
            logger.error(f"Error fetching pending purchase orders: {e}")
            return []

    # =========================================================================
    # SHIPMENT METHODS
    # =========================================================================

    def get_shipment(self, shipment_id: str) -> Optional[dict]:
        """
        Get a shipment record by ID.

        Args:
            shipment_id: Shipment identifier.

        Returns:
            dict: Shipment record, or None if not found.
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM shipments WHERE shipment_id = ?", (shipment_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
        except sqlite3.Error as e:
            logger.error(f"Error fetching shipment {shipment_id}: {e}")
            return None

    def get_shipment_downstream_orders(self, shipment_id: str) -> list[dict]:
        """
        Get all downstream customer orders for a shipment.

        Args:
            shipment_id: Shipment identifier.

        Returns:
            list[dict]: List of downstream order records.
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT order_id, customer_tier, sku_id, quantity
                FROM downstream_orders
                WHERE shipment_id = ?
                """,
                (shipment_id,)
            )
            return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            logger.error(f"Error fetching downstream orders for {shipment_id}: {e}")
            return []

    # =========================================================================
    # ACTION METHODS
    # =========================================================================

    def save_action(self, action: dict) -> bool:
        """
        Save a proposed action to pending_actions table.

        Args:
            action: Action dict from action_agent.propose_action()
                   Must contain: action_id, action_type, details (dict), status,
                   created_by, reasoning, created_at

        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            import json
            conn = self._get_connection()
            cursor = conn.cursor()

            # Convert details dict to JSON string
            details_json = json.dumps(action["details"])

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
            logger.info(f"Action {action['action_id']} saved")
            return True
        except Exception as e:
            logger.error(f"Error saving action: {e}")
            return False

    def get_pending_actions(self) -> list[dict]:
        """
        Get all pending actions (status = pending_approval).

        Returns:
            list[dict]: List of pending action records.
        """
        try:
            import json
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM pending_actions
                WHERE status = 'pending_approval'
                ORDER BY created_at DESC
                """
            )
            actions = []
            for row in cursor.fetchall():
                action = dict(row)
                # Parse details JSON
                try:
                    action["details"] = json.loads(action["details"])
                except json.JSONDecodeError:
                    action["details"] = {}
                actions.append(action)
            return actions
        except sqlite3.Error as e:
            logger.error(f"Error fetching pending actions: {e}")
            return []

    def update_action_status(self, action_id: str, new_status: str) -> bool:
        """
        Update action status (e.g., pending_approval -> approved).

        Args:
            action_id: Action identifier.
            new_status: New status (pending_approval, approved, rejected, executed).

        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE pending_actions SET status = ? WHERE action_id = ?",
                (new_status, action_id)
            )
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            logger.error(f"Error updating action status: {e}")
            return False

    # =========================================================================
    # INTROSPECTION & HEALTH
    # =========================================================================

    def get_database_stats(self) -> dict:
        """
        Get summary statistics about the database.

        Returns:
            dict: {
                "suppliers": count,
                "warehouses": count,
                "skus": count,
                "inventory_records": count,
                "demand_history_records": count,
                "purchase_orders": count,
                "shipments": count,
                "downstream_orders": count,
                "pending_actions": count
            }
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            stats = {}
            tables = [
                "suppliers", "warehouses", "skus", "inventory",
                "demand_history", "purchase_orders", "shipments",
                "downstream_orders", "pending_actions"
            ]

            for table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                stats[table] = cursor.fetchone()[0]

            return stats

        except sqlite3.Error as e:
            logger.error(f"Error fetching database stats: {e}")
            return {}

    def is_healthy(self) -> bool:
        """
        Check if database is accessible and responsive.

        Returns:
            bool: True if database is healthy, False otherwise.
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM suppliers")
            cursor.fetchone()
            return True
        except sqlite3.Error as e:
            logger.error(f"Database health check failed: {e}")
            return False


# ═══════════════════════════════════════════════════════════════════════════════
# TESTING
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    """Quick test of data store interface."""
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

    from data.schema import init_db
    from data.generators import populate_database
    import tempfile

    print("\n" + "=" * 80)
    print("DATA STORE INTERFACE TEST")
    print("=" * 80 + "\n")

    temp_dir = tempfile.mkdtemp()
    temp_db = os.path.join(temp_dir, "test_datastore.db")

    try:
        # Initialize and populate database
        print("Setting up test database...")
        conn = init_db(temp_db)
        populate_database(conn, verbose=False)
        conn.close()
        print("[OK] Database ready\n")

        # Create data store
        store = SupplyChainDataStore(temp_db)

        # Test suppliers
        print("Testing supplier access:")
        suppliers = store.get_all_suppliers()
        print(f"  Found {len(suppliers)} suppliers: {suppliers[:2]}")

        supplier = store.get_supplier(suppliers[0])
        print(f"  Sample supplier: {supplier['name']} ({supplier['region']})")

        delivery_hist = store.get_delivery_history(suppliers[0])
        print(f"  Delivery history: {len(delivery_hist)} orders\n")

        # Test SKUs
        print("Testing SKU access:")
        skus = store.get_all_skus()
        print(f"  Found {len(skus)} SKUs")

        # Test inventory
        print("\nTesting inventory access:")
        warehouses = store.get_all_warehouses()
        stock = store.get_current_stock(skus[0], warehouses[0])
        print(f"  {skus[0]} at {warehouses[0]}: {stock} units")

        # Test demand forecast
        print("\nTesting demand access:")
        forecast = store.get_forecast(skus[0], days=30)
        if forecast:
            print(f"  Forecast data for {skus[0]}: {len(forecast['demand_data'])} days")
            print(f"  Sample: {forecast['demand_data'][0]}")

        # Test database stats
        print("\nDatabase statistics:")
        stats = store.get_database_stats()
        for table, count in stats.items():
            print(f"  {table}: {count}")

        # Test health
        print("\nHealth check:")
        health = store.is_healthy()
        print(f"  Database healthy: {health}")

        store.close()

        print("\n" + "=" * 80)
        print("TEST PASSED")
        print("=" * 80 + "\n")

    except Exception as e:
        print(f"\n[FAIL] {str(e)}")
        import traceback
        traceback.print_exc()

    finally:
        if os.path.exists(temp_db):
            os.remove(temp_db)
        os.rmdir(temp_dir)
