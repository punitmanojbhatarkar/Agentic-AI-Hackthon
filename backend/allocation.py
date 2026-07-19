"""
Inventory allocation and order fulfillment module for supply chain intelligence.

Provides intelligent stock allocation across pending orders based on customer
tier priority and order recency.
"""

from typing import Optional
from datetime import datetime


def recommend_allocation(
    sku_id: str,
    available_stock: int,
    pending_orders: list[dict],
) -> dict:
    """
    Recommend optimal inventory allocation across pending orders.

    This function implements a prioritized allocation strategy that maximizes
    customer satisfaction while respecting inventory constraints. Premium tier
    customers receive priority within their tier based on order date (FIFO),
    followed by standard tier customers (also FIFO).

    Args:
        sku_id: Unique identifier for the stock keeping unit.
        available_stock: Current inventory quantity available for allocation (int).
        pending_orders: List of pending customer orders, each containing:
                       - order_id: str (unique order identifier)
                       - customer_tier: str ("premium" or "standard")
                       - quantity_requested: int (units requested by customer)
                       - order_date: str (YYYY-MM-DD format, determines priority)

    Returns:
        dict with keys:
            - sku_id: str — the input SKU identifier.
            - available_stock: int — starting inventory quantity.
            - total_requested: int — sum of all quantity_requested across orders.
            - allocations: list[dict] — allocation result per order, each containing:
                * order_id: str
                * customer_tier: str
                * quantity_requested: int
                * quantity_allocated: int
                * fulfillment_status: str ("full" | "partial" | "none")
            - fully_satisfied: bool — True if all orders fully satisfied.

    Raises:
        KeyError: If pending_orders items missing required keys.
        ValueError: If quantity_requested is negative or customer_tier invalid.
        TypeError: If inputs are incorrect types.
    """
    # Input validation
    if not isinstance(available_stock, int):
        raise TypeError(f"available_stock must be int, got {type(available_stock).__name__}")
    if available_stock < 0:
        raise ValueError(f"available_stock cannot be negative, got {available_stock}")
    if not isinstance(pending_orders, list):
        raise TypeError(
            f"pending_orders must be list, got {type(pending_orders).__name__}"
        )

    # =========================================================================
    # Validate and organize pending orders
    # =========================================================================
    validated_orders: list[dict] = []
    total_requested: int = 0

    for i, order in enumerate(pending_orders):
        if not isinstance(order, dict):
            raise TypeError(f"pending_orders[{i}] must be dict, got {type(order).__name__}")

        # Validate required keys
        required_keys = {"order_id", "customer_tier", "quantity_requested", "order_date"}
        if not required_keys.issubset(order.keys()):
            missing = required_keys - order.keys()
            raise KeyError(f"pending_orders[{i}] missing keys: {missing}")

        # Validate customer tier
        customer_tier: str = order["customer_tier"]
        if customer_tier not in ("premium", "standard"):
            raise ValueError(
                f"pending_orders[{i}]['customer_tier'] must be 'premium' or 'standard', "
                f"got '{customer_tier}'"
            )

        # Validate quantity_requested
        quantity_requested: int = order["quantity_requested"]
        if not isinstance(quantity_requested, int) or quantity_requested < 0:
            raise ValueError(
                f"pending_orders[{i}]['quantity_requested'] must be non-negative int, "
                f"got {quantity_requested}"
            )

        # Validate and parse order_date
        try:
            order_date = datetime.strptime(order["order_date"], "%Y-%m-%d").date()
        except ValueError as e:
            raise ValueError(
                f"pending_orders[{i}]['order_date'] has invalid format (expected YYYY-MM-DD): {e}"
            )

        # Add to validated list with parsed date
        validated_orders.append({
            "order_id": order["order_id"],
            "customer_tier": customer_tier,
            "quantity_requested": quantity_requested,
            "order_date": order_date,
        })

        total_requested += quantity_requested

    # =========================================================================
    # Sort orders by priority: premium tier first (by order_date), then standard
    # =========================================================================
    # Sort by: (tier priority, order_date) where premium=0, standard=1
    tier_priority = {"premium": 0, "standard": 1}
    sorted_orders = sorted(
        validated_orders,
        key=lambda o: (tier_priority[o["customer_tier"]], o["order_date"])
    )

    # =========================================================================
    # Allocate stock
    # =========================================================================
    remaining_stock: int = available_stock
    allocations: list[dict] = []

    for order in sorted_orders:
        order_id: str = order["order_id"]
        customer_tier: str = order["customer_tier"]
        quantity_requested: int = order["quantity_requested"]

        # Determine allocation
        if remaining_stock == 0:
            # No stock left
            quantity_allocated: int = 0
            fulfillment_status: str = "none"
        elif remaining_stock >= quantity_requested:
            # Full fulfillment
            quantity_allocated = quantity_requested
            fulfillment_status = "full"
            remaining_stock -= quantity_allocated
        else:
            # Partial fulfillment
            quantity_allocated = remaining_stock
            fulfillment_status = "partial"
            remaining_stock = 0

        allocations.append({
            "order_id": order_id,
            "customer_tier": customer_tier,
            "quantity_requested": quantity_requested,
            "quantity_allocated": quantity_allocated,
            "fulfillment_status": fulfillment_status,
        })

    # =========================================================================
    # Determine if all orders fully satisfied
    # =========================================================================
    fully_satisfied: bool = all(
        alloc["fulfillment_status"] == "full" for alloc in allocations
    )

    return {
        "sku_id": sku_id,
        "available_stock": available_stock,
        "total_requested": total_requested,
        "allocations": allocations,
        "fully_satisfied": fully_satisfied,
    }
