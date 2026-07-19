"""
SQLite schema definitions for SupplySense supply chain data layer.

Defines all tables needed for the agentic supply chain intelligence system,
including suppliers, warehouses, inventory, demand history, orders, shipments,
and action tracking.
"""

import sqlite3
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# TABLE SCHEMAS (SQL CREATE TABLE statements)
# ═══════════════════════════════════════════════════════════════════════════════

SCHEMA_SUPPLIERS = """
CREATE TABLE IF NOT EXISTS suppliers (
    supplier_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    region TEXT NOT NULL,
    avg_lead_time_days REAL DEFAULT 0,
    on_time_delivery_pct REAL DEFAULT 100,
    quality_score REAL DEFAULT 5,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
"""

SCHEMA_WAREHOUSES = """
CREATE TABLE IF NOT EXISTS warehouses (
    warehouse_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    region TEXT NOT NULL,
    capacity INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
"""

SCHEMA_SKUS = """
CREATE TABLE IF NOT EXISTS skus (
    sku_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
"""

SCHEMA_INVENTORY = """
CREATE TABLE IF NOT EXISTS inventory (
    warehouse_id TEXT NOT NULL,
    sku_id TEXT NOT NULL,
    current_stock INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (warehouse_id, sku_id),
    FOREIGN KEY (warehouse_id) REFERENCES warehouses(warehouse_id),
    FOREIGN KEY (sku_id) REFERENCES skus(sku_id)
)
"""

SCHEMA_DEMAND_HISTORY = """
CREATE TABLE IF NOT EXISTS demand_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sku_id TEXT NOT NULL,
    date TEXT NOT NULL,
    units_sold INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (sku_id) REFERENCES skus(sku_id),
    UNIQUE(sku_id, date)
)
"""

SCHEMA_PURCHASE_ORDERS = """
CREATE TABLE IF NOT EXISTS purchase_orders (
    order_id TEXT PRIMARY KEY,
    supplier_id TEXT NOT NULL,
    sku_id TEXT NOT NULL,
    quantity INTEGER NOT NULL,
    promised_date TEXT NOT NULL,
    actual_date TEXT,
    quality_rating INTEGER DEFAULT 5,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (supplier_id) REFERENCES suppliers(supplier_id),
    FOREIGN KEY (sku_id) REFERENCES skus(sku_id)
)
"""

SCHEMA_SHIPMENTS = """
CREATE TABLE IF NOT EXISTS shipments (
    shipment_id TEXT PRIMARY KEY,
    order_id TEXT NOT NULL,
    promised_date TEXT NOT NULL,
    estimated_delivery TEXT,
    current_status TEXT DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (order_id) REFERENCES purchase_orders(order_id)
)
"""

SCHEMA_DOWNSTREAM_ORDERS = """
CREATE TABLE IF NOT EXISTS downstream_orders (
    order_id TEXT PRIMARY KEY,
    shipment_id TEXT NOT NULL,
    customer_tier TEXT NOT NULL CHECK (customer_tier IN ('premium', 'standard')),
    sku_id TEXT NOT NULL,
    quantity INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (shipment_id) REFERENCES shipments(shipment_id),
    FOREIGN KEY (sku_id) REFERENCES skus(sku_id)
)
"""

SCHEMA_PENDING_ACTIONS = """
CREATE TABLE IF NOT EXISTS pending_actions (
    action_id TEXT PRIMARY KEY,
    action_type TEXT NOT NULL CHECK (action_type IN ('reorder', 'switch_supplier')),
    details TEXT NOT NULL,
    status TEXT DEFAULT 'pending_approval' CHECK (status IN ('pending_approval', 'approved', 'rejected', 'executed')),
    created_by TEXT DEFAULT 'agent',
    reasoning TEXT,
    created_at TEXT NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
"""

# ═══════════════════════════════════════════════════════════════════════════════
# SCHEMA REGISTRY
# ═══════════════════════════════════════════════════════════════════════════════

