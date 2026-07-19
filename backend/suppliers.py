"""
Supplier risk assessment module for supply chain intelligence.

Provides supplier reliability scoring based on delivery performance,
lead time consistency, and quality ratings.
"""

from typing import Optional
from datetime import datetime
import numpy as np


def supplier_risk_score(supplier_id: str, delivery_history: list[dict]) -> dict:
    """
    Calculate supplier reliability risk score based on delivery performance and quality.

    This function computes a weighted composite score (0-100) based on three metrics:
    1. On-time delivery percentage (weight 0.4) — reliability
    2. Lead time variance (weight 0.3) — consistency
    3. Average quality score (weight 0.3) — product quality

    Args:
        supplier_id: Unique identifier for the supplier.
        delivery_history: List of delivery records, each containing:
                         - order_id: str (unique order identifier)
                         - promised_date: str (YYYY-MM-DD format)
                         - actual_date: str (YYYY-MM-DD format) or None (not delivered)
                         - quality_rating: int (1-10 scale)

    Returns:
        dict with keys:
            - supplier_id: str — the input supplier identifier.
            - score: float | None — composite risk score (0-100). None if no valid data.
            - breakdown: dict with components:
                * on_time_delivery_pct: float (0-100)
                * lead_time_variance_days: float (standard deviation of days)
                * avg_quality_score: float (0-100, based on 1-10 rating scale)
            - risk_category: str — "low" (score >= 70), "medium" (>= 40),
                            "high" (< 40), or "unknown" (no valid data).

    Raises:
        KeyError: If delivery_history items missing required keys.
        ValueError: If date formats are invalid or quality_rating out of 1-10 range.
        TypeError: If delivery_history is not a list or contains non-dict items.
    """
    # Input validation
    if not isinstance(delivery_history, list):
        raise TypeError(f"delivery_history must be list, got {type(delivery_history).__name__}")

    # Handle empty delivery history
    if len(delivery_history) == 0:
        return {
            "supplier_id": supplier_id,
            "score": None,
            "breakdown": {
                "on_time_delivery_pct": None,
                "lead_time_variance_days": None,
                "avg_quality_score": None,
            },
            "risk_category": "unknown",
        }

    # =========================================================================
    # Validate and extract delivery data
    # =========================================================================
    delivered_orders: list[dict] = []
    quality_ratings: list[int] = []

    for i, record in enumerate(delivery_history):
        if not isinstance(record, dict):
            raise TypeError(f"delivery_history[{i}] must be dict, got {type(record).__name__}")

        # Validate required keys
        required_keys = {"order_id", "promised_date", "actual_date", "quality_rating"}
        if not required_keys.issubset(record.keys()):
            missing = required_keys - record.keys()
            raise KeyError(f"delivery_history[{i}] missing keys: {missing}")

        # Validate quality rating
        quality_rating: int = record["quality_rating"]
        if not isinstance(quality_rating, int) or quality_rating < 1 or quality_rating > 10:
            raise ValueError(
                f"delivery_history[{i}]['quality_rating'] must be int 1-10, got {quality_rating}"
            )
        quality_ratings.append(quality_rating)

        # Process delivered orders, and also undelivered orders that are overdue
        if record["actual_date"] is not None:
            try:
                promised = datetime.strptime(record["promised_date"], "%Y-%m-%d").date()
                actual = datetime.strptime(record["actual_date"], "%Y-%m-%d").date()
                delivered_orders.append({
                    "promised_date": promised,
                    "actual_date": actual,
                })
            except ValueError as e:
                raise ValueError(
                    f"delivery_history[{i}] has invalid date format (expected YYYY-MM-DD): {e}"
                )
        else:
            try:
                promised = datetime.strptime(record["promised_date"], "%Y-%m-%d").date()
                today = datetime.now().date()
                if today > promised:
                    # Order is overdue but not yet delivered.
                    # Use today's date as a conservative 'actual' date to penalize the supplier.
                    delivered_orders.append({
                        "promised_date": promised,
                        "actual_date": today,
                    })
            except ValueError as e:
                raise ValueError(
                    f"delivery_history[{i}] has invalid date format (expected YYYY-MM-DD): {e}"
                )

    # =========================================================================
    # Calculate on-time delivery percentage
    # =========================================================================
    if len(delivered_orders) == 0:
        # No delivered orders, cannot calculate on-time percentage
        on_time_delivery_pct: Optional[float] = None
    else:
        on_time_count: int = sum(
            1 for order in delivered_orders if order["actual_date"] <= order["promised_date"]
        )
        on_time_delivery_pct = (on_time_count / len(delivered_orders)) * 100

    # =========================================================================
    # Calculate lead time variance
    # =========================================================================
    if len(delivered_orders) == 0:
        # No delivered orders, cannot calculate variance
        lead_time_variance_days: Optional[float] = None
    else:
        # Calculate lead time (days late/early): actual_date - promised_date
        lead_times: list[int] = [
            (order["actual_date"] - order["promised_date"]).days
            for order in delivered_orders
        ]
        # Standard deviation of lead times
        lead_time_variance_days = float(np.std(lead_times)) if len(lead_times) > 0 else 0.0

    # =========================================================================
    # Calculate average quality score (normalize to 0-100)
    # =========================================================================
    avg_quality_rating: float = np.mean(quality_ratings)
    avg_quality_score: float = avg_quality_rating * 10  # 1-10 rating → 10-100 score

    # =========================================================================
    # Calculate composite risk score (weighted average)
    # =========================================================================
    # Handle cases where some metrics may be None (no delivered orders)
    if on_time_delivery_pct is None or lead_time_variance_days is None:
        # Insufficient data: return None for score
        score: Optional[float] = None
    else:
        # Normalize lead_time_variance to 0-100 score
        # 0 days variance = 100 (perfect consistency)
        # 15+ days variance = 0 (terrible consistency)
        lead_time_score: float = _normalize_variance_to_score(lead_time_variance_days)

        # Weighted composite score
        score = (
            on_time_delivery_pct * 0.4 +
            lead_time_score * 0.3 +
            avg_quality_score * 0.3
        )

    # =========================================================================
    # Classify risk category
    # =========================================================================
    risk_category: str = _classify_risk_category(score)

    return {
        "supplier_id": supplier_id,
        "score": score,
        "breakdown": {
            "on_time_delivery_pct": on_time_delivery_pct,
            "lead_time_variance_days": lead_time_variance_days,
            "avg_quality_score": avg_quality_score,
        },
        "risk_category": risk_category,
    }


def _normalize_variance_to_score(variance_days: float) -> float:
    """
    Normalize lead time variance (days) to a 0-100 risk score.

    Mapping:
    - 0 days variance → 100 (perfect consistency)
    - 15+ days variance → 0 (terrible consistency)
    - Linear interpolation in between

    Args:
        variance_days: Standard deviation of lead time in days (float).

    Returns:
        float: Score in range [0, 100].
    """
    if variance_days <= 0:
        return 100.0
    elif variance_days >= 15:
        return 0.0
    else:
        # Linear interpolation: score = 100 * (1 - variance_days / 15)
        score: float = 100 * (1 - variance_days / 15)
        return float(np.clip(score, 0.0, 100.0))


def _classify_risk_category(score: Optional[float]) -> str:
    """
    Classify supplier risk category based on composite score.

    Args:
        score: Composite score (0-100) or None.

    Returns:
        str: One of "low", "medium", "high", or "unknown".
    """
    if score is None:
        return "unknown"
    elif score >= 70:
        return "low"
    elif score >= 40:
        return "medium"
    else:
        return "high"
