"""
Unit tests for inventory management module.

Verifies:
1. Stockout prediction calculation (current_stock / avg_demand)
2. Risk level classification (critical, high, medium, low)
3. Recommended reorder quantity (14-day supply buffer)
4. Return dict structure matches specification
5. Type hints correctness
6. Division-by-zero handling (avg_forecasted_demand = 0)
7. Negative stock handling
8. Edge cases (current_stock = 0, exactly at thresholds)
"""

import pytest
from inventory import predict_stockout, _classify_risk_level


class TestClassifyRiskLevel:
    """Test risk level classification logic."""

    def test_critical_risk_at_3_days(self):
        """Test critical risk at exactly 3 days."""
        risk = _classify_risk_level(3.0)
        assert risk == "critical"

    def test_critical_risk_below_3_days(self):
        """Test critical risk below 3 days."""
        risk = _classify_risk_level(1.5)
        assert risk == "critical"

    def test_critical_risk_at_0_days(self):
        """Test critical risk at 0 days (immediate stockout)."""
        risk = _classify_risk_level(0.0)
        assert risk == "critical"

    def test_high_risk_at_7_days(self):
        """Test high risk at exactly 7 days."""
        risk = _classify_risk_level(7.0)
        assert risk == "high"

    def test_high_risk_between_3_and_7(self):
        """Test high risk between 3 and 7 days."""
        risk = _classify_risk_level(5.0)
        assert risk == "high"

    def test_medium_risk_at_14_days(self):
        """Test medium risk at exactly 14 days."""
        risk = _classify_risk_level(14.0)
        assert risk == "medium"

    def test_medium_risk_between_7_and_14(self):
        """Test medium risk between 7 and 14 days."""
        risk = _classify_risk_level(10.0)
        assert risk == "medium"

    def test_low_risk_above_14_days(self):
        """Test low risk above 14 days."""
        risk = _classify_risk_level(30.0)
        assert risk == "low"

    def test_low_risk_no_demand(self):
        """Test low risk when no demand (None)."""
        risk = _classify_risk_level(None)
        assert risk == "low"

    def test_high_risk_above_7_below_14(self):
        """Test boundary: just above 7 should be medium."""
        risk = _classify_risk_level(7.1)
        assert risk == "medium"

    def test_critical_risk_just_below_3(self):
        """Test boundary: just below 3 should still be critical."""
        risk = _classify_risk_level(2.9)
        assert risk == "critical"


class TestPredictStockoutInputValidation:
    """Test input validation and error handling."""

    def test_invalid_current_stock_type_float(self):
        """Test that float current_stock raises TypeError."""
        forecast = {"avg_forecasted_demand": 100.0}
        with pytest.raises(TypeError):
            predict_stockout("SKU-001", "WH-001", 50.5, forecast)

    def test_invalid_current_stock_type_string(self):
        """Test that string current_stock raises TypeError."""
        forecast = {"avg_forecasted_demand": 100.0}
        with pytest.raises(TypeError):
            predict_stockout("SKU-001", "WH-001", "50", forecast)

    def test_negative_current_stock(self):
        """Test that negative current_stock raises ValueError."""
        forecast = {"avg_forecasted_demand": 100.0}
        with pytest.raises(ValueError):
            predict_stockout("SKU-001", "WH-001", -10, forecast)

    def test_missing_avg_forecasted_demand_key(self):
        """Test that missing avg_forecasted_demand raises KeyError."""
        forecast = {"trend": "stable", "confidence": 0.9}
        with pytest.raises(KeyError):
            predict_stockout("SKU-001", "WH-001", 100, forecast)

    def test_invalid_forecast_result_type(self):
        """Test that non-dict forecast_result raises TypeError."""
        with pytest.raises(TypeError):
            predict_stockout("SKU-001", "WH-001", 100, "not-a-dict")

    def test_invalid_forecast_result_list(self):
        """Test that list forecast_result raises TypeError."""
        with pytest.raises(TypeError):
            predict_stockout("SKU-001", "WH-001", 100, [100.0])