SCHEMAS = [
    ("suppliers", SCHEMA_SUPPLIERS),
    ("warehouses", SCHEMA_WAREHOUSES),
    ("skus", SCHEMA_SKUS),
    ("inventory", SCHEMA_INVENTORY),
    ("demand_history", SCHEMA_DEMAND_HISTORY),
    ("purchase_orders", SCHEMA_PURCHASE_ORDERS),
    ("shipments", SCHEMA_SHIPMENTS),
    ("downstream_orders", SCHEMA_DOWNSTREAM_ORDERS),
    ("pending_actions", SCHEMA_PENDING_ACTIONS),
]


# ═══════════════════════════════════════════════════════════════════════════════
# DATABASE INITIALIZATION
# ═══════════════════════════════════════════════════════════════════════════════

def init_db(db_path: str) -> sqlite3.Connection:
    """
    Initialize SQLite database with all SupplySense schema tables.

    This function creates the database file if it doesn't exist and creates
    all required tables (suppliers, warehouses, skus, inventory, etc.) if they
    don't already exist. Uses IF NOT EXISTS to make it idempotent and safe to
    call multiple times.

    Args:
        db_path: Path to SQLite database file (str or Path-like).
                 Example: "/data/supply_chain.db" or "data/supply_chain.db"
                 Parent directory must exist or will be created.

    Returns:
        sqlite3.Connection: Active database connection (caller must close).
        Caller responsibility: connection.close() when done.

    Raises:
        FileNotFoundError: If parent directory does not exist (unless auto-create).
        sqlite3.DatabaseError: If database corruption or schema conflict detected.
        PermissionError: If insufficient permissions to create/write database file.

    Side Effects:
        - Creates database file at db_path if it doesn't exist
        - Creates all 9 tables if they don't exist
        - Logs table creation events
        - Sets sqlite3 connection to row_factory for dict-like access

    Example:
        >>> conn = init_db("data/supply_chain.db")
        >>> cursor = conn.cursor()
        >>> cursor.execute("SELECT COUNT(*) FROM suppliers")
        >>> conn.close()

        Or as context manager (recommended):
        >>> with sqlite3.connect("data/supply_chain.db") as conn:
        ...     cursor = conn.cursor()
        ...     cursor.execute("SELECT COUNT(*) FROM suppliers")
    """
    # =========================================================================
    # Input validation and setup
    # =========================================================================
    if not isinstance(db_path, str):
        db_path = str(db_path)

    db_path = db_path.strip()
    if not db_path:
        raise ValueError("db_path cannot be empty string")

    # Create parent directories if they don't exist
    db_file = Path(db_path)
    db_file.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Initializing SupplySense database at: {db_path}")

    # =========================================================================
    # Connect to database
    # =========================================================================
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row  # Enable dict-like row access
        logger.debug("Database connection established")
    except sqlite3.Error as e:
        logger.error(f"Failed to connect to database at {db_path}: {e}")
        raise

    # =========================================================================
    # Create all tables
    # =========================================================================
    cursor = conn.cursor()
    tables_created = 0
    tables_skipped = 0

    try:
        for table_name, schema_sql in SCHEMAS:
            try:
                cursor.execute(schema_sql)
                logger.debug(f"Table '{table_name}' created or already exists")
                tables_created += 1

            except sqlite3.Error as e:
                if "already exists" in str(e).lower():
                    logger.debug(f"Table '{table_name}' already exists, skipping")
                    tables_skipped += 1
                else:
                    logger.error(f"Error creating table '{table_name}': {e}")
                    raise

        # Commit all changes
        conn.commit()
        logger.info(
            f"Database initialization complete. "
            f"Tables: {tables_created} created, {tables_skipped} already existed"
        )

    except sqlite3.Error as e:
        logger.error(f"Database initialization failed: {e}", exc_info=True)
        conn.close()
        raise

    return conn


# ═══════════════════════════════════════════════════════════════════════════════
# DATABASE UTILITY FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def get_db_connection(db_path: str) -> sqlite3.Connection:
    """
    Get or create a database connection (does NOT initialize schema).

    Use this if the database has already been initialized. For first-time setup,
    use init_db() instead.

    Args:
        db_path: Path to SQLite database file.

    Returns:
        sqlite3.Connection: Active database connection.

    Raises:
        sqlite3.Error: If connection fails.
    """
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        logger.error(f"Failed to get database connection: {e}")
        raise


