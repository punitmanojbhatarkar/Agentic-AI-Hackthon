"""
Synthetic data generator for SupplySense supply chain database.

Generates realistic test data for suppliers, warehouses, SKUs, inventory,
demand history, purchase orders, shipments, and downstream orders.
Suitable for demo, testing, and development environments.
"""

import sqlite3
import logging
from datetime import datetime, timedelta
import random
import json

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# DATA GENERATION CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════════

SUPPLIER_NAMES = [
    ("SUP-RELIABLE-001", "TechSupply Inc", "North America"),
    ("SUP-VENDOR-B", "Global Parts Ltd", "Europe"),
    ("SUP-PARTNER-C", "Asia Logistics Co", "Asia"),
    ("SUP-FAST-SHIP", "Express Suppliers", "North America"),
    ("SUP-QUALITY-X", "Premium Components", "Europe"),
]

WAREHOUSE_NAMES = [
    ("WH-MAIN", "Main Distribution Center", "North America", 50000),
    ("WH-EAST", "Eastern Regional Hub", "North America", 30000),
    ("WH-WEST", "Western Regional Hub", "North America", 25000),
    ("WH-EU", "European Fulfillment", "Europe", 40000),
]

SKU_DATA = [
    ("SKU-WIDGET-100", "Widget Type 100", "Electronics"),
    ("SKU-GADGET-50", "Gadget Type 50", "Electronics"),
    ("SKU-COMPONENT-A", "Component A", "Parts"),
    ("SKU-COMPONENT-B", "Component B", "Parts"),
    ("SKU-ASSEMBLY-X", "Assembly X", "Assemblies"),
    ("SKU-ASSEMBLY-Y", "Assembly Y", "Assemblies"),
    ("SKU-CABLE-USB", "USB Cable", "Accessories"),
    ("SKU-BRACKET-STL", "Steel Bracket", "Hardware"),
]

CUSTOMER_TIERS = ["premium", "standard"]
ORDER_STATUSES = ["pending", "in_transit", "delivered", "delayed"]


# ═══════════════════════════════════════════════════════════════════════════════
# SYNTHETIC DATA GENERATORS
# ═══════════════════════════════════════════════════════════════════════════════

def generate_suppliers() -> list[dict]:
    """
    Generate synthetic supplier data.

    Returns:
        list[dict]: List of supplier records with realistic metrics.
    """
    suppliers = []
    for supplier_id, name, region in SUPPLIER_NAMES:
        supplier = {
            "supplier_id": supplier_id,
            "name": name,
            "region": region,
            "avg_lead_time_days": round(random.uniform(3, 15), 1),
            "on_time_delivery_pct": round(random.uniform(60, 98), 1),
            "quality_score": round(random.uniform(6, 10), 1),
        }
        suppliers.append(supplier)
    return suppliers


def generate_warehouses() -> list[dict]:
    """
    Generate synthetic warehouse data.

    Returns:
        list[dict]: List of warehouse records.
    """
    warehouses = []
    for warehouse_id, name, region, capacity in WAREHOUSE_NAMES:
        warehouse = {
            "warehouse_id": warehouse_id,
            "name": name,
            "region": region,
            "capacity": capacity,
        }
        warehouses.append(warehouse)
    return warehouses


def generate_skus() -> list[dict]:
    """
    Generate synthetic SKU data.

    Returns:
        list[dict]: List of SKU records.
    """
    skus = []
    for sku_id, name, category in SKU_DATA:
        sku = {
            "sku_id": sku_id,
            "name": name,
            "category": category,
        }
        skus.append(sku)
    return skus


def generate_inventory(warehouses: list[dict], skus: list[dict]) -> list[dict]:
    """
    Generate synthetic inventory data (stock levels by warehouse and SKU).

    Args:
        warehouses: List of warehouse records.
        skus: List of SKU records.

    Returns:
        list[dict]: List of inventory records (warehouse_id, sku_id, current_stock).
    """
    inventory = []
    for warehouse in warehouses:
        for sku in skus:
            record = {
                "warehouse_id": warehouse["warehouse_id"],
                "sku_id": sku["sku_id"],
                "current_stock": random.randint(50, 2000),  # Realistic stock levels
            }
            inventory.append(record)
    return inventory