class TestPredictStockoutCalculations:
    """Test core calculation logic."""

    def test_days_until_stockout_basic(self):
        """Test basic days_until_stockout calculation."""
        forecast = {"avg_forecasted_demand": 100.0}
        result = predict_stockout("SKU-001", "WH-001", 500, forecast)
        
        # days_until_stockout = 500 / 100 = 5 days
        assert result["days_until_stockout"] == 5.0

    def test_days_until_stockout_fractional(self):
        """Test days_until_stockout with fractional result."""
        forecast = {"avg_forecasted_demand": 30.0}
        result = predict_stockout("SKU-001", "WH-001", 100, forecast)
        
        # days_until_stockout = 100 / 30 ≈ 3.333...
        expected = 100 / 30
        assert abs(result["days_until_stockout"] - expected) < 1e-6

    def test_days_until_stockout_zero_stock(self):
        """Test days_until_stockout when current_stock is 0."""
        forecast = {"avg_forecasted_demand": 100.0}
        result = predict_stockout("SKU-001", "WH-001", 0, forecast)
        
        # days_until_stockout = 0 / 100 = 0
        assert result["days_until_stockout"] == 0.0

    def test_days_until_stockout_zero_demand(self):
        """Test days_until_stockout when avg_forecasted_demand is 0."""
        forecast = {"avg_forecasted_demand": 0.0}
        result = predict_stockout("SKU-001", "WH-001", 500, forecast)
        
        # No demand: days_until_stockout = None
        assert result["days_until_stockout"] is None

    def test_days_until_stockout_negative_demand(self):
        """Test days_until_stockout when avg_forecasted_demand is negative."""
        forecast = {"avg_forecasted_demand": -50.0}
        result = predict_stockout("SKU-001", "WH-001", 500, forecast)
        
        # Negative demand treated as no demand: None
        assert result["days_until_stockout"] is None

    def test_recommended_reorder_quantity_basic(self):
        """Test basic recommended reorder quantity calculation."""
        forecast = {"avg_forecasted_demand": 100.0}
        result = predict_stockout("SKU-001", "WH-001", 500, forecast)
        
        # target_stock = 100 * 14 = 1400
        # recommended = 1400 - 500 = 900
        assert result["recommended_reorder_quantity"] == 900

    def test_recommended_reorder_quantity_stock_exceeds_target(self):
        """Test recommended reorder when stock already exceeds 14-day target."""
        forecast = {"avg_forecasted_demand": 100.0}
        result = predict_stockout("SKU-001", "WH-001", 2000, forecast)
        
        # target_stock = 100 * 14 = 1400
        # recommended = 1400 - 2000 = -600 → clamped to 0
        assert result["recommended_reorder_quantity"] == 0

    def test_recommended_reorder_quantity_rounding(self):
        """Test recommended reorder rounding to nearest int."""
        forecast = {"avg_forecasted_demand": 33.33}
        result = predict_stockout("SKU-001", "WH-001", 100, forecast)
        
        # target_stock = 33.33 * 14 = 466.62
        # recommended = 466.62 - 100 = 366.62 → rounds to 367
        expected = int(round(33.33 * 14 - 100))
        assert result["recommended_reorder_quantity"] == expected

    def test_recommended_reorder_quantity_zero_demand(self):
        """Test recommended reorder when demand is 0."""
        forecast = {"avg_forecasted_demand": 0.0}
        result = predict_stockout("SKU-001", "WH-001", 100, forecast)
        
        # target_stock = 0 * 14 = 0
        # recommended = 0 - 100 = -100 → clamped to 0
        assert result["recommended_reorder_quantity"] == 0


class TestPredictStockoutReturnStructure:
    """Test return dict structure and types."""

    def test_return_dict_has_all_keys(self):
        """Test that return dict has all required keys."""
        forecast = {"avg_forecasted_demand": 50.0}
        result = predict_stockout("SKU-001", "WH-001", 200, forecast)
        
        required_keys = {
            "sku_id",
            "warehouse_id",
            "current_stock",
            "days_until_stockout",
            "risk_level",
            "recommended_reorder_quantity",
        }
        assert set(result.keys()) == required_keys

    def test_return_dict_types(self):
        """Test that return values have correct types."""
        forecast = {"avg_forecasted_demand": 100.0}
        result = predict_stockout("SKU-001", "WH-001", 500, forecast)
        
        assert isinstance(result["sku_id"], str)
        assert isinstance(result["warehouse_id"], str)
        assert isinstance(result["current_stock"], int)
        assert isinstance(result["days_until_stockout"], (float, type(None)))
        assert isinstance(result["risk_level"], str)
        assert isinstance(result["recommended_reorder_quantity"], int)

    def test_sku_id_passthrough(self):
        """Test that SKU ID is correctly passed through."""
        sku_id = "SKU-CUSTOM-12345"
        forecast = {"avg_forecasted_demand": 100.0}
        result = predict_stockout(sku_id, "WH-001", 500, forecast)
        
        assert result["sku_id"] == sku_id

    def test_warehouse_id_passthrough(self):
        """Test that warehouse ID is correctly passed through."""
        warehouse_id = "WH-CUSTOM-789"
        forecast = {"avg_forecasted_demand": 100.0}
        result = predict_stockout("SKU-001", warehouse_id, 500, forecast)
        
        assert result["warehouse_id"] == warehouse_id

    def test_current_stock_passthrough(self):
        """Test that current stock is correctly passed through."""
        current_stock = 12345
        forecast = {"avg_forecasted_demand": 100.0}
        result = predict_stockout("SKU-001", "WH-001", current_stock, forecast)
        
        assert result["current_stock"] == current_stock


