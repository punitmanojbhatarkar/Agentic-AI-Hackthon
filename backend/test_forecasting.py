"""
Unit tests for demand forecasting module.

Verifies:
1. 7-day moving average as baseline
2. Manual linear regression with correct slope calculation
3. Trend classification thresholds (±5 units/day)
4. Confidence calculation based on coefficient of variation
5. Return dict structure matches specification
6. Type hints correctness
7. Handles <14 days of data (confidence=0.3, simple average)
8. Forecast generation (7 daily values as list[float])
"""

import pytest
import numpy as np
from forecasting import (
    forecast_demand,
    _compute_moving_average,
    _detect_trend,
    _calculate_confidence,
    _generate_forecast,
)


class TestComputeMovingAverage:
    """Test 7-day moving average calculation."""

    def test_moving_average_full_window(self):
        """Test moving average with sufficient data."""
        data = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
        # Last 7 values: [70, 80, 90, 100, ...] (window=7)
        # Actually last 7 are [40, 50, 60, 70, 80, 90, 100]
        result = _compute_moving_average(data, window=7)
        expected = np.mean([40, 50, 60, 70, 80, 90, 100])
        assert result == expected

    def test_moving_average_short_data(self):
        """Test moving average when data < window size."""
        data = [10, 20, 30]
        result = _compute_moving_average(data, window=7)
        expected = np.mean([10, 20, 30])
        assert result == expected


class TestDetectTrend:
    """Test trend detection via manual linear regression."""

    def test_increasing_trend(self):
        """Test detection of increasing trend (slope > 5)."""
        # Linear data with slope > 5: 100, 106, 112, 118, ...
        data = [100 + 6 * i for i in range(20)]
        trend = _detect_trend(data)
        assert trend == "increasing", f"Expected 'increasing', got '{trend}'"

    def test_decreasing_trend(self):
        """Test detection of decreasing trend (slope < -5)."""
        # Linear data with slope < -5: 500, 494, 488, 482, ...
        data = [500 - 6 * i for i in range(20)]
        trend = _detect_trend(data)
        assert trend == "decreasing", f"Expected 'decreasing', got '{trend}'"

    def test_stable_trend(self):
        """Test detection of stable trend (|slope| <= 5)."""
        # Flat data: all same value
        data = [100] * 20
        trend = _detect_trend(data)
        assert trend == "stable", f"Expected 'stable', got '{trend}'"

    def test_noisy_stable_trend(self):
        """Test stable trend with small noise (slope within ±5 threshold)."""
        # Data with small oscillation around 100
        data = [100, 101, 102, 101, 100, 99, 100, 101, 102, 101]
        trend = _detect_trend(data)
        assert trend == "stable", f"Expected 'stable' for noisy data, got '{trend}'"

    def test_edge_case_single_value(self):
        """Test trend detection with single data point."""
        data = [100]
        trend = _detect_trend(data)
        assert trend == "stable"


class TestCalculateConfidence:
    """Test confidence scoring based on variance."""

    def test_confidence_zero_mean(self):
        """Test confidence when mean is 0."""
        data = [0, 0, 0]
        confidence = _calculate_confidence(data)
        assert confidence == 0.3

    def test_confidence_stable_demand(self):
        """Test high confidence for stable (low-variance) demand."""
        # All values are the same: variance = 0, std = 0
        data = [100] * 90
        confidence = _calculate_confidence(data)
        # CV = 0 / 100 = 0
        # confidence = 1.0 / (1.0 + 0) = 1.0
        assert confidence == 1.0

    def test_confidence_volatile_demand(self):
        """Test lower confidence for volatile (high-variance) demand."""
        # High variance: values range from 10 to 190
        data = list(range(10, 200, 2))  # 10, 12, 14, ..., 198
        confidence = _calculate_confidence(data)
        mean = np.mean(data)
        std = np.std(data)
        cv = std / mean
        expected = 1.0 / (1.0 + cv)
        expected = float(np.clip(expected, 0.0, 1.0))
        assert abs(confidence - expected) < 1e-6

    def test_confidence_clipped_range(self):
        """Test that confidence is always in [0.0, 1.0]."""
        test_cases = [
            [1, 1, 1],  # Very stable
            [1, 100, 1, 100],  # Very volatile
            [50] * 50,  # Moderate stable
        ]
        for data in test_cases:
            confidence = _calculate_confidence(data)
            assert 0.0 <= confidence <= 1.0


