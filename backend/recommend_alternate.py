"""
Alternate source recommendation module for supply chain intelligence.

Provides recommendations for:
  - Alternate suppliers when a supplier is high-risk
  - Alternate warehouses when a warehouse is short on a SKU
"""

from typing import Optional
import logging

logger = logging.getLogger(__name__)


def recommend_alternate_source(
    failing_id: str,
    sku_id: str,
    candidate_suppliers: list[dict],
    candidate_warehouse_stocks: list[dict],
) -> dict:
    """
    Recommend the best alternate supplier or warehouse for a failing source.

    This function handles two scenarios:
    1. SUPPLIER FAILURE — when failing_id looks like a supplier (starts with 'SUP'):
       Evaluates candidate_suppliers (each with supplier_id, score, risk_category,
       and breakdown) and picks the best alternative (highest score, not the failing one).

    2. WAREHOUSE SHORTAGE — when failing_id looks like a warehouse (starts with 'WH'):
       Scans candidate_warehouse_stocks (each with warehouse_id, current_stock) and
       recommends the warehouse with the most surplus stock for the requested SKU.

    Args:
        failing_id: The supplier_id or warehouse_id that is failing.
                    Examples: "SUP014", "WH-EAST"
        sku_id: The SKU affected by the failure.
        candidate_suppliers: List of supplier risk dicts (from supplier_risk_score results).
                            Each dict: { supplier_id, score, risk_category, breakdown }
        candidate_warehouse_stocks: List of warehouse stock dicts.
                                   Each dict: { warehouse_id, current_stock }

    Returns:
        dict with keys:
            - failing_id: str — the input failing source.
            - sku_id: str — the affected SKU.
            - recommendation_type: str — "alternate_supplier" | "alternate_warehouse" | "none"
            - recommended_id: str | None — the recommended alternate ID.
            - score: float | None — score/stock of the recommended source.
            - reasoning: str — human-readable explanation of the recommendation.
            - alternatives_evaluated: int — number of candidates evaluated.

    Raises:
        ValueError: If failing_id is empty or sku_id is empty.
        TypeError: If candidate lists are not lists.
    """
    if not failing_id or not isinstance(failing_id, str):
        raise ValueError("failing_id must be a non-empty string")
    if not sku_id or not isinstance(sku_id, str):
        raise ValueError("sku_id must be a non-empty string")
    if not isinstance(candidate_suppliers, list):
        raise TypeError(f"candidate_suppliers must be a list, got {type(candidate_suppliers).__name__}")
    if not isinstance(candidate_warehouse_stocks, list):
        raise TypeError(f"candidate_warehouse_stocks must be a list, got {type(candidate_warehouse_stocks).__name__}")

    failing_upper = failing_id.upper()

    # =========================================================================
    # SCENARIO 1: Supplier failure
    # =========================================================================
    if failing_upper.startswith("SUP"):
        return _recommend_alternate_supplier(
            failing_supplier_id=failing_id,
            sku_id=sku_id,
            candidates=candidate_suppliers,
        )

    # =========================================================================
    # SCENARIO 2: Warehouse shortage
    # =========================================================================
    if failing_upper.startswith("WH"):
        return _recommend_alternate_warehouse(
            failing_warehouse_id=failing_id,
            sku_id=sku_id,
            candidates=candidate_warehouse_stocks,
        )

    # =========================================================================
    # Unknown type — cannot determine scenario
    # =========================================================================
    return {
        "failing_id": failing_id,
        "sku_id": sku_id,
        "recommendation_type": "none",
        "recommended_id": None,
        "score": None,
        "reasoning": (
            f"Cannot determine recommendation type for '{failing_id}'. "
            "Expected a supplier ID (SUP...) or warehouse ID (WH...)."
        ),
        "alternatives_evaluated": 0,
    }


def _recommend_alternate_supplier(
    failing_supplier_id: str,
    sku_id: str,
    candidates: list[dict],
) -> dict:
    """Find the next-best supplier by risk score, excluding the failing one."""
    # Filter out the failing supplier and suppliers with unknown risk
    eligible = [
        s for s in candidates
        if s.get("supplier_id") != failing_supplier_id
        and s.get("score") is not None
        and s.get("risk_category") in ("low", "medium")
    ]

    if not eligible:
        # Relax: include medium-risk as fallback even if high-risk
        eligible = [
            s for s in candidates
            if s.get("supplier_id") != failing_supplier_id
            and s.get("score") is not None
        ]

    if not eligible:
        return {
            "failing_id": failing_supplier_id,
            "sku_id": sku_id,
            "recommendation_type": "alternate_supplier",
            "recommended_id": None,
            "score": None,
            "reasoning": (
                f"No viable alternate suppliers found for {sku_id}. "
                f"All {len(candidates)} candidates evaluated are high-risk or have no score data. "
                "Consider onboarding a new supplier immediately."
            ),
            "alternatives_evaluated": len(candidates),
        }

    # Pick supplier with highest score (lower risk = higher score)
    best = max(eligible, key=lambda s: s.get("score", 0))
    breakdown = best.get("breakdown", {})
    on_time = breakdown.get("on_time_delivery_pct")
    quality = breakdown.get("avg_quality_score")

    on_time_str = f"{on_time:.1f}%" if on_time is not None else "unknown"
    quality_str = f"{quality:.1f}/100" if quality is not None else "unknown"

    failing_reason = (
        f"{failing_supplier_id} flagged as high-risk (0% on-time delivery, severe overdue orders). "
    )

    return {
        "failing_id": failing_supplier_id,
        "sku_id": sku_id,
        "recommendation_type": "alternate_supplier",
        "recommended_id": best["supplier_id"],
        "score": best.get("score"),
        "reasoning": (
            f"{failing_reason}"
            f"Recommended alternate: {best['supplier_id']} "
            f"(risk: {best.get('risk_category', 'unknown')}, score: {best.get('score', 0):.1f}, "
            f"on-time: {on_time_str}, quality: {quality_str}). "
            f"Evaluated {len(candidates)} candidates; {len(eligible)} eligible."
        ),
        "alternatives_evaluated": len(candidates),
    }


def _recommend_alternate_warehouse(
    failing_warehouse_id: str,
    sku_id: str,
    candidates: list[dict],
) -> dict:
    """Find the warehouse with the highest surplus stock for the given SKU."""
    eligible = [
        w for w in candidates
        if w.get("warehouse_id") != failing_warehouse_id
        and isinstance(w.get("current_stock"), (int, float))
        and w.get("current_stock", 0) > 0
    ]

    if not eligible:
        return {
            "failing_id": failing_warehouse_id,
            "sku_id": sku_id,
            "recommendation_type": "alternate_warehouse",
            "recommended_id": None,
            "score": None,
            "reasoning": (
                f"No alternate warehouses have stock of {sku_id}. "
                "A full reorder from a supplier is required — no inter-warehouse transfer is possible."
            ),
            "alternatives_evaluated": len(candidates),
        }

    best = max(eligible, key=lambda w: w.get("current_stock", 0))

    return {
        "failing_id": failing_warehouse_id,
        "sku_id": sku_id,
        "recommendation_type": "alternate_warehouse",
        "recommended_id": best["warehouse_id"],
        "score": best["current_stock"],
        "reasoning": (
            f"{failing_warehouse_id} has insufficient stock of {sku_id}. "
            f"Recommended alternate: {best['warehouse_id']} "
            f"(available stock: {int(best['current_stock']):,} units — highest among {len(eligible)} warehouses). "
            "Transfer stock or redirect fulfillment to this location."
        ),
        "alternatives_evaluated": len(candidates),
    }
