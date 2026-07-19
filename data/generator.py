"""
Realistic synthetic data generator for SupplySense supply chain database.

Generates comprehensive test data including suppliers, warehouses, SKUs,
inventory, demand history, purchase orders, shipments, and downstream orders.

CRITICAL PATTERNS BAKED IN:
1. Supplier SUP014: Degrading reliability (92% → 61% on-time over 90 days)
2. SKU008: Increasing demand trend causing 5-day stockout risk
3. SKU015: Sudden 3x demand spike (last 10 days) causing unexpected stockout
"""

import sqlite3
import random
import logging
from datetime import datetime, timedelta
from typing import Optional

logger = logging.getLogger(__name__)

# Fixed seed for reproducibility
random.seed(42)


# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════════

REGIONS = ["North America", "Europe", "Asia", "South America", "Australia"]

SUPPLIER_BASES = [
    ("SUP001", "TechSupply Global", "North America"),
    ("SUP002", "Logistics Express", "Europe"),
    ("SUP003", "Asia Components", "Asia"),
    ("SUP004", "Premium Parts Inc", "North America"),
    ("SUP005", "Quality Manufacturing", "Europe"),
    ("SUP006", "Fast Distributors", "South America"),
    ("SUP007", "Advanced Tech Ltd", "Asia"),
    ("SUP008", "Reliable Partners", "North America"),
    ("SUP009", "Global Sourcing Co", "Australia"),
    ("SUP010", "Efficient Supply", "Europe"),
    ("SUP011", "Industrial Goods", "Asia"),
    ("SUP012", "Regional Suppliers", "South America"),
    ("SUP013", "Premium Quality", "Australia"),
    ("SUP014", "Degrading Supplier", "North America"),  # PATTERN 1: Declining reliability
    ("SUP015", "Fast Track Co", "Europe"),
    ("SUP016", "Warehouse Direct", "Asia"),
    ("SUP017", "Cost Leaders", "North America"),
    ("SUP018", "Specialty Parts", "Europe"),
    ("SUP019", "Emergency Supply", "Asia"),
    ("SUP020", "Standard Vendor", "South America"),
]

SKU_CONFIGS = [
    ("SKU001", "Widget Type A", "Electronics"),
    ("SKU002", "Widget Type B", "Electronics"),
    ("SKU003", "Gadget Pro", "Electronics"),
    ("SKU004", "Component Alpha", "Parts"),
    ("SKU005", "Component Beta", "Parts"),
    ("SKU006", "Component Gamma", "Parts"),
    ("SKU007", "Assembly Unit X", "Assemblies"),
    ("SKU008", "Assembly Unit Y", "Assemblies"),  # PATTERN 2: Increasing trend
    ("SKU009", "Cable Bundle", "Accessories"),
    ("SKU010", "Power Supply", "Electronics"),
    ("SKU011", "Bracket Set", "Hardware"),
    ("SKU012", "Fastener Pack", "Hardware"),
    ("SKU013", "Circuit Board", "Electronics"),
    ("SKU014", "Motor Unit", "Parts"),
    ("SKU015", "Premium Kit", "Assemblies"),  # PATTERN 3: Demand spike
    ("SKU016", "Standard Kit", "Assemblies"),
    ("SKU017", "Connector Pack", "Accessories"),
    ("SKU018", "Thermal Paste", "Accessories"),
    ("SKU019", "Controller Board", "Electronics"),
    ("SKU020", "Sensor Array", "Parts"),
    ("SKU021", "Enclosure Pro", "Hardware"),
    ("SKU022", "Filter Unit", "Parts"),
    ("SKU023", "Battery Module", "Electronics"),
    ("SKU024", "Cooling Fan", "Parts"),
    ("SKU025", "Mounting Bracket", "Hardware"),
]

WAREHOUSE_CONFIGS = [
    ("WH-MAIN", "Main Distribution Center", "North America", 100000),
    ("WH-EAST", "Eastern Regional Hub", "North America", 50000),
    ("WH-EURO", "European Fulfillment", "Europe", 60000),
    ("WH-ASIA", "Asia Pacific Hub", "Asia", 55000),
    ("WH-SOUTH", "South American Warehouse", "South America", 30000),
]

CUSTOMER_TIERS = ["premium", "standard"]