def generate_demand_history(
    skus: list[dict],
    days: int = 90,
    base_date: datetime = None
) -> list[dict]:
    """
    Generate synthetic historical demand data (last N days).

    Args:
        skus: List of SKU records.
        days: Number of historical days to generate (default 90).
        base_date: Reference date (default today). Dates go backward from here.

    Returns:
        list[dict]: List of demand history records (sku_id, date, units_sold).
    """
    if base_date is None:
        base_date = datetime.now()

    demand_history = []
    for sku in skus:
        # Generate demand with trend and seasonality
        base_demand = random.randint(80, 200)
        trend = random.choice([-1, 0, 1])  # -1: decreasing, 0: stable, 1: increasing

        for day_offset in range(days):
            date = base_date - timedelta(days=day_offset)
            date_str = date.strftime("%Y-%m-%d")

            # Add trend and random noise
            daily_demand = base_demand + (trend * day_offset * 0.5) + random.randint(-20, 20)
            daily_demand = max(10, int(daily_demand))  # Ensure positive demand

            record = {
                "sku_id": sku["sku_id"],
                "date": date_str,
                "units_sold": daily_demand,
            }
            demand_history.append(record)

    return demand_history


def generate_purchase_orders(
    suppliers: list[dict],
    skus: list[dict],
    num_orders: int = 50,
    days_back: int = 180
) -> list[dict]:
    """
    Generate synthetic purchase orders from suppliers.

    Args:
        suppliers: List of supplier records.
        skus: List of SKU records.
        num_orders: Number of purchase orders to generate.
        days_back: Days into the past to generate orders.

    Returns:
        list[dict]: List of purchase order records.
    """
    purchase_orders = []
    base_date = datetime.now()

    for i in range(num_orders):
        order_id = f"PO-{1000 + i}"
        supplier = random.choice(suppliers)
        sku = random.choice(skus)

        promised_date = base_date - timedelta(days=random.randint(1, days_back))

        # Some orders are delivered, some not yet
        if random.random() < 0.8:  # 80% delivered
            # Simulate on-time and late deliveries
            if random.random() < supplier["on_time_delivery_pct"] / 100:
                actual_date = promised_date
            else:
                actual_date = promised_date + timedelta(days=random.randint(1, 10))
            actual_date_str = actual_date.strftime("%Y-%m-%d")
        else:
            actual_date_str = None  # Not yet delivered

        order = {
            "order_id": order_id,
            "supplier_id": supplier["supplier_id"],
            "sku_id": sku["sku_id"],
            "quantity": random.randint(100, 1000),
            "promised_date": promised_date.strftime("%Y-%m-%d"),
            "actual_date": actual_date_str,
            "quality_rating": int(random.choice([6, 7, 8, 9, 10])),
        }
        purchase_orders.append(order)

    return purchase_orders


def generate_shipments(purchase_orders: list[dict]) -> list[dict]:
    """
    Generate synthetic shipments corresponding to purchase orders.

    Args:
        purchase_orders: List of purchase order records.

    Returns:
        list[dict]: List of shipment records.
    """
    shipments = []

    for i, po in enumerate(purchase_orders):
        shipment_id = f"SHIP-{5000 + i}"

        # Shipment dates based on PO promised date
        promised_date = datetime.strptime(po["promised_date"], "%Y-%m-%d")

        # Some shipments are on-time, some delayed
        if random.random() < 0.85:  # 85% on-time or early
            estimated_delivery = promised_date
            current_status = random.choice(["pending", "in_transit", "delivered"])
        else:  # 15% delayed
            estimated_delivery = promised_date + timedelta(days=random.randint(1, 5))
            current_status = random.choice(["delayed", "in_transit"])

        shipment = {
            "shipment_id": shipment_id,
            "order_id": po["order_id"],
            "promised_date": po["promised_date"],
            "estimated_delivery": estimated_delivery.strftime("%Y-%m-%d"),
            "current_status": current_status,
        }
        shipments.append(shipment)

    return shipments


def generate_downstream_orders(
    shipments: list[dict],
    skus: list[dict],
    num_orders_per_shipment: int = 3
) -> list[dict]:
    """
    Generate synthetic downstream customer orders dependent on shipments.

    Args:
        shipments: List of shipment records.
        skus: List of SKU records.
        num_orders_per_shipment: Number of downstream orders per shipment.

    Returns:
        list[dict]: List of downstream order records.
    """
    downstream_orders = []
    order_counter = 10000

    for shipment in shipments:
        for _ in range(num_orders_per_shipment):
            order_id = f"ORD-CUST-{order_counter}"
            order_counter += 1

            sku = random.choice(skus)
            customer_tier = random.choice(CUSTOMER_TIERS)

            order = {
                "order_id": order_id,
                "shipment_id": shipment["shipment_id"],
                "customer_tier": customer_tier,
                "sku_id": sku["sku_id"],
                "quantity": random.randint(50, 500),
            }
            downstream_orders.append(order)

    return downstream_orders


