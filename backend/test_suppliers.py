"""
Unit tests for supplier risk assessment module.

Verifies:
1. On-time delivery percentage calculation (exclude None actual_date)
2. Lead time variance normalization (0 days=100, 15+=0, linear interpolation)
3. Average quality score (mean of 1-10 ratings * 10)
4. Weighted composite score (0.4 on-time + 0.3 variance + 0.3 quality)
5. Risk category classification (low>=70, medium>=40, high<40)
6. Return dict structure matches specification
7. Type hints correctness
8. Empty delivery history handling (score=None, risk_category="unknown")
9. Edge cases (no delivered orders, all delivered, perfect vs poor performance)
"""

import pytest
from datetime import datetime, timedelta
from suppliers import supplier_risk_score, _normalize_variance_to_score, _classify_risk_category


class TestNormalizeVarianceToScore:
    """Test lead time variance normalization."""

    def test_zero_variance_is_perfect(self):
        """Test that zero variance yields perfect score of 100."""
        score = _normalize_variance_to_score(0.0)
        assert score == 100.0

    def test_negative_variance_is_perfect(self):
        """Test that negative variance (edge case) yields 100."""
        score = _normalize_variance_to_score(-5.0)
        assert score == 100.0

    def test_15_days_variance_is_zero(self):
        """Test that 15 days variance yields score of 0."""
        score = _normalize_variance_to_score(15.0)
        assert score == 0.0

    def test_over_15_days_variance_is_zero(self):
        """Test that over 15 days variance still yields 0."""
        score = _normalize_variance_to_score(30.0)
        assert score == 0.0

    def test_7_5_days_variance_is_50(self):
        """Test linear interpolation: 7.5 days should yield 50."""
        # formula: 100 * (1 - 7.5 / 15) = 100 * 0.5 = 50
        score = _normalize_variance_to_score(7.5)
        assert abs(score - 50.0) < 0.1

    def test_5_days_variance_is_66_7(self):
        """Test linear interpolation: 5 days should yield ~66.7."""
        # formula: 100 * (1 - 5 / 15) = 100 * (2/3) ≈ 66.67
        score = _normalize_variance_to_score(5.0)
        assert abs(score - 66.67) < 0.1

    def test_score_clipped_to_range(self):
        """Test that score is always in [0, 100]."""
        test_cases = [0.0, 5.0, 10.0, 15.0, 30.0]
        for variance in test_cases:
            score = _normalize_variance_to_score(variance)
            assert 0.0 <= score <= 100.0


class TestClassifyRiskCategory:
    """Test risk category classification."""

    def test_low_risk_at_70(self):
        """Test low risk at exactly 70."""
        risk = _classify_risk_category(70.0)
        assert risk == "low"

    def test_low_risk_above_70(self):
        """Test low risk above 70."""
        risk = _classify_risk_category(85.0)
        assert risk == "low"

    def test_medium_risk_at_40(self):
        """Test medium risk at exactly 40."""
        risk = _classify_risk_category(40.0)
        assert risk == "medium"

    def test_medium_risk_between_40_70(self):
        """Test medium risk between 40 and 70."""
        risk = _classify_risk_category(55.0)
        assert risk == "medium"

    def test_high_risk_below_40(self):
        """Test high risk below 40."""
        risk = _classify_risk_category(25.0)
        assert risk == "high"

    def test_high_risk_at_0(self):
        """Test high risk at 0."""
        risk = _classify_risk_category(0.0)
        assert risk == "high"

    def test_unknown_risk_for_none(self):
        """Test unknown risk when score is None."""
        risk = _classify_risk_category(None)
        assert risk == "unknown"


