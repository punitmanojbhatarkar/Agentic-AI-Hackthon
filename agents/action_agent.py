"""
Action proposal agent for supply chain risk response.

Converts risk findings (stockout alerts, supplier issues) into
structured action proposals with reasoning and approval workflow.
"""

import logging
from datetime import datetime
from typing import Literal
from uuid import uuid4

logger = logging.getLogger(__name__)


def propose_action(
    finding: dict,
    finding_type: Literal["stockout", "supplier_risk"],
) -> dict:
    """
    Propose a corrective action based on a risk finding.

    This function converts supply chain risk findings into structured action
    proposals. Each proposal is assigned a unique ID, timestamped, and includes
    detailed reasoning for the proposed action.

    Action types:
    - "reorder": Emergency inventory procurement
    - "switch_supplier": Supplier diversification / fallback activation

    Args:
        finding: Risk finding dict (output from predict_stockout or supplier_risk_score).
                For "stockout": {
                    "sku_id": str,
                    "warehouse_id": str,
                    "days_until_stockout": float,
                    "current_stock": int,
                    "recommended_reorder_quantity": int,
                    "risk_level": "critical" | "high"
                }
                For "supplier_risk": {
                    "supplier_id": str,
                    "score": float (0-100),
                    "risk_category": "high",
                    "breakdown": {
                        "on_time_delivery_pct": float,
                        "lead_time_variance_days": float,
                        "avg_quality_score": float
                    }
                }
        finding_type: Type of finding ("stockout" or "supplier_risk").

    Returns:
        dict with keys:
            - action_id: str — UUID4 identifier for tracking
            - action_type: str — "reorder" or "switch_supplier"
            - details: dict — Action-specific parameters
              For "reorder": {sku_id, warehouse_id, quantity, urgency_level}
              For "switch_supplier": {supplier_id, reason, risk_score}
            - status: str — "pending_approval" (workflow state)
            - created_by: str — "agent" (audit trail)
            - reasoning: str — 2-3 sentence explanation with specific numbers
            - created_at: str — ISO timestamp (YYYY-MM-DDTHH:MM:SSZ)

    Raises:
        ValueError: If finding_type not in ["stockout", "supplier_risk"]
        KeyError: If finding missing required keys for its type
        TypeError: If finding is not a dict

    Error Handling:
        - Invalid finding_type: raises ValueError with clear message
        - Missing required fields: raises KeyError listing missing fields
        - Type mismatches: raises TypeError with context

    Example:
        >>> # Stockout action
        >>> stockout_finding = {
        ...     "sku_id": "SKU-WIDGET-100",
        ...     "warehouse_id": "WH-MAIN",
        ...     "days_until_stockout": 2.5,
        ...     "current_stock": 250,
        ...     "recommended_reorder_quantity": 1400,
        ...     "risk_level": "critical"
        ... }
        >>> action = propose_action(stockout_finding, "stockout")
        >>> print(action["action_type"])
        "reorder"
        >>> print(action["status"])
        "pending_approval"

        >>> # Supplier risk action
        >>> supplier_finding = {
        ...     "supplier_id": "SUP-VENDOR-B",
        ...     "score": 35.0,
        ...     "risk_category": "high",
        ...     "breakdown": {
        ...         "on_time_delivery_pct": 60.0,
        ...         "lead_time_variance_days": 3.2,
        ...         "avg_quality_score": 60.0
        ...     }
        ... }
        >>> action = propose_action(supplier_finding, "supplier_risk")
        >>> print(action["action_type"])
        "switch_supplier"
    """
    # =========================================================================
    # Input validation
    # =========================================================================
    if not isinstance(finding, dict):
        raise TypeError(f"finding must be dict, got {type(finding).__name__}")

    if finding_type not in ["stockout", "supplier_risk"]:
        raise ValueError(
            f"finding_type must be 'stockout' or 'supplier_risk', got '{finding_type}'"
        )

    # =========================================================================
    # Generate action based on finding type
    # =========================================================================
    if finding_type == "stockout":
        return _propose_reorder_action(finding)
    else:  # finding_type == "supplier_risk"
        return _propose_supplier_switch_action(finding)


# ═══════════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS: ACTION-SPECIFIC PROPOSERS
# ═══════════════════════════════════════════════════════════════════════════════