class TestPredictStockoutRiskLevel:
    """Test risk level assignment in full context."""

    def test_critical_risk_with_high_demand(self):
        """Test critical risk when stockout is imminent."""
        forecast = {"avg_forecasted_demand": 100.0}
        result = predict_stockout("SKU-001", "WH-001", 200, forecast)
        
        # days_until_stockout = 200 / 100 = 2 days (critical)
        assert result["risk_level"] == "critical"
        assert result["days_until_stockout"] == 2.0

    def test_high_risk(self):
        """Test high risk classification."""
        forecast = {"avg_forecasted_demand": 100.0}
        result = predict_stockout("SKU-001", "WH-001", 500, forecast)
        
        # days_until_stockout = 500 / 100 = 5 days (high)
        assert result["risk_level"] == "high"

    def test_medium_risk(self):
        """Test medium risk classification."""
        forecast = {"avg_forecasted_demand": 100.0}
        result = predict_stockout("SKU-001", "WH-001", 1000, forecast)
        
        # days_until_stockout = 1000 / 100 = 10 days (medium)
        assert result["risk_level"] == "medium"

    def test_low_risk(self):
        """Test low risk classification."""
        forecast = {"avg_forecasted_demand": 100.0}
        result = predict_stockout("SKU-001", "WH-001", 2000, forecast)
        
        # days_until_stockout = 2000 / 100 = 20 days (low)
        assert result["risk_level"] == "low"

    def test_low_risk_no_demand(self):
        """Test low risk when there's no demand."""
        forecast = {"avg_forecasted_demand": 0.0}
        result = predict_stockout("SKU-001", "WH-001", 100, forecast)
        
        # No demand: risk is low
        assert result["risk_level"] == "low"


class TestPredictStockoutIntegration:
    """Integration tests with realistic scenarios."""

    def test_scenario_urgent_restock(self):
        """Scenario: Urgent restock needed (critical risk)."""
        forecast = {
            "avg_forecasted_demand": 50.0,
            "trend": "increasing",
            "confidence": 0.8,
        }
        result = predict_stockout("SKU-WIDGET", "WH-MAIN", 100, forecast)
        
        assert result["risk_level"] == "critical"
        assert result["days_until_stockout"] == 2.0
        assert result["recommended_reorder_quantity"] == 600  # 50*14 - 100

    def test_scenario_normal_stock(self):
        """Scenario: Normal stock level (low risk)."""
        forecast = {
            "avg_forecasted_demand": 75.0,
            "trend": "stable",
            "confidence": 0.95,
        }
        result = predict_stockout("SKU-GADGET", "WH-EAST", 1500, forecast)
        
        assert result["risk_level"] == "low"
        assert result["days_until_stockout"] == 20.0
        assert result["recommended_reorder_quantity"] == 0  # Stock exceeds 14-day target

    def test_scenario_new_product_no_demand(self):
        """Scenario: New product with no historical demand."""
        forecast = {
            "avg_forecasted_demand": 0.0,
            "trend": "stable",
            "confidence": 0.3,
        }
        result = predict_stockout("SKU-NEW", "WH-WEST", 500, forecast)
        
        assert result["risk_level"] == "low"
        assert result["days_until_stockout"] is None
        assert result["recommended_reorder_quantity"] == 0

    def test_scenario_zero_stock(self):
        """Scenario: Already out of stock."""
        forecast = {
            "avg_forecasted_demand": 100.0,
            "trend": "stable",
            "confidence": 0.9,
        }
        result = predict_stockout("SKU-OUT", "WH-CENTRAL", 0, forecast)
        
        assert result["risk_level"] == "critical"
        assert result["days_until_stockout"] == 0.0
        assert result["recommended_reorder_quantity"] == 1400  # 100*14


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