class TestSupplierRiskScoreInputValidation:
    """Test input validation and error handling."""

    def test_invalid_delivery_history_type_string(self):
        """Test that string delivery_history raises TypeError."""
        with pytest.raises(TypeError):
            supplier_risk_score("SUP-001", "not-a-list")

    def test_invalid_delivery_history_type_dict(self):
        """Test that dict delivery_history raises TypeError."""
        with pytest.raises(TypeError):
            supplier_risk_score("SUP-001", {"order_id": "ORD-001"})

    def test_delivery_history_contains_non_dict(self):
        """Test that non-dict items in list raise TypeError."""
        with pytest.raises(TypeError):
            supplier_risk_score("SUP-001", [{"order_id": "ORD-001", "promised_date": "2024-01-01",
                                               "actual_date": "2024-01-01", "quality_rating": 8},
                                              "not-a-dict"])

    def test_missing_order_id_key(self):
        """Test that missing order_id raises KeyError."""
        delivery = [{
            "promised_date": "2024-01-01",
            "actual_date": "2024-01-01",
            "quality_rating": 8
        }]
        with pytest.raises(KeyError):
            supplier_risk_score("SUP-001", delivery)

    def test_missing_promised_date_key(self):
        """Test that missing promised_date raises KeyError."""
        delivery = [{
            "order_id": "ORD-001",
            "actual_date": "2024-01-01",
            "quality_rating": 8
        }]
        with pytest.raises(KeyError):
            supplier_risk_score("SUP-001", delivery)

    def test_invalid_quality_rating_too_low(self):
        """Test that quality_rating < 1 raises ValueError."""
        delivery = [{
            "order_id": "ORD-001",
            "promised_date": "2024-01-01",
            "actual_date": "2024-01-01",
            "quality_rating": 0
        }]
        with pytest.raises(ValueError):
            supplier_risk_score("SUP-001", delivery)

    def test_invalid_quality_rating_too_high(self):
        """Test that quality_rating > 10 raises ValueError."""
        delivery = [{
            "order_id": "ORD-001",
            "promised_date": "2024-01-01",
            "actual_date": "2024-01-01",
            "quality_rating": 11
        }]
        with pytest.raises(ValueError):
            supplier_risk_score("SUP-001", delivery)

    def test_invalid_quality_rating_type(self):
        """Test that non-int quality_rating raises ValueError."""
        delivery = [{
            "order_id": "ORD-001",
            "promised_date": "2024-01-01",
            "actual_date": "2024-01-01",
            "quality_rating": "8"
        }]
        with pytest.raises(ValueError):
            supplier_risk_score("SUP-001", delivery)

    def test_invalid_promised_date_format(self):
        """Test that invalid promised_date format raises ValueError."""
        delivery = [{
            "order_id": "ORD-001",
            "promised_date": "01-01-2024",  # Wrong format
            "actual_date": "2024-01-01",
            "quality_rating": 8
        }]
        with pytest.raises(ValueError):
            supplier_risk_score("SUP-001", delivery)

    def test_invalid_actual_date_format(self):
        """Test that invalid actual_date format raises ValueError."""
        delivery = [{
            "order_id": "ORD-001",
            "promised_date": "2024-01-01",
            "actual_date": "01-01-2024",  # Wrong format
            "quality_rating": 8
        }]
        with pytest.raises(ValueError):
            supplier_risk_score("SUP-001", delivery)


class TestSupplierRiskScoreCalculations:
    """Test core calculation logic."""

    def test_on_time_delivery_perfect(self):
        """Test on-time delivery calculation when all delivered on time."""
        delivery = [
            {
                "order_id": f"ORD-{i:03d}",
                "promised_date": "2024-01-10",
                "actual_date": "2024-01-08",  # Early
                "quality_rating": 8
            }
            for i in range(5)
        ]
        result = supplier_risk_score("SUP-001", delivery)
        assert result["breakdown"]["on_time_delivery_pct"] == 100.0

    def test_on_time_delivery_partial(self):
        """Test on-time delivery with mixed on-time and late."""
        delivery = [
            {
                "order_id": "ORD-001",
                "promised_date": "2024-01-10",
                "actual_date": "2024-01-08",  # On time
                "quality_rating": 8
            },
            {
                "order_id": "ORD-002",
                "promised_date": "2024-01-10",
                "actual_date": "2024-01-12",  # Late
                "quality_rating": 8
            },
        ]
        result = supplier_risk_score("SUP-001", delivery)
        assert result["breakdown"]["on_time_delivery_pct"] == 50.0

    def test_on_time_delivery_excludes_undelivered(self):
        """Test that undelivered orders (actual_date=None) are excluded."""
        delivery = [
            {
                "order_id": "ORD-001",
                "promised_date": "2024-01-10",
                "actual_date": "2024-01-08",  # Delivered on time
                "quality_rating": 8
            },
            {
                "order_id": "ORD-002",
                "promised_date": "2024-01-10",
                "actual_date": None,  # Not delivered yet
                "quality_rating": 7
            },
        ]
        result = supplier_risk_score("SUP-001", delivery)
        # Only 1 delivered order, which was on time
        assert result["breakdown"]["on_time_delivery_pct"] == 100.0

    def test_lead_time_variance_zero(self):
        """Test lead time variance when all delivered exactly on promised date."""
        delivery = [
            {
                "order_id": f"ORD-{i:03d}",
                "promised_date": "2024-01-10",
                "actual_date": "2024-01-10",  # Exactly on time
                "quality_rating": 8
            }
            for i in range(5)
        ]
        result = supplier_risk_score("SUP-001", delivery)
        assert result["breakdown"]["lead_time_variance_days"] == 0.0

    def test_lead_time_variance_mixed(self):
        """Test lead time variance with mixed early/late deliveries."""
        # Promised: 2024-01-10 for all
        delivery = [
            {
                "order_id": "ORD-001",
                "promised_date": "2024-01-10",
                "actual_date": "2024-01-08",  # 2 days early
                "quality_rating": 8
            },
            {
                "order_id": "ORD-002",
                "promised_date": "2024-01-10",
                "actual_date": "2024-01-10",  # 0 days
                "quality_rating": 8
            },
            {
                "order_id": "ORD-003",
                "promised_date": "2024-01-10",
                "actual_date": "2024-01-12",  # 2 days late
                "quality_rating": 8
            },
        ]
        result = supplier_risk_score("SUP-001", delivery)
        # Lead times: [-2, 0, 2], mean=0, std ≈ 1.63
        variance = result["breakdown"]["lead_time_variance_days"]
        assert abs(variance - 1.63) < 0.1

    def test_average_quality_score(self):
        """Test quality score calculation."""
        delivery = [
            {
                "order_id": "ORD-001",
                "promised_date": "2024-01-10",
                "actual_date": "2024-01-10",
                "quality_rating": 8
            },
            {
                "order_id": "ORD-002",
                "promised_date": "2024-01-10",
                "actual_date": "2024-01-10",
                "quality_rating": 6
            },
        ]
        result = supplier_risk_score("SUP-001", delivery)
        # Mean rating = 7, score = 7 * 10 = 70
        assert result["breakdown"]["avg_quality_score"] == 70.0

    def test_composite_score_calculation(self):
        """Test weighted composite score."""
        delivery = [
            {
                "order_id": "ORD-001",
                "promised_date": "2024-01-10",
                "actual_date": "2024-01-10",  # 100% on-time
                "quality_rating": 10  # 100 quality score
            },
        ]
        result = supplier_risk_score("SUP-001", delivery)
        # on_time=100, variance_score=100, quality=100
        # composite = 100*0.4 + 100*0.3 + 100*0.3 = 100
        assert result["score"] == 100.0