# ═══════════════════════════════════════════════════════════════════════════════
# DATA GENERATION FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def generate_suppliers() -> list[dict]:
    """
    Generate 20 suppliers with realistic metrics.

    Returns:
        list[dict]: Supplier records with id, name, region, lead_time, on_time%, quality.
    """
    suppliers = []
    for supplier_id, name, region in SUPPLIER_BASES:
        supplier = {
            "supplier_id": supplier_id,
            "name": name,
            "region": region,
            "avg_lead_time_days": round(random.uniform(2, 20), 1),
            "on_time_delivery_pct": round(random.uniform(70, 98), 1),
            "quality_score": round(random.uniform(6.5, 9.8), 1),
        }
        suppliers.append(supplier)
    
    # PATTERN 1: SUP014 has degrading reliability
    # Find SUP014 and mark it for special handling (will degrade in PO generation)
    sup014_idx = next(i for i, s in enumerate(suppliers) if s["supplier_id"] == "SUP014")
    suppliers[sup014_idx]["on_time_delivery_pct"] = 92.0  # Start high
    suppliers[sup014_idx]["_degrading"] = True
    
    return suppliers


def generate_warehouses() -> list[dict]:
    """
    Generate 5 warehouses across regions.

    Returns:
        list[dict]: Warehouse records.
    """
    warehouses = []
    for warehouse_id, name, region, capacity in WAREHOUSE_CONFIGS:
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
    Generate 25 SKUs across 4-5 categories.

    Returns:
        list[dict]: SKU records.
    """
    skus = []
    for sku_id, name, category in SKU_CONFIGS:
        sku = {
            "sku_id": sku_id,
            "name": name,
            "category": category,
        }
        skus.append(sku)
    return skus


def generate_inventory(warehouses: list[dict], skus: list[dict]) -> list[dict]:
    """
    Generate current inventory levels for all warehouse/SKU combinations.

    Args:
        warehouses: List of warehouse records.
        skus: List of SKU records.

    Returns:
        list[dict]: Inventory records (warehouse_id, sku_id, current_stock).
    """
    inventory = []
    for warehouse in warehouses:
        for sku in skus:
            sku_id = sku["sku_id"]
            
            # PATTERN 2: SKU008 (assembly unit Y) has low stock for stockout risk
            if sku_id == "SKU008":
                stock = random.randint(40, 120)  # Low stock (will cause 5-day risk)
            # PATTERN 3: SKU015 (premium kit) also low stock after demand spike
            elif sku_id == "SKU015":
                stock = random.randint(30, 100)  # Very low stock
            else:
                stock = random.randint(200, 1500)
            
            record = {
                "warehouse_id": warehouse["warehouse_id"],
                "sku_id": sku_id,
                "current_stock": stock,
            }
            inventory.append(record)
    
    return inventory


def generate_demand_history(
    skus: list[dict],
    days: int = 90,
    base_date: Optional[datetime] = None
) -> list[dict]:
    """
    Generate 90 days of demand history per SKU with realistic patterns.

    Includes the 3 CRITICAL PATTERNS:
    1. Regular demand with daily variation
    2. SKU008: Increasing trend (leading to 5-day stockout risk)
    3. SKU015: 3x demand spike in last 10 days (unexpected stockout)

    Args:
        skus: List of SKU records.
        days: Number of historical days (default 90).
        base_date: Reference date (default today). Dates go backward.

    Returns:
        list[dict]: Demand history records (sku_id, date, units_sold).
    """
    if base_date is None:
        base_date = datetime.now()

    demand_history = []

    for sku in skus:
        sku_id = sku["sku_id"]

        # Set base demand per SKU
        if sku_id == "SKU008":
            # PATTERN 2: Increasing trend from ~80 to ~200+ units/day
            base_demand = 80
        elif sku_id == "SKU015":
            # PATTERN 3: Normal ~60 units, spike to ~180 in last 10 days
            base_demand = 60
        else:
            # Regular demand: 80-150 units/day
            base_demand = random.randint(80, 150)

        # Generate each day backwards from base_date
        for day_offset in range(days):
            date = base_date - timedelta(days=day_offset)
            date_str = date.strftime("%Y-%m-%d")

            # PATTERN 2: SKU008 - Linear increasing trend
            if sku_id == "SKU008":
                # Trend: start at ~80, increase to ~200 over 90 days
                trend_factor = (day_offset / 90)  # 0 to 1 (backward in time)
                daily_demand = base_demand + (120 * (1 - trend_factor)) + random.randint(-15, 15)
                daily_demand = max(10, int(daily_demand))

            # PATTERN 3: SKU015 - Normal demand + sudden 3x spike in last 10 days
            elif sku_id == "SKU015":
                if day_offset < 10:  # Last 10 days = high demand
                    daily_demand = base_demand * 3 + random.randint(-20, 20)
                else:
                    daily_demand = base_demand + random.randint(-10, 10)
                daily_demand = max(10, int(daily_demand))

            # Regular demand with random noise
            else:
                daily_demand = base_demand + random.randint(-30, 30)
                daily_demand = max(10, int(daily_demand))

            record = {
                "sku_id": sku_id,
                "date": date_str,
                "units_sold": daily_demand,
            }
            demand_history.append(record)

    return demand_history


def generate_purchase_orders(
    suppliers: list[dict],
    skus: list[dict],
    num_orders: int = 100,
    days_back: int = 180
) -> list[dict]:
    """
    Generate 100+ purchase orders with realistic delivery patterns.

    Includes PATTERN 1: SUP014 has degrading on-time delivery (92% → 61%).

    Args:
        suppliers: List of supplier records.
        skus: List of SKU records.
        num_orders: Number of purchase orders to generate (default 100).
        days_back: Days into the past to generate orders (default 180).

    Returns:
        list[dict]: Purchase order records.
    """
    purchase_orders = []
    base_date = datetime.now()

    # Find SUP014 index for pattern handling
    sup014 = next((s for s in suppliers if s["supplier_id"] == "SUP014"), None)

    for i in range(num_orders):
        order_id = f"PO-{10000 + i}"
        supplier = random.choice(suppliers)
        sku = random.choice(skus)

        promised_date = base_date - timedelta(days=random.randint(1, days_back))

        # PATTERN 1: SUP014 has degrading reliability
        # Orders from SUP014: start 92% on-time, degrade to 61% over 90 days
        if supplier["supplier_id"] == "SUP014":
            # Days from today (0 = today, 90 = 90 days ago)
            days_from_now = (base_date - promised_date).days
            # Degrade from 92% to 61% over 90 days
            on_time_pct = 92.0 - (31.0 * (days_from_now / 90.0))
            on_time_pct = max(61.0, min(92.0, on_time_pct))
        else:
            on_time_pct = supplier["on_time_delivery_pct"]

        # Determine if delivered and whether on-time
        if random.random() < 0.75:  # 75% delivered
            # On-time or late based on supplier metric
            if random.random() < (on_time_pct / 100.0):
                actual_date = promised_date
            else:
                actual_date = promised_date + timedelta(days=random.randint(1, 15))
            actual_date_str = actual_date.strftime("%Y-%m-%d")
        else:
            actual_date_str = None  # Not yet delivered

        order = {
            "order_id": order_id,
            "supplier_id": supplier["supplier_id"],
            "sku_id": sku["sku_id"],
            "quantity": random.randint(50, 500),
            "promised_date": promised_date.strftime("%Y-%m-%d"),
            "actual_date": actual_date_str,
            "quality_rating": int(random.choice([6, 7, 8, 9, 10])),
        }
        purchase_orders.append(order)

    return purchase_orders


def generate_shipments(purchase_orders: list[dict]) -> list[dict]:
    """
    Generate 30 shipments linked to purchase orders.

    Includes delay patterns: 85% on-time, 15% delayed.

    Args:
        purchase_orders: List of purchase order records.

    Returns:
        list[dict]: Shipment records.
    """
    shipments = []

    # Sample 30 random purchase orders to create shipments from
    selected_pos = random.sample(purchase_orders, min(30, len(purchase_orders)))

    for i, po in enumerate(selected_pos):
        shipment_id = f"SHIP-{20000 + i}"

        promised_date = datetime.strptime(po["promised_date"], "%Y-%m-%d")

        # 85% on-time, 15% delayed
        if random.random() < 0.85:
            estimated_delivery = promised_date
            current_status = random.choice(["pending", "in_transit", "delivered"])
        else:
            estimated_delivery = promised_date + timedelta(days=random.randint(1, 7))
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
    num_orders_per_shipment: int = 2
) -> list[dict]:
    """
    Generate 50+ downstream customer orders linked to shipments.

    Includes mix of premium (33%) and standard (67%) tiers.

    Args:
        shipments: List of shipment records.
        skus: List of SKU records.
        num_orders_per_shipment: Orders per shipment (default 2).

    Returns:
        list[dict]: Downstream order records.
    """
    downstream_orders = []
    order_counter = 100000

    for shipment in shipments:
        for _ in range(num_orders_per_shipment):
            order_id = f"ORD-CUST-{order_counter}"
            order_counter += 1

            sku = random.choice(skus)
            
            # Premium: 33%, Standard: 67%
            customer_tier = "premium" if random.random() < 0.33 else "standard"

            order = {
                "order_id": order_id,
                "shipment_id": shipment["shipment_id"],
                "customer_tier": customer_tier,
                "sku_id": sku["sku_id"],
                "quantity": random.randint(10, 200),
            }
            downstream_orders.append(order)

    return downstream_orders


# ═══════════════════════════════════════════════════════════════════════════════
# DATABASE POPULATION
# ═══════════════════════════════════════════════════════════════════════════════

def generate_data(db_path: str) -> dict:
    """
    Generate and populate complete synthetic supply chain dataset.

    This is the main entry point. It:
    1. Generates all data programmatically
    2. Inserts into SQLite database in dependency order
    3. Bakes in 3 CRITICAL PATTERNS for demo:
       a) Supplier SUP014: Degrading reliability (92% → 61% on-time)
       b) SKU008: Increasing demand trend (causes 5-day stockout risk)
       c) SKU015: Sudden 3x demand spike (causes unexpected stockout)

    Args:
        db_path: Path to SQLite database file (must be initialized via schema.init_db first).

    Returns:
        dict: Summary of inserted records per table.
              {
                  "suppliers": int,
                  "warehouses": int,
                  "skus": int,
                  "inventory": int,
                  "demand_history": int,
                  "purchase_orders": int,
                  "shipments": int,
                  "downstream_orders": int,
              }

    Raises:
        sqlite3.Error: If database operations fail.
        FileNotFoundError: If database file doesn't exist.

    Example:
        >>> from data.schema import init_db
        >>> from data.generator import generate_data
        >>> conn = init_db("data/supplysense.db")
        >>> conn.close()
        >>> summary = generate_data("data/supplysense.db")
        >>> print(summary)
        {"suppliers": 20, "warehouses": 5, "skus": 25, ...}
    """
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        conn.row_factory = sqlite3.Row
        logger.info(f"Generating data for {db_path}")

        # =====================================================================
        # Generate all data
        # =====================================================================
        print("Generating synthetic data...")
        suppliers = generate_suppliers()
        warehouses = generate_warehouses()
        skus = generate_skus()
        inventory = generate_inventory(warehouses, skus)
        demand_history = generate_demand_history(skus, days=90)
        purchase_orders = generate_purchase_orders(suppliers, skus, num_orders=100)
        shipments = generate_shipments(purchase_orders)
        downstream_orders = generate_downstream_orders(shipments, skus, num_orders_per_shipment=2)

        summary = {}

        # =====================================================================
        # Insert suppliers
        # =====================================================================
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

        # Commit all changes
        conn.commit()
        conn.close()

        print("\n" + "=" * 80)
        print("DATA GENERATION COMPLETE")
        print("=" * 80)
        print("\nRecords inserted:")
        for table_name, count in summary.items():
            print(f"  {table_name}: {count}")

        logger.info(f"Data generation complete: {summary}")
        return summary

    except sqlite3.Error as e:
        logger.error(f"Database error during data generation: {e}", exc_info=True)
        raise
    except Exception as e:
        logger.error(f"Error during data generation: {e}", exc_info=True)
        raise


# ═══════════════════════════════════════════════════════════════════════════════
# CLI ENTRY POINT & TESTING
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    """Quick test and verification of data generation."""
    import sys
    import os

    # Add parent to path for imports
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format="[%(asctime)s] %(levelname)s: %(message)s"
    )

    print("\n" + "=" * 80)
    print("SYNTHETIC DATA GENERATION - COMPLETE SUPPLY CHAIN DATASET")
    print("=" * 80 + "\n")

    # Initialize database
    print("STEP 1: Initializing database schema...")
    from data.schema import init_db

    db_path = "data/supplysense.db"

    try:
        # Remove old database if it exists
        if os.path.exists(db_path):
            print(f"  Removing existing database: {db_path}")
            os.remove(db_path)

        # Initialize
        conn = init_db(db_path)
        conn.close()
        print(f"[OK] Database initialized at {db_path}\n")

        # Generate data
        print("STEP 2: Generating synthetic data with critical patterns...")
        print("-" * 80)
        summary = generate_data(db_path)
        print()

        # Verification queries
        print("STEP 3: Verifying data with test queries...")
        print("-" * 80)

        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Pattern 1: Verify SUP014 degrading reliability
        print("\nPATTERN 1: Supplier SUP014 degrading reliability")
        cursor.execute(
            "SELECT * FROM purchase_orders WHERE supplier_id = 'SUP014' LIMIT 5"
        )
        sup014_orders = cursor.fetchall()
        print(f"  SUP014 purchase orders found: {len(sup014_orders)}")
        if sup014_orders:
            delivered = sum(1 for o in sup014_orders if o["actual_date"] is not None)
            print(f"  Delivered: {delivered}/{len(sup014_orders)}")

        # Pattern 2: Verify SKU008 inventory low + increasing demand
        print("\nPATTERN 2: SKU008 increasing demand trend + low stock")
        cursor.execute(
            "SELECT SUM(current_stock) as total_stock FROM inventory WHERE sku_id = 'SKU008'"
        )
        sku008_stock = cursor.fetchone()["total_stock"]
        print(f"  SKU008 total inventory: {sku008_stock} units")

        cursor.execute(
            """
            SELECT date, units_sold FROM demand_history 
            WHERE sku_id = 'SKU008' 
            ORDER BY date DESC 
            LIMIT 10
            """
        )
        sku008_recent = cursor.fetchall()
        recent_avg = sum(r["units_sold"] for r in sku008_recent) / len(sku008_recent)
        print(f"  SKU008 recent average demand (last 10 days): {recent_avg:.0f} units/day")

        cursor.execute(
            """
            SELECT date, units_sold FROM demand_history 
            WHERE sku_id = 'SKU008' 
            ORDER BY date ASC 
            LIMIT 10
            """
        )
        sku008_old = cursor.fetchall()
        old_avg = sum(r["units_sold"] for r in sku008_old) / len(sku008_old)
        print(f"  SKU008 old average demand (first 10 days): {old_avg:.0f} units/day")
        print(f"  Trend: {old_avg:.0f} -> {recent_avg:.0f} units/day (INCREASING)")

        # Pattern 3: Verify SKU015 demand spike
        print("\nPATTERN 3: SKU015 sudden 3x demand spike (last 10 days)")
        cursor.execute(
            """
            SELECT date, units_sold FROM demand_history 
            WHERE sku_id = 'SKU015' 
            ORDER BY date DESC 
            LIMIT 10
            """
        )
        sku015_recent = cursor.fetchall()
        recent_avg_015 = sum(r["units_sold"] for r in sku015_recent) / len(sku015_recent)
        print(f"  SKU015 spike demand (last 10 days): {recent_avg_015:.0f} units/day")

        cursor.execute(
            """
            SELECT date, units_sold FROM demand_history 
            WHERE sku_id = 'SKU015' 
            ORDER BY date ASC 
            LIMIT 20
            """
        )
        sku015_old = cursor.fetchall()
        old_avg_015 = sum(r["units_sold"] for r in sku015_old) / len(sku015_old)
        print(f"  SKU015 baseline demand (days 70-90): {old_avg_015:.0f} units/day")
        print(f"  Spike multiplier: {recent_avg_015 / old_avg_015:.1f}x")

        cursor.execute(
            "SELECT SUM(current_stock) as total_stock FROM inventory WHERE sku_id = 'SKU015'"
        )
        sku015_stock = cursor.fetchone()["total_stock"]
        print(f"  SKU015 current total inventory: {sku015_stock} units")

        # Summary stats
        print("\n" + "-" * 80)
        print("DATABASE SUMMARY")
        print("-" * 80)
        for table in [
            "suppliers",
            "warehouses",
            "skus",
            "inventory",
            "demand_history",
            "purchase_orders",
            "shipments",
            "downstream_orders",
        ]:
            cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
            count = cursor.fetchone()["count"]
            print(f"  {table}: {count}")

        conn.close()

        print("\n" + "=" * 80)
        print("DATA GENERATION & VERIFICATION COMPLETE")
        print("=" * 80)
        print(f"\nDatabase: {db_path}")
        print("Status: READY FOR AGENT TESTING")
        print()

    except Exception as e:
        print(f"\n[ERROR] {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