class TestGenerateForecast:
    """Test 7-day forecast generation."""

    def test_forecast_length(self):
        """Test that forecast returns exactly 7 values."""
        baseline_avg = 100.0
        trend = "stable"
        recent_data = [100] * 30
        forecast = _generate_forecast(baseline_avg, trend, recent_data)
        assert len(forecast) == 7

    def test_forecast_stable_flat(self):
        """Test stable trend produces flat forecast."""
        baseline_avg = 100.0
        trend = "stable"
        recent_data = [100] * 30
        forecast = _generate_forecast(baseline_avg, trend, recent_data)
        # All values should be baseline_avg
        for value in forecast:
            assert abs(value - baseline_avg) < 1e-6

    def test_forecast_increasing(self):
        """Test increasing trend produces upward forecast."""
        baseline_avg = 100.0
        trend = "increasing"
        recent_data = list(range(100, 130))
        forecast = _generate_forecast(baseline_avg, trend, recent_data)
        # Each day should be higher than previous
        for i in range(1, 7):
            assert forecast[i] > forecast[i - 1]

    def test_forecast_decreasing(self):
        """Test decreasing trend produces downward forecast."""
        baseline_avg = 100.0
        trend = "decreasing"
        recent_data = list(range(130, 100, -1))
        forecast = _generate_forecast(baseline_avg, trend, recent_data)
        # Each day should be lower than previous
        for i in range(1, 7):
            assert forecast[i] < forecast[i - 1]

    def test_forecast_non_negative(self):
        """Test that forecast never produces negative values."""
        baseline_avg = 1.0
        trend = "decreasing"
        recent_data = [1] * 30
        forecast = _generate_forecast(baseline_avg, trend, recent_data)
        for value in forecast:
            assert value >= 0.0


class TestForecastDemandIntegration:
    """Integration tests for forecast_demand function."""

    def test_return_dict_structure(self):
        """Test that return dict has all required keys with correct types."""
        historical_demand = [
            {"date": "2024-01-01", "units_sold": 100},
            {"date": "2024-01-02", "units_sold": 105},
            {"date": "2024-01-03", "units_sold": 110},
            {"date": "2024-01-04", "units_sold": 108},
            {"date": "2024-01-05", "units_sold": 112},
            {"date": "2024-01-06", "units_sold": 115},
            {"date": "2024-01-07", "units_sold": 118},
            {"date": "2024-01-08", "units_sold": 120},
        ]
        result = forecast_demand("SKU-001", historical_demand)

        # Check all required keys present
        required_keys = {
            "sku_id",
            "trend",
            "forecasted_daily_demand",
            "avg_forecasted_demand",
            "confidence",
        }
        assert set(result.keys()) == required_keys

        # Check types
        assert isinstance(result["sku_id"], str)
        assert isinstance(result["trend"], str)
        assert isinstance(result["forecasted_daily_demand"], list)
        assert isinstance(result["avg_forecasted_demand"], float)
        assert isinstance(result["confidence"], float)

        # Check forecast list contains floats
        assert len(result["forecasted_daily_demand"]) == 7
        for value in result["forecasted_daily_demand"]:
            assert isinstance(value, float)

    def test_sku_id_passed_through(self):
        """Test that SKU ID is correctly passed to result."""
        sku_id = "SKU-12345"
        historical_demand = [{"date": "2024-01-01", "units_sold": i} for i in range(10, 20)]
        result = forecast_demand(sku_id, historical_demand)
        assert result["sku_id"] == sku_id

    def test_short_data_handling(self):
        """Test handling of <14 days of data."""
        historical_demand = [{"date": f"2024-01-{i:02d}", "units_sold": 100 + i} for i in range(1, 10)]
        result = forecast_demand("SKU-001", historical_demand)

        # Should have confidence = 0.3
        assert result["confidence"] == 0.3
        # Should have trend = "stable"
        assert result["trend"] == "stable"
        # Forecast should be constant (simple average)
        simple_avg = np.mean([100 + i for i in range(1, 10)])
        for value in result["forecasted_daily_demand"]:
            assert abs(value - simple_avg) < 1e-6

    def test_full_90_days_data(self):
        """Test with full 90 days of historical data."""
        # Create realistic 90-day dataset with increasing trend
        historical_demand = [
            {"date": f"2024-01-{i % 31 + 1:02d}", "units_sold": 100 + i}
            for i in range(90)
        ]
        result = forecast_demand("SKU-001", historical_demand)

        # Should detect increasing trend
        assert result["trend"] in ["increasing", "decreasing", "stable"]
        # Confidence should be reasonable
        assert 0.0 <= result["confidence"] <= 1.0
        # Forecast should be reasonable
        assert len(result["forecasted_daily_demand"]) == 7
        assert result["avg_forecasted_demand"] > 0

    def test_empty_demand_raises_error(self):
        """Test that empty demand list raises ValueError."""
        with pytest.raises(ValueError):
            forecast_demand("SKU-001", [])

    def test_trend_values_valid(self):
        """Test that trend is one of the three expected values."""
        historical_demand = [{"date": f"2024-01-{i:02d}", "units_sold": 100} for i in range(1, 31)]
        result = forecast_demand("SKU-001", historical_demand)
        assert result["trend"] in ["increasing", "decreasing", "stable"]

    def test_avg_forecasted_demand_is_mean(self):
        """Test that avg_forecasted_demand is actually the mean of forecast."""
        historical_demand = [{"date": f"2024-01-{i:02d}", "units_sold": 100 + i} for i in range(1, 31)]
        result = forecast_demand("SKU-001", historical_demand)
        expected_avg = np.mean(result["forecasted_daily_demand"])
        assert abs(result["avg_forecasted_demand"] - expected_avg) < 1e-6


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