class TestSupplierRiskScoreReturnStructure:
    """Test return dict structure and types."""

    def test_return_dict_has_all_keys(self):
        """Test that return dict has all required keys."""
        delivery = [{
            "order_id": "ORD-001",
            "promised_date": "2024-01-10",
            "actual_date": "2024-01-10",
            "quality_rating": 8
        }]
        result = supplier_risk_score("SUP-001", delivery)
        
        required_keys = {"supplier_id", "score", "breakdown", "risk_category"}
        assert set(result.keys()) == required_keys

    def test_breakdown_has_all_components(self):
        """Test that breakdown dict has all components."""
        delivery = [{
            "order_id": "ORD-001",
            "promised_date": "2024-01-10",
            "actual_date": "2024-01-10",
            "quality_rating": 8
        }]
        result = supplier_risk_score("SUP-001", delivery)
        
        breakdown_keys = {
            "on_time_delivery_pct",
            "lead_time_variance_days",
            "avg_quality_score"
        }
        assert set(result["breakdown"].keys()) == breakdown_keys

    def test_return_dict_types(self):
        """Test that return values have correct types."""
        delivery = [{
            "order_id": "ORD-001",
            "promised_date": "2024-01-10",
            "actual_date": "2024-01-10",
            "quality_rating": 8
        }]
        result = supplier_risk_score("SUP-001", delivery)
        
        assert isinstance(result["supplier_id"], str)
        assert isinstance(result["score"], (float, type(None)))
        assert isinstance(result["breakdown"], dict)
        assert isinstance(result["risk_category"], str)

    def test_supplier_id_passthrough(self):
        """Test that supplier ID is correctly passed through."""
        supplier_id = "SUP-CUSTOM-12345"
        delivery = [{
            "order_id": "ORD-001",
            "promised_date": "2024-01-10",
            "actual_date": "2024-01-10",
            "quality_rating": 8
        }]
        result = supplier_risk_score(supplier_id, delivery)
        assert result["supplier_id"] == supplier_id