def _propose_reorder_action(finding: dict) -> dict:
    """
    Propose an emergency reorder action for stockout risk.

    Args:
        finding: Stockout prediction result dict

    Returns:
        dict: Complete action proposal

    Raises:
        KeyError: If finding missing required fields
    """
    # Validate required fields
    required_fields = {
        "sku_id",
        "warehouse_id",
        "current_stock",
        "recommended_reorder_quantity",
        "days_until_stockout",
        "risk_level",
    }
    missing = required_fields - set(finding.keys())
    if missing:
        raise KeyError(
            f"stockout finding missing required fields: {missing}"
        )

    sku_id: str = finding["sku_id"]
    warehouse_id: str = finding["warehouse_id"]
    current_stock: int = finding["current_stock"]
    recommended_qty: int = finding["recommended_reorder_quantity"]
    days_until: float = finding["days_until_stockout"]
    risk_level: str = finding["risk_level"]

    # Determine urgency level
    if risk_level == "critical" or days_until <= 3:
        urgency_level = "CRITICAL"
    elif days_until <= 7:
        urgency_level = "HIGH"
    else:
        urgency_level = "MEDIUM"

    # Generate reasoning
    reasoning = _build_reorder_reasoning(
        sku_id, warehouse_id, current_stock, recommended_qty, days_until, risk_level
    )

    # Generate action
    action_id: str = str(uuid4())
    created_at: str = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

    action: dict = {
        "action_id": action_id,
        "action_type": "reorder",
        "details": {
            "sku_id": sku_id,
            "warehouse_id": warehouse_id,
            "quantity": recommended_qty,
            "urgency_level": urgency_level,
            "current_stock": current_stock,
            "days_until_stockout": round(days_until, 1),
        },
        "status": "pending_approval",
        "created_by": "agent",
        "reasoning": reasoning,
        "created_at": created_at,
    }

    logger.info(
        f"Proposed reorder action {action_id}: {sku_id} @ {warehouse_id}, "
        f"{recommended_qty} units, urgency={urgency_level}"
    )

    return action


def _propose_supplier_switch_action(finding: dict) -> dict:
    """
    Propose a supplier switch action for reliability risk.

    Args:
        finding: Supplier risk score result dict

    Returns:
        dict: Complete action proposal

    Raises:
        KeyError: If finding missing required fields
    """
    # Validate required fields
    required_fields = {"supplier_id", "score", "risk_category", "breakdown"}
    missing = required_fields - set(finding.keys())
    if missing:
        raise KeyError(
            f"supplier_risk finding missing required fields: {missing}"
        )

    supplier_id: str = finding["supplier_id"]
    score: float = finding["score"]
    breakdown: dict = finding["breakdown"]

    # Extract metrics
    on_time_pct: float = breakdown.get("on_time_delivery_pct", 0)
    lead_variance: float = breakdown.get("lead_time_variance_days", 0)
    quality_score: float = breakdown.get("avg_quality_score", 0)

    # Generate reason string from breakdown
    reason = _build_supplier_switch_reason(
        supplier_id, score, on_time_pct, lead_variance, quality_score
    )

    # Generate action
    action_id: str = str(uuid4())
    created_at: str = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

    action: dict = {
        "action_id": action_id,
        "action_type": "switch_supplier",
        "details": {
            "supplier_id": supplier_id,
            "reason": reason,
            "risk_score": score,
            "on_time_delivery_pct": on_time_pct,
            "lead_time_variance_days": lead_variance,
            "quality_score": quality_score,
        },
        "status": "pending_approval",
        "created_by": "agent",
        "reasoning": _build_supplier_switch_reasoning(
            supplier_id, score, on_time_pct, lead_variance, quality_score
        ),
        "created_at": created_at,
    }

    logger.info(
        f"Proposed supplier switch action {action_id}: {supplier_id}, "
        f"score={score:.1f}, on_time={on_time_pct:.0f}%"
    )

    return action


# ═══════════════════════════════════════════════════════════════════════════════
# REASONING BUILDERS (generate human-readable explanations)
# ═══════════════════════════════════════════════════════════════════════════════


def _build_reorder_reasoning(
    sku_id: str,
    warehouse_id: str,
    current_stock: int,
    recommended_qty: int,
    days_until: float,
    risk_level: str,
) -> str:
    """
    Build reasoning string for reorder action.

    Args:
        sku_id: SKU identifier
        warehouse_id: Warehouse location
        current_stock: Current inventory units
        recommended_qty: Recommended reorder quantity
        days_until: Days until stockout
        risk_level: Risk level (critical/high/medium/low)

    Returns:
        str: 2-3 sentence explanation with specific numbers
    """
    if risk_level == "critical":
        urgency = "CRITICAL situation"
    elif days_until <= 7:
        urgency = "HIGH-risk situation"
    else:
        urgency = "situation"

    reasoning = (
        f"{sku_id} at {warehouse_id} faces a {urgency} with only {current_stock} units "
        f"in stock ({days_until:.1f} days of supply remaining). "
        f"Recommended action: immediately place order for {recommended_qty} units "
        f"to restore 14-day supply buffer and prevent stockout."
    )

    return reasoning


