"""
Inventory management module for supply chain inventory intelligence.

Provides stockout prediction, risk assessment, and reorder recommendations
based on current stock levels and forecasted demand.
"""

from typing import Optional


def predict_stockout(
    sku_id: str,
    warehouse_id: str,
    current_stock: int,
    forecast_result: dict,
) -> dict:
    """
    Predict stockout risk and recommend reorder quantity for a SKU at a warehouse.

    This function analyzes the time until stockout based on current inventory levels
    and forecasted average daily demand. It classifies risk level and calculates
    a recommended reorder quantity to maintain a 14-day supply buffer.

    Args:
        sku_id: Unique identifier for the stock keeping unit.
        warehouse_id: Unique identifier for the warehouse location.
        current_stock: Current inventory quantity (units) at the warehouse.
        forecast_result: Output dict from forecast_demand() containing:
                        - avg_forecasted_demand: float (average daily demand)
                        - Other fields from forecast_demand (used for context)

    Returns:
        dict with keys:
            - sku_id: str — the input SKU identifier.
            - warehouse_id: str — the input warehouse identifier.
            - current_stock: int — current inventory level.
            - days_until_stockout: float | None — days until stock depleted at
                                   current demand rate. None if avg_forecasted_demand
                                   is 0 (no demand).
            - risk_level: str — "critical" (≤3 days), "high" (≤7), "medium" (≤14),
                          or "low" (>14 days or no demand).
            - recommended_reorder_quantity: int — units to order to maintain 14-day
                                           supply (current_stock + recommendation
                                           should cover 14 days of demand).

    Raises:
        KeyError: If forecast_result is missing 'avg_forecasted_demand' key.
        ValueError: If current_stock is negative.
        TypeError: If forecast_result is not a dict or current_stock is not an int.
    """
    # Input validation
    if not isinstance(current_stock, int):
        raise TypeError(f"current_stock must be int, got {type(current_stock).__name__}")
    if current_stock < 0:
        raise ValueError(f"current_stock cannot be negative, got {current_stock}")
    if not isinstance(forecast_result, dict):
        raise TypeError(f"forecast_result must be dict, got {type(forecast_result).__name__}")
    if "avg_forecasted_demand" not in forecast_result:
        raise KeyError("forecast_result must contain 'avg_forecasted_demand' key")

    avg_forecasted_demand: float = float(forecast_result["avg_forecasted_demand"])

    # =========================================================================
    # Calculate days until stockout
    # =========================================================================
    if avg_forecasted_demand <= 0:
        # No demand or invalid forecast: cannot deplete stock
        days_until_stockout: Optional[float] = None
    else:
        days_until_stockout = current_stock / avg_forecasted_demand

    # =========================================================================
    # Classify risk level
    # =========================================================================
    risk_level: str = _classify_risk_level(days_until_stockout)

    # =========================================================================
    # Calculate recommended reorder quantity
    # =========================================================================
    # Target: 14 days of supply
    target_stock: float = avg_forecasted_demand * 14
    recommended_reorder_quantity: int = int(round(target_stock - current_stock))
    # Ensure we never recommend negative reorder (stock already exceeds target)
    recommended_reorder_quantity = max(recommended_reorder_quantity, 0)

    return {
        "sku_id": sku_id,
        "warehouse_id": warehouse_id,
        "current_stock": current_stock,
        "days_until_stockout": days_until_stockout,
        "risk_level": risk_level,
        "recommended_reorder_quantity": recommended_reorder_quantity,
        "overstock_risk": _check_overstock(current_stock, avg_forecasted_demand),
        "overstock_ratio": round(current_stock / (avg_forecasted_demand * 7), 2) if avg_forecasted_demand > 0 else None,
    }


def _classify_risk_level(days_until_stockout: Optional[float]) -> str:
    """
    Classify stockout risk based on days remaining.

    Args:
        days_until_stockout: Days until stock depleted, or None if no demand.

    Returns:
        str: One of "critical", "high", "medium", or "low".
    """
    if days_until_stockout is None:
        # No demand: stock will never deplete
        return "low"
    elif days_until_stockout <= 3:
        return "critical"
    elif days_until_stockout <= 7:
        return "high"
    elif days_until_stockout <= 14:
        return "medium"
    else:
        return "low"


def _check_overstock(current_stock: int, avg_daily_demand: float) -> bool:
    """
    Detect overstock risk: current stock > 3x forecasted 7-day demand.

    Args:
        current_stock: Units currently in warehouse.
        avg_daily_demand: Forecasted average daily units.

    Returns:
        bool: True if overstock risk detected.
    """
    if avg_daily_demand <= 0:
        return False
    weekly_demand = avg_daily_demand * 7
    return current_stock > (3 * weekly_demand)