# ═══════════════════════════════════════════════════════════════════════════════
# DATABASE POPULATION
# ═══════════════════════════════════════════════════════════════════════════════

def populate_database(conn: sqlite3.Connection, verbose: bool = True) -> dict:
    """
    Populate database with complete synthetic dataset.

    This function generates and inserts all data into the database in the
    correct dependency order (suppliers first, then warehouses, etc.).

    Args:
        conn: Active sqlite3.Connection to initialized database.
        verbose: If True, log insertion progress (default True).

    Returns:
        dict: Summary of inserted records per table.
              {"suppliers": 5, "warehouses": 4, "skus": 8, ...}

    Raises:
        sqlite3.Error: If insertion fails.
    """
    cursor = conn.cursor()
    summary = {}

    try:
        # Generate all data
        if verbose:
            print("Generating synthetic data...")

        suppliers = generate_suppliers()
        warehouses = generate_warehouses()
        skus = generate_skus()
        inventory = generate_inventory(warehouses, skus)
        demand_history = generate_demand_history(skus, days=90)
        purchase_orders = generate_purchase_orders(suppliers, skus, num_orders=50)
        shipments = generate_shipments(purchase_orders)
        downstream_orders = generate_downstream_orders(shipments, skus, num_orders_per_shipment=3)

        if verbose:
            print("Data generated. Inserting into database...\n")

        # =====================================================================
        # Insert suppliers
        # =====================================================================
        if verbose:
            print(f"Inserting {len(suppliers)} suppliers...")
        for supplier in suppliers:
            cursor.execute(
                """
                INSERT OR REPLACE INTO suppliers
                (supplier_id, name, region, avg_lead_time_days, on_time_delivery_pct, quality_score)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    supplier["supplier_id"],
                    supplier["name"],
                    supplier["region"],
                    supplier["avg_lead_time_days"],
                    supplier["on_time_delivery_pct"],
                    supplier["quality_score"],
                )
            )
        summary["suppliers"] = len(suppliers)

        # =====================================================================
        # Insert warehouses
        # =====================================================================
        if verbose:
            print(f"Inserting {len(warehouses)} warehouses...")
        for warehouse in warehouses:
            cursor.execute(
                """
                INSERT OR REPLACE INTO warehouses
                (warehouse_id, name, region, capacity)
                VALUES (?, ?, ?, ?)
                """,
                (
                    warehouse["warehouse_id"],
                    warehouse["name"],
                    warehouse["region"],
                    warehouse["capacity"],
                )
            )
        summary["warehouses"] = len(warehouses)

        # =====================================================================
        # Insert SKUs
        # =====================================================================
        if verbose:
            print(f"Inserting {len(skus)} SKUs...")
        for sku in skus:
            cursor.execute(
                """
                INSERT OR REPLACE INTO skus
                (sku_id, name, category)
                VALUES (?, ?, ?)
                """,
                (sku["sku_id"], sku["name"], sku["category"])
            )
        summary["skus"] = len(skus)

        # =====================================================================
        # Insert inventory
        # =====================================================================
        if verbose:
            print(f"Inserting {len(inventory)} inventory records...")
        for inv in inventory:
            cursor.execute(
                """
                INSERT OR REPLACE INTO inventory
                (warehouse_id, sku_id, current_stock)
                VALUES (?, ?, ?)
                """,
                (inv["warehouse_id"], inv["sku_id"], inv["current_stock"])
            )
        summary["inventory"] = len(inventory)

        # =====================================================================
        # Insert demand history
        # =====================================================================
        if verbose:
            print(f"Inserting {len(demand_history)} demand history records...")
        for demand in demand_history:
            cursor.execute(
                """
                INSERT OR IGNORE INTO demand_history
                (sku_id, date, units_sold)
                VALUES (?, ?, ?)
                """,
                (demand["sku_id"], demand["date"], demand["units_sold"])
            )
        summary["demand_history"] = len(demand_history)

        # =====================================================================
        # Insert purchase orders
        # =====================================================================
        if verbose:
            print(f"Inserting {len(purchase_orders)} purchase orders...")
        for po in purchase_orders:
            cursor.execute(
                """
                INSERT OR REPLACE INTO purchase_orders
                (order_id, supplier_id, sku_id, quantity, promised_date, actual_date, quality_rating)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    po["order_id"],
                    po["supplier_id"],
                    po["sku_id"],
                    po["quantity"],
                    po["promised_date"],
                    po["actual_date"],
                    po["quality_rating"],
                )
            )
        summary["purchase_orders"] = len(purchase_orders)

        # =====================================================================
        # Insert shipments
        # =====================================================================
        if verbose:
            print(f"Inserting {len(shipments)} shipments...")
        for shipment in shipments:
            cursor.execute(
                """
                INSERT OR REPLACE INTO shipments
                (shipment_id, order_id, promised_date, estimated_delivery, current_status)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    shipment["shipment_id"],
                    shipment["order_id"],
                    shipment["promised_date"],
                    shipment["estimated_delivery"],
                    shipment["current_status"],
                )
            )
        summary["shipments"] = len(shipments)

        # =====================================================================
        # Insert downstream orders
        # =====================================================================
        if verbose:
            print(f"Inserting {len(downstream_orders)} downstream orders...")
        for order in downstream_orders:
            cursor.execute(
                """
                INSERT OR REPLACE INTO downstream_orders
                (order_id, shipment_id, customer_tier, sku_id, quantity)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    order["order_id"],
                    order["shipment_id"],
                    order["customer_tier"],
                    order["sku_id"],
                    order["quantity"],
                )
            )
        summary["downstream_orders"] = len(downstream_orders)

        # Commit all insertions
        conn.commit()

        if verbose:
            print("\n" + "=" * 80)
            print("DATABASE POPULATION COMPLETE")
            print("=" * 80)
            print("\nRecords inserted:")
            for table_name, count in summary.items():
                print(f"  {table_name}: {count}")
            print()

        logger.info(f"Database populated successfully: {summary}")
        return summary

    except sqlite3.Error as e:
        logger.error(f"Error populating database: {e}", exc_info=True)
        conn.rollback()
        raise


