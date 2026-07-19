"""
Demand forecasting module for supply chain inventory intelligence.

Provides deterministic demand prediction using moving averages and linear regression.
"""

from typing import Optional
import numpy as np
from datetime import datetime, timedelta


def forecast_demand(sku_id: str, historical_demand: list[dict]) -> dict:
    """
    Forecast demand for the next 7 days using historical data.

    This function implements a two-stage approach:
    1. 7-day moving average as the baseline trend.
    2. Linear regression on the last 30 days (or available data if <30 days) to detect
       directional trend: "increasing", "decreasing", or "stable".
    3. Generates 7-day forecast by applying trend adjustment to the moving average.
    4. Calculates confidence score based on historical variance.

    Args:
        sku_id: Unique identifier for the stock keeping unit.
        historical_demand: List of dicts with "date" (YYYY-MM-DD) and "units_sold" (int).
                          Expected to be sorted chronologically (oldest first).
                          Typically covers the last 90 days.

    Returns:
        dict with keys:
            - sku_id: str — the input SKU identifier.
            - trend: str — "increasing", "decreasing", or "stable".
            - forecasted_daily_demand: list[float] — 7-day forecast, daily units.
            - avg_forecasted_demand: float — average of 7-day forecast.
            - confidence: float — confidence score (0.0-1.0). Higher = more reliable.

    Raises:
        ValueError: If historical_demand is empty or has invalid structure.
    """
    if not historical_demand:
        raise ValueError("historical_demand cannot be empty")

    # Extract units_sold in chronological order
    units_sold: list[int] = [entry["units_sold"] for entry in historical_demand]

    if len(units_sold) == 0:
        raise ValueError("No valid units_sold values in historical_demand")

    # =========================================================================
    # Stage 1: 7-day moving average (baseline trend)
    # =========================================================================
    baseline_avg: float = _compute_moving_average(units_sold, window=7)

    # =========================================================================
    # Stage 2: Trend detection using linear regression
    # =========================================================================
    if len(units_sold) < 14:
        # Insufficient data for regression; use simple average and low confidence
        trend: str = "stable"
        confidence: float = 0.3
        simple_avg: float = float(np.mean(units_sold))
        forecasted_daily_demand: list[float] = [simple_avg] * 7
    else:
        # Use last 30 days for trend detection (or all if less than 30)
        lookback_days: int = min(30, len(units_sold))
        recent_data: list[int] = units_sold[-lookback_days:]

        trend = _detect_trend(recent_data)
        confidence = _calculate_confidence(units_sold)
        forecasted_daily_demand = _generate_forecast(
            baseline_avg=baseline_avg,
            trend=trend,
            recent_data=recent_data,
        )

    avg_forecasted_demand: float = float(np.mean(forecasted_daily_demand))

    # =========================================================================
    # Stage 4: Demand spike detection
    # Fire if recent 30-day avg is >= 2x the prior 60-day avg
    # =========================================================================
    demand_spike_detected: bool = False
    spike_ratio: Optional[float] = None
    if len(units_sold) >= 30:
        recent_30: list[int] = units_sold[-30:]
        recent_30_avg: float = float(np.mean(recent_30))
        if len(units_sold) >= 90:
            prior_60: list[int] = units_sold[-90:-30]
        elif len(units_sold) >= 60:
            prior_60 = units_sold[-60:-30]
        else:
            prior_60 = []

        if prior_60:
            prior_avg: float = float(np.mean(prior_60))
            if prior_avg > 0:
                spike_ratio = recent_30_avg / prior_avg
                demand_spike_detected = spike_ratio >= 2.0

    return {
        "sku_id": sku_id,
        "trend": trend,
        "forecasted_daily_demand": forecasted_daily_demand,
        "avg_forecasted_demand": avg_forecasted_demand,
        "confidence": confidence,
        "demand_spike_detected": demand_spike_detected,
        "spike_ratio": round(spike_ratio, 2) if spike_ratio is not None else None,
    }


