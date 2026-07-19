"""
Shipment delay impact assessment module for supply chain intelligence.

Provides detection and impact analysis of supply chain delays on downstream orders.
"""

from typing import Optional
from datetime import datetime


def detect_delay_impact(
    shipment_id: str,
    shipment_data: dict,
    downstream_orders: list[dict],
) -> dict:
    """
    Detect shipment delays and assess impact on downstream orders.

    This function evaluates whether a shipment is delayed relative to its promised
    delivery date, calculates the delay duration, and quantifies the downstream
    business impact based on affected customer order tiers (premium tier weighted
    2x higher than standard).

    Args:
        shipment_id: Unique identifier for the shipment.
        shipment_data: Shipment details containing:
                      - promised_date: str (YYYY-MM-DD format)
                      - current_status: str (e.g., "in_transit", "delayed", "delivered")
                      - estimated_delivery: str (YYYY-MM-DD format) or None
        downstream_orders: List of orders dependent on this shipment, each containing:
                          - order_id: str (unique order identifier)
                          - customer_tier: str ("premium" or "standard")
                          - sku_id: str (stock keeping unit)
                          - quantity: int (order quantity in units)

    Returns:
        dict with keys:
            - shipment_id: str — the input shipment identifier.
            - is_delayed: bool — True if estimated_delivery > promised_date.
            - delay_days: int — days delayed (0 if not delayed).
            - downstream_impact_score: float (0-100) — weighted count of affected
                                      orders normalized against max 20 weighted orders.
                                      Premium tier orders count as 2x weight.
            - affected_order_ids: list[str] — order IDs dependent on this shipment.
            - severity: str — "critical" (score >= 70), "moderate" (>= 30),
                       or "minor" (otherwise).

    Raises:
        KeyError: If shipment_data or downstream_orders items missing required keys.
        ValueError: If date formats are invalid or customer_tier is invalid.
        TypeError: If inputs are incorrect types.
    """
    # Input validation
    if not isinstance(shipment_data, dict):
        raise TypeError(f"shipment_data must be dict, got {type(shipment_data).__name__}")
    if not isinstance(downstream_orders, list):
        raise TypeError(
            f"downstream_orders must be list, got {type(downstream_orders).__name__}"
        )

    # =========================================================================
    # Validate and extract shipment data
    # =========================================================================
    required_shipment_keys = {"promised_date", "current_status", "estimated_delivery"}
    if not required_shipment_keys.issubset(shipment_data.keys()):
        missing = required_shipment_keys - shipment_data.keys()
        raise KeyError(f"shipment_data missing keys: {missing}")

    # Parse dates
    try:
        promised_date = datetime.strptime(shipment_data["promised_date"], "%Y-%m-%d").date()
    except ValueError as e:
        raise ValueError(
            f"shipment_data['promised_date'] has invalid format (expected YYYY-MM-DD): {e}"
        )

    estimated_delivery_str: Optional[str] = shipment_data["estimated_delivery"]
    if estimated_delivery_str is not None:
        try:
            estimated_delivery = datetime.strptime(
                estimated_delivery_str, "%Y-%m-%d"
            ).date()
        except ValueError as e:
            raise ValueError(
                f"shipment_data['estimated_delivery'] has invalid format (expected YYYY-MM-DD): {e}"
            )
    else:
        estimated_delivery = None

    # =========================================================================
    # Determine if delayed
    # =========================================================================
    if estimated_delivery is None:
        # No estimated delivery date: assume not delayed yet
        is_delayed: bool = False
        delay_days: int = 0
    elif estimated_delivery > promised_date:
        is_delayed = True
        delay_days = (estimated_delivery - promised_date).days
    else:
        is_delayed = False
        delay_days = 0

    # =========================================================================
    # Calculate downstream impact score
    # =========================================================================
    affected_order_ids: list[str] = []
    weighted_order_count: float = 0.0

    for i, order in enumerate(downstream_orders):
        if not isinstance(order, dict):
            raise TypeError(f"downstream_orders[{i}] must be dict, got {type(order).__name__}")

        # Validate required keys
        required_order_keys = {"order_id", "customer_tier", "sku_id", "quantity"}
        if not required_order_keys.issubset(order.keys()):
            missing = required_order_keys - order.keys()
            raise KeyError(f"downstream_orders[{i}] missing keys: {missing}")

        # Validate customer tier
        customer_tier: str = order["customer_tier"]
        if customer_tier not in ("premium", "standard"):
            raise ValueError(
                f"downstream_orders[{i}]['customer_tier'] must be 'premium' or 'standard', "
                f"got '{customer_tier}'"
            )

        # Collect affected order
        order_id: str = order["order_id"]
        affected_order_ids.append(order_id)

        # Calculate weighted count: premium = 2x, standard = 1x
        weight: float = 2.0 if customer_tier == "premium" else 1.0
        weighted_order_count += weight

    # Normalize against max 20 weighted orders (20 standard or 10 premium)
    # Score formula: (weighted_count / 20) * 100, clipped to [0, 100]
    max_weighted_orders: float = 20.0
    downstream_impact_score: float = (weighted_order_count / max_weighted_orders) * 100
    downstream_impact_score = min(downstream_impact_score, 100.0)

    # =========================================================================
    # Classify severity
    # =========================================================================
    severity: str = _classify_severity(downstream_impact_score)

    return {
        "shipment_id": shipment_id,
        "is_delayed": is_delayed,
        "delay_days": delay_days,
        "downstream_impact_score": downstream_impact_score,
        "affected_order_ids": affected_order_ids,
        "severity": severity,
    }


def _classify_severity(impact_score: float) -> str:
    """
    Classify delay severity based on downstream impact score.

    Args:
        impact_score: Impact score (0-100).

    Returns:
        str: One of "critical", "moderate", or "minor".
    """
    if impact_score >= 70:
        return "critical"
    elif impact_score >= 30:
        return "moderate"
    else:
        return "minor"