# ═══════════════════════════════════════════════════════════════════════════════
# TESTING & DEMO
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    """
    Quick test of data generation and population.
    """
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    
    from data.schema import init_db
    import tempfile

    print("\n" + "=" * 80)
    print("SYNTHETIC DATA GENERATION TEST")
    print("=" * 80 + "\n")

    # Create temporary database
    temp_dir = tempfile.mkdtemp()
    temp_db = os.path.join(temp_dir, "test_populated.db")

    try:
        # Initialize and populate
        print(f"Initializing database at: {temp_db}\n")
        conn = init_db(temp_db)
        print()

        summary = populate_database(conn, verbose=True)

        # Verify data
        print("Verification queries:")
        print("-" * 80)

        cursor = conn.cursor()

        # Count suppliers
        cursor.execute("SELECT COUNT(*) FROM suppliers")
        supplier_count = cursor.fetchone()[0]
        print(f"Suppliers in database: {supplier_count}")

        # Count inventory records
        cursor.execute("SELECT COUNT(*) FROM inventory")
        inv_count = cursor.fetchone()[0]
        print(f"Inventory records: {inv_count}")

        # Sample inventory data
        cursor.execute(
            "SELECT warehouse_id, sku_id, current_stock FROM inventory LIMIT 3"
        )
        print("\nSample inventory records:")
        for row in cursor.fetchall():
            print(f"  {row[0]}, {row[1]}: {row[2]} units")

        # Recent demand
        cursor.execute(
            "SELECT sku_id, date, units_sold FROM demand_history ORDER BY date DESC LIMIT 3"
        )
        print("\nRecent demand history:")
        for row in cursor.fetchall():
            print(f"  {row[0]} on {row[1]}: {row[2]} units")

        # Purchase orders
        cursor.execute("SELECT COUNT(*) FROM purchase_orders WHERE actual_date IS NOT NULL")
        delivered_po = cursor.fetchone()[0]
        print(f"\nDelivered purchase orders: {delivered_po}")

        conn.close()
        print("\n" + "=" * 80)
        print("TEST PASSED")
        print("=" * 80 + "\n")

    except Exception as e:
        print(f"\n[FAIL] {str(e)}")
        import traceback
        traceback.print_exc()

    finally:
        # Cleanup
        if os.path.exists(temp_db):
            os.remove(temp_db)
        os.rmdir(temp_dir)