def _compute_moving_average(data: list[int], window: int) -> float:
    """
    Compute 7-day moving average of a time series.

    Args:
        data: List of demand values in chronological order.
        window: Window size for moving average (default 7).

    Returns:
        float: The moving average of the last `window` elements.
    """
    if len(data) < window:
        return float(np.mean(data))
    return float(np.mean(data[-window:]))


def _detect_trend(recent_data: list[int]) -> str:
    """
    Detect trend direction using simple linear regression.

    Fits a line to recent_data (last 30 days) and classifies based on slope:
    - Slope > 5: "increasing"
    - Slope < -5: "decreasing"
    - Otherwise: "stable"

    Args:
        recent_data: List of demand values (e.g., last 30 days).

    Returns:
        str: "increasing", "decreasing", or "stable".
    """
    if len(recent_data) < 2:
        return "stable"

    # Prepare data for regression: x = day index (0, 1, 2, ..., n-1)
    x: np.ndarray = np.arange(len(recent_data), dtype=np.float64)
    y: np.ndarray = np.array(recent_data, dtype=np.float64)

    # Manual linear regression: y = mx + b
    # m = (n*sum(xy) - sum(x)*sum(y)) / (n*sum(x^2) - (sum(x))^2)
    n: float = float(len(recent_data))
    sum_x: float = float(np.sum(x))
    sum_y: float = float(np.sum(y))
    sum_xy: float = float(np.sum(x * y))
    sum_x2: float = float(np.sum(x * x))

    denominator: float = n * sum_x2 - sum_x * sum_x
    if abs(denominator) < 1e-9:
        return "stable"

    slope: float = (n * sum_xy - sum_x * sum_y) / denominator

    # Classify trend based on slope magnitude
    threshold: float = 5.0
    if slope > threshold:
        return "increasing"
    elif slope < -threshold:
        return "decreasing"
    else:
        return "stable"


def _calculate_confidence(historical_data: list[int]) -> float:
    """
    Calculate confidence score based on historical variance.

    Lower variance (more stable demand) = higher confidence.
    Formula:
        - If mean = 0, confidence = 0.3 (edge case).
        - Otherwise: confidence = 1.0 / (1.0 + coefficient_of_variation)
        - Clipped to [0.0, 1.0].

    Args:
        historical_data: Full historical demand list.

    Returns:
        float: Confidence score in range [0.0, 1.0].
    """
    mean: float = float(np.mean(historical_data))
    std_dev: float = float(np.std(historical_data))

    if mean == 0:
        return 0.3

    coefficient_of_variation: float = std_dev / mean
    confidence: float = 1.0 / (1.0 + coefficient_of_variation)

    return float(np.clip(confidence, 0.0, 1.0))


def _generate_forecast(
    baseline_avg: float, trend: str, recent_data: list[int]
) -> list[float]:
    """
    Generate 7-day demand forecast.

    Starts with baseline_avg and applies a trend-based adjustment:
    - "increasing": +2% per day (cumulative).
    - "decreasing": -2% per day (cumulative).
    - "stable": no adjustment (flat forecast).

    Args:
        baseline_avg: The 7-day moving average baseline.
        trend: "increasing", "decreasing", or "stable".
        recent_data: Recent demand data (used for context).

    Returns:
        list[float]: 7-day forecast, one value per day.
    """
    forecast: list[float] = []
    daily_adjustment: float = 0.02  # 2% per day

    for day in range(7):
        if trend == "increasing":
            adjusted_demand: float = baseline_avg * ((1.0 + daily_adjustment) ** (day + 1))
        elif trend == "decreasing":
            adjusted_demand: float = baseline_avg * ((1.0 - daily_adjustment) ** (day + 1))
        else:  # "stable"
            adjusted_demand: float = baseline_avg

        forecast.append(max(adjusted_demand, 0.0))  # Ensure non-negative

    return forecast