class TestSupplierRiskScoreRiskCategory:
    """Test risk category assignment."""

    def test_low_risk_high_score(self):
        """Test low risk for high-scoring supplier."""
        delivery = [
            {
                "order_id": f"ORD-{i:03d}",
                "promised_date": "2024-01-10",
                "actual_date": "2024-01-10",  # On time
                "quality_rating": 9
            }
            for i in range(10)
        ]
        result = supplier_risk_score("SUP-001", delivery)
        assert result["risk_category"] == "low"
        assert result["score"] >= 70

    def test_medium_risk_medium_score(self):
        """Test medium risk for medium-scoring supplier."""
        delivery = [
            {
                "order_id": "ORD-001",
                "promised_date": "2024-01-10",
                "actual_date": "2024-01-11",  # 1 day late
                "quality_rating": 7
            },
        ]
        result = supplier_risk_score("SUP-001", delivery)
        assert result["risk_category"] == "medium"
        assert 40 <= result["score"] < 70

    def test_high_risk_low_score(self):
        """Test high risk for low-scoring supplier."""
        delivery = [
            {
                "order_id": "ORD-001",
                "promised_date": "2024-01-10",
                "actual_date": "2024-01-25",  # 15 days late
                "quality_rating": 2
            },
        ]
        result = supplier_risk_score("SUP-001", delivery)
        assert result["risk_category"] == "high"
        assert result["score"] < 40

    def test_unknown_risk_empty_history(self):
        """Test unknown risk for empty delivery history."""
        result = supplier_risk_score("SUP-001", [])
        assert result["risk_category"] == "unknown"
        assert result["score"] is None


class TestSupplierRiskScoreEdgeCases:
    """Test edge cases and special scenarios."""

    def test_empty_delivery_history(self):
        """Test handling of empty delivery history."""
        result = supplier_risk_score("SUP-001", [])
        assert result["score"] is None
        assert result["risk_category"] == "unknown"
        assert result["breakdown"]["on_time_delivery_pct"] is None
        assert result["breakdown"]["lead_time_variance_days"] is None

    def test_all_orders_undelivered(self):
        """Test when no orders have been delivered yet."""
        delivery = [
            {
                "order_id": f"ORD-{i:03d}",
                "promised_date": "2024-01-10",
                "actual_date": None,  # Not delivered
                "quality_rating": 8
            }
            for i in range(5)
        ]
        result = supplier_risk_score("SUP-001", delivery)
        assert result["score"] is None
        assert result["risk_category"] == "unknown"
        assert result["breakdown"]["on_time_delivery_pct"] is None

    def test_single_delivered_order(self):
        """Test with single delivered order."""
        delivery = [{
            "order_id": "ORD-001",
            "promised_date": "2024-01-10",
            "actual_date": "2024-01-10",
            "quality_rating": 8
        }]
        result = supplier_risk_score("SUP-001", delivery)
        assert result["score"] is not None
        assert result["risk_category"] in ["low", "medium", "high"]

    def test_perfect_supplier(self):
        """Test perfect supplier (all on time, high quality, zero variance)."""
        delivery = [
            {
                "order_id": f"ORD-{i:03d}",
                "promised_date": "2024-01-10",
                "actual_date": "2024-01-10",  # Exactly on time
                "quality_rating": 10
            }
            for i in range(5)
        ]
        result = supplier_risk_score("SUP-001", delivery)
        assert result["score"] == 100.0
        assert result["risk_category"] == "low"

    def test_poor_supplier(self):
        """Test poor supplier (always late, low quality)."""
        delivery = [
            {
                "order_id": f"ORD-{i:03d}",
                "promised_date": "2024-01-10",
                "actual_date": "2024-01-30",  # 20 days late
                "quality_rating": 2
            }
            for i in range(5)
        ]
        result = supplier_risk_score("SUP-001", delivery)
        assert result["score"] < 40
        assert result["risk_category"] == "high"

    def test_realistic_supplier_scenario(self):
        """Test realistic supplier with mixed performance."""
        delivery = [
            {"order_id": "ORD-001", "promised_date": "2024-01-10", "actual_date": "2024-01-10", "quality_rating": 9},
            {"order_id": "ORD-002", "promised_date": "2024-01-15", "actual_date": "2024-01-16", "quality_rating": 7},
            {"order_id": "ORD-003", "promised_date": "2024-01-20", "actual_date": "2024-01-19", "quality_rating": 8},
            {"order_id": "ORD-004", "promised_date": "2024-01-25", "actual_date": "2024-01-25", "quality_rating": 8},
            {"order_id": "ORD-005", "promised_date": "2024-02-01", "actual_date": None, "quality_rating": 5},  # Undelivered, quality placeholder
        ]
        result = supplier_risk_score("SUP-RELIABLE-100", delivery)
        
        # Verify result has all required fields
        assert result["supplier_id"] == "SUP-RELIABLE-100"
        assert result["score"] is not None
        assert result["risk_category"] in ["low", "medium", "high"]
        assert result["breakdown"]["on_time_delivery_pct"] == 75.0  # 3 out of 4 delivered on time


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