def drop_all_tables(conn: sqlite3.Connection) -> None:
    """
    Drop all SupplySense tables from the database (DESTRUCTIVE).

    WARNING: This permanently deletes all data in all tables.
    Use only for testing or data reset.

    Args:
        conn: Active sqlite3.Connection to database.

    Raises:
        sqlite3.Error: If drop operation fails.
    """
    cursor = conn.cursor()
    table_names = [name for name, _ in SCHEMAS]

    logger.warning(f"Dropping all tables: {table_names}")

    try:
        for table_name in reversed(table_names):  # Reverse to respect foreign keys
            cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
        conn.commit()
        logger.warning("All tables dropped successfully")
    except sqlite3.Error as e:
        logger.error(f"Failed to drop tables: {e}")
        conn.close()
        raise


def get_table_info(conn: sqlite3.Connection, table_name: str) -> list[dict]:
    """
    Get column information for a table (for introspection).

    Args:
        conn: Active sqlite3.Connection.
        table_name: Name of table to inspect.

    Returns:
        list[dict]: List of column info dicts with keys (name, type, notnull, etc.)
    """
    cursor = conn.cursor()
    try:
        cursor.execute(f"PRAGMA table_info({table_name})")
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    except sqlite3.Error as e:
        logger.error(f"Failed to get table info for {table_name}: {e}")
        return []


def get_all_tables(conn: sqlite3.Connection) -> list[str]:
    """
    Get list of all tables in the database.

    Args:
        conn: Active sqlite3.Connection.

    Returns:
        list[str]: Table names.
    """
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        )
        return [row[0] for row in cursor.fetchall()]
    except sqlite3.Error as e:
        logger.error(f"Failed to get table list: {e}")
        return []


def export_schema(conn: sqlite3.Connection, output_file: Optional[str] = None) -> str:
    """
    Export current database schema as SQL DDL statements.

    Useful for debugging, documentation, and schema migration.

    Args:
        conn: Active sqlite3.Connection.
        output_file: Optional file path to write schema to. If None, returns as string.

    Returns:
        str: Complete schema SQL statements (all CREATE TABLE statements).
    """
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
        )
        schema_statements = [row[0] for row in cursor.fetchall()]
        schema_sql = ";\n\n".join(schema_statements) + ";"

        if output_file:
            with open(output_file, "w") as f:
                f.write(schema_sql)
            logger.info(f"Schema exported to {output_file}")

        return schema_sql

    except sqlite3.Error as e:
        logger.error(f"Failed to export schema: {e}")
        return ""


# ═══════════════════════════════════════════════════════════════════════════════
# TESTING & INTROSPECTION (for verification)
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    """
    Quick test of schema initialization and introspection.
    """
    import tempfile
    import os

    print("\n" + "=" * 80)
    print("SCHEMA INITIALIZATION TEST")
    print("=" * 80 + "\n")

    # Create temporary database for testing
    temp_dir = tempfile.mkdtemp()
    temp_db = os.path.join(temp_dir, "test_supply_chain.db")

    try:
        # Initialize database
        print(f"Initializing database at: {temp_db}")
        conn = init_db(temp_db)
        print("[OK] Database initialized successfully\n")

        # List all tables
        print("Tables created:")
        tables = get_all_tables(conn)
        for i, table in enumerate(tables, 1):
            print(f"  {i}. {table}")
        print(f"\nTotal: {len(tables)} tables\n")

        # Show schema for each table
        print("Table schemas:")
        print("-" * 80)
        for table in tables:
            columns = get_table_info(conn, table)
            print(f"\n{table}:")
            for col in columns:
                col_name = col["name"]
                col_type = col["type"]
                notnull = "NOT NULL" if col["notnull"] else ""
                pk = "PRIMARY KEY" if col["pk"] else ""
                attrs = " ".join(filter(None, [notnull, pk]))
                print(f"  - {col_name}: {col_type} {attrs}".rstrip())

        # Export schema
        print("\n" + "-" * 80)
        print("Complete schema SQL:")
        print("-" * 80 + "\n")
        schema = export_schema(conn)
        print(schema[:500] + "..." if len(schema) > 500 else schema)

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