def _build_supplier_switch_reason(
    supplier_id: str,
    score: float,
    on_time_pct: float,
    lead_variance: float,
    quality_score: float,
) -> str:
    """
    Build brief reason string for supplier switch.

    Args:
        supplier_id: Supplier identifier
        score: Risk score (0-100)
        on_time_pct: On-time delivery percentage
        lead_variance: Lead time variance (days)
        quality_score: Quality score (0-100)

    Returns:
        str: One-phrase reason
    """
    issues: list[str] = []

    if on_time_pct < 80:
        issues.append(f"only {on_time_pct:.0f}% on-time delivery")
    if lead_variance > 3:
        issues.append(f"{lead_variance:.1f}-day lead time variance")
    if quality_score < 70:
        issues.append(f"quality score {quality_score:.0f}")

    if issues:
        return f"Reliability concerns: {', '.join(issues)}"
    else:
        return f"Risk score {score:.0f} indicates supplier performance issues"


def _build_supplier_switch_reasoning(
    supplier_id: str,
    score: float,
    on_time_pct: float,
    lead_variance: float,
    quality_score: float,
) -> str:
    """
    Build reasoning string for supplier switch action.

    Args:
        supplier_id: Supplier identifier
        score: Risk score (0-100)
        on_time_pct: On-time delivery percentage
        lead_variance: Lead time variance (days)
        quality_score: Quality score (0-100)

    Returns:
        str: 2-3 sentence explanation with specific numbers
    """
    issues: list[str] = []

    if on_time_pct < 70:
        issues.append(f"poor on-time delivery ({on_time_pct:.0f}%)")
    elif on_time_pct < 85:
        issues.append(f"below-target on-time delivery ({on_time_pct:.0f}%)")

    if lead_variance > 2.5:
        issues.append(f"excessive lead time variability ({lead_variance:.1f} days)")

    if quality_score < 70:
        issues.append(f"quality concerns (score {quality_score:.0f})")

    issue_text = ", ".join(issues) if issues else "overall performance concerns"

    reasoning = (
        f"{supplier_id} has a risk score of {score:.0f}/100, indicating {issue_text}. "
        f"Recommend identifying alternative suppliers for non-critical items "
        f"and diversifying sourcing to reduce single-supplier dependency risk."
    )

    return reasoning


# ═══════════════════════════════════════════════════════════════════════════════
# BATCH ACTION PROPOSAL (helper for sweep integration)
# ═══════════════════════════════════════════════════════════════════════════════


def propose_actions_from_sweep(
    critical_stockouts: list[dict],
    risky_suppliers: list[dict],
) -> dict:
    """
    Generate action proposals from sweep findings.

    Convenience function to batch-propose actions from intelligence sweep results.

    Args:
        critical_stockouts: List of high/critical risk stockout findings
        risky_suppliers: List of high-risk supplier findings

    Returns:
        dict with keys:
            - stockout_actions: list[dict] — reorder actions
            - supplier_actions: list[dict] — supplier switch actions
            - total_actions: int — total proposed actions
            - created_at: str — ISO timestamp (batch creation time)

    Example:
        >>> from agents.sweep import run_intelligence_sweep
        >>> sweep_result = run_intelligence_sweep(...)
        >>> actions = propose_actions_from_sweep(
        ...     sweep_result["critical_stockouts"],
        ...     sweep_result["risky_suppliers"]
        ... )
        >>> print(f"Proposed {actions['total_actions']} actions")
    """
    stockout_actions: list[dict] = []
    supplier_actions: list[dict] = []

    # Propose reorder actions for each stockout
    for stockout in critical_stockouts:
        try:
            action = propose_action(stockout, "stockout")
            stockout_actions.append(action)
        except Exception as e:
            logger.error(f"Failed to propose action for stockout {stockout}: {e}")
            continue

    # Propose supplier switch actions for each risky supplier
    for supplier in risky_suppliers:
        try:
            action = propose_action(supplier, "supplier_risk")
            supplier_actions.append(action)
        except Exception as e:
            logger.error(f"Failed to propose action for supplier {supplier}: {e}")
            continue

    batch_created_at: str = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

    return {
        "stockout_actions": stockout_actions,
        "supplier_actions": supplier_actions,
        "total_actions": len(stockout_actions) + len(supplier_actions),
        "created_at": batch_created_at,
    }
