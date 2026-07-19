"""
Unit tests for shipment delay impact detection module.

Verifies:
1. Delay detection (estimated_delivery > promised_date)
2. Delay days calculation
3. Downstream impact scoring (premium 2x, standard 1x, normalized /20)
4. Affected order collection
5. Severity classification (critical>=70, moderate>=30, minor)
6. Return dict structure
7. Type hints correctness
8. Input validation and error handling
"""

import pytest
from datetime import datetime, timedelta
from shipments import detect_delay_impact, _classify_severity


class TestClassifySeverity:
    """Test severity classification logic."""

    def test_critical_severity_at_70(self):
        """Test critical severity at exactly 70."""
        severity = _classify_severity(70.0)
        assert severity == "critical"

    def test_critical_severity_above_70(self):
        """Test critical severity above 70."""
        severity = _classify_severity(85.0)
        assert severity == "critical"

    def test_moderate_severity_at_30(self):
        """Test moderate severity at exactly 30."""
        severity = _classify_severity(30.0)
        assert severity == "moderate"

    def test_moderate_severity_between_30_70(self):
        """Test moderate severity between 30 and 70."""
        severity = _classify_severity(50.0)
        assert severity == "moderate"

    def test_minor_severity_below_30(self):
        """Test minor severity below 30."""
        severity = _classify_severity(15.0)
        assert severity == "minor"

    def test_minor_severity_at_0(self):
        """Test minor severity at 0."""
        severity = _classify_severity(0.0)
        assert severity == "minor"


class TestDetectDelayImpactInputValidation:
    """Test input validation and error handling."""

    def test_invalid_shipment_data_type_string(self):
        """Test that string shipment_data raises TypeError."""
        with pytest.raises(TypeError):
            detect_delay_impact("SHIP-001", "not-a-dict", [])

    def test_invalid_downstream_orders_type_dict(self):
        """Test that dict downstream_orders raises TypeError."""
        shipment = {
            "promised_date": "2024-01-10",
            "current_status": "in_transit",
            "estimated_delivery": "2024-01-10"
        }
        with pytest.raises(TypeError):
            detect_delay_impact("SHIP-001", shipment, {"order_id": "ORD-001"})

    def test_missing_promised_date_key(self):
        """Test that missing promised_date raises KeyError."""
        shipment = {
            "current_status": "in_transit",
            "estimated_delivery": "2024-01-10"
        }
        with pytest.raises(KeyError):
            detect_delay_impact("SHIP-001", shipment, [])

    def test_invalid_promised_date_format(self):
        """Test that invalid promised_date format raises ValueError."""
        shipment = {
            "promised_date": "01-10-2024",  # Wrong format
            "current_status": "in_transit",
            "estimated_delivery": "2024-01-10"
        }
        with pytest.raises(ValueError):
            detect_delay_impact("SHIP-001", shipment, [])

    def test_invalid_estimated_delivery_format(self):
        """Test that invalid estimated_delivery format raises ValueError."""
        shipment = {
            "promised_date": "2024-01-10",
            "current_status": "in_transit",
            "estimated_delivery": "01-10-2024"  # Wrong format
        }
        with pytest.raises(ValueError):
            detect_delay_impact("SHIP-001", shipment, [])

    def test_downstream_order_non_dict(self):
        """Test that non-dict order raises TypeError."""
        shipment = {
            "promised_date": "2024-01-10",
            "current_status": "in_transit",
            "estimated_delivery": "2024-01-10"
        }
        with pytest.raises(TypeError):
            detect_delay_impact("SHIP-001", shipment, ["not-a-dict"])

    def test_missing_order_id_key(self):
        """Test that missing order_id raises KeyError."""
        shipment = {
            "promised_date": "2024-01-10",
            "current_status": "in_transit",
            "estimated_delivery": "2024-01-10"
        }
        order = {"customer_tier": "premium", "sku_id": "SKU-001", "quantity": 10}
        with pytest.raises(KeyError):
            detect_delay_impact("SHIP-001", shipment, [order])

    def test_invalid_customer_tier(self):
        """Test that invalid customer_tier raises ValueError."""
        shipment = {
            "promised_date": "2024-01-10",
            "current_status": "in_transit",
            "estimated_delivery": "2024-01-10"
        }
        order = {
            "order_id": "ORD-001",
            "customer_tier": "gold",  # Invalid tier
            "sku_id": "SKU-001",
            "quantity": 10
        }
        with pytest.raises(ValueError):
            detect_delay_impact("SHIP-001", shipment, [order])


class TestDetectDelayCalculations:
    """Test core calculation logic."""

    def test_not_delayed_when_on_time(self):
        """Test that on-time delivery is not marked as delayed."""
        shipment = {
            "promised_date": "2024-01-10",
            "current_status": "in_transit",
            "estimated_delivery": "2024-01-10"
        }
        result = detect_delay_impact("SHIP-001", shipment, [])
        assert result["is_delayed"] is False
        assert result["delay_days"] == 0

    def test_not_delayed_when_early(self):
        """Test that early delivery is not marked as delayed."""
        shipment = {
            "promised_date": "2024-01-10",
            "current_status": "in_transit",
            "estimated_delivery": "2024-01-09"
        }
        result = detect_delay_impact("SHIP-001", shipment, [])
        assert result["is_delayed"] is False
        assert result["delay_days"] == 0

    def test_delayed_when_late(self):
        """Test that late delivery is marked as delayed."""
        shipment = {
            "promised_date": "2024-01-10",
            "current_status": "delayed",
            "estimated_delivery": "2024-01-12"
        }
        result = detect_delay_impact("SHIP-001", shipment, [])
        assert result["is_delayed"] is True
        assert result["delay_days"] == 2

    def test_delay_days_calculation(self):
        """Test delay days calculation with various delays."""
        test_cases = [
            ("2024-01-10", "2024-01-15", 5),  # 5 days late
            ("2024-01-10", "2024-01-11", 1),  # 1 day late
            ("2024-01-10", "2024-01-10", 0),  # On time
        ]
        for promised, estimated, expected_delay in test_cases:
            shipment = {
                "promised_date": promised,
                "current_status": "delayed" if estimated > promised else "in_transit",
                "estimated_delivery": estimated
            }
            result = detect_delay_impact("SHIP-001", shipment, [])
            assert result["delay_days"] == expected_delay

    def test_not_delayed_when_estimated_delivery_none(self):
        """Test that None estimated_delivery is not marked as delayed."""
        shipment = {
            "promised_date": "2024-01-10",
            "current_status": "in_transit",
            "estimated_delivery": None
        }
        result = detect_delay_impact("SHIP-001", shipment, [])
        assert result["is_delayed"] is False
        assert result["delay_days"] == 0

    def test_impact_score_standard_only(self):
        """Test impact score with standard tier orders only."""
        shipment = {
            "promised_date": "2024-01-10",
            "current_status": "delayed",
            "estimated_delivery": "2024-01-12"
        }
        # 5 standard orders = 5 * 1x weight = 5 weighted
        # score = (5 / 20) * 100 = 25
        orders = [
            {
                "order_id": f"ORD-{i:03d}",
                "customer_tier": "standard",
                "sku_id": "SKU-001",
                "quantity": 10
            }
            for i in range(5)
        ]
        result = detect_delay_impact("SHIP-001", shipment, orders)
        assert result["downstream_impact_score"] == 25.0

    def test_impact_score_premium_only(self):
        """Test impact score with premium tier orders only."""
        shipment = {
            "promised_date": "2024-01-10",
            "current_status": "delayed",
            "estimated_delivery": "2024-01-12"
        }
        # 5 premium orders = 5 * 2x weight = 10 weighted
        # score = (10 / 20) * 100 = 50
        orders = [
            {
                "order_id": f"ORD-{i:03d}",
                "customer_tier": "premium",
                "sku_id": "SKU-001",
                "quantity": 10
            }
            for i in range(5)
        ]
        result = detect_delay_impact("SHIP-001", shipment, orders)
        assert result["downstream_impact_score"] == 50.0

    def test_impact_score_mixed(self):
        """Test impact score with mixed premium and standard orders."""
        shipment = {
            "promised_date": "2024-01-10",
            "current_status": "delayed",
            "estimated_delivery": "2024-01-12"
        }
        # 3 premium (3*2 = 6) + 4 standard (4*1 = 4) = 10 weighted
        # score = (10 / 20) * 100 = 50
        orders = [
            {"order_id": "ORD-001", "customer_tier": "premium", "sku_id": "SKU-001", "quantity": 10},
            {"order_id": "ORD-002", "customer_tier": "premium", "sku_id": "SKU-002", "quantity": 5},
            {"order_id": "ORD-003", "customer_tier": "premium", "sku_id": "SKU-003", "quantity": 8},
            {"order_id": "ORD-004", "customer_tier": "standard", "sku_id": "SKU-004", "quantity": 12},
            {"order_id": "ORD-005", "customer_tier": "standard", "sku_id": "SKU-005", "quantity": 20},
            {"order_id": "ORD-006", "customer_tier": "standard", "sku_id": "SKU-006", "quantity": 15},
            {"order_id": "ORD-007", "customer_tier": "standard", "sku_id": "SKU-007", "quantity": 10},
        ]
        result = detect_delay_impact("SHIP-001", shipment, orders)
        assert result["downstream_impact_score"] == 50.0

    def test_impact_score_exceeds_max_clipped(self):
        """Test that impact score is clipped to 100 max."""
        shipment = {
            "promised_date": "2024-01-10",
            "current_status": "delayed",
            "estimated_delivery": "2024-01-12"
        }
        # 15 premium orders = 15 * 2x = 30 weighted
        # Formula would give (30 / 20) * 100 = 150, but clipped to 100
        orders = [
            {
                "order_id": f"ORD-{i:03d}",
                "customer_tier": "premium",
                "sku_id": "SKU-001",
                "quantity": 10
            }
            for i in range(15)
        ]
        result = detect_delay_impact("SHIP-001", shipment, orders)
        assert result["downstream_impact_score"] == 100.0

    def test_affected_order_ids_collected(self):
        """Test that affected order IDs are correctly collected."""
        shipment = {
            "promised_date": "2024-01-10",
            "current_status": "delayed",
            "estimated_delivery": "2024-01-12"
        }
        orders = [
            {"order_id": "ORD-001", "customer_tier": "premium", "sku_id": "SKU-001", "quantity": 10},
            {"order_id": "ORD-002", "customer_tier": "standard", "sku_id": "SKU-002", "quantity": 5},
            {"order_id": "ORD-003", "customer_tier": "premium", "sku_id": "SKU-003", "quantity": 8},
        ]
        result = detect_delay_impact("SHIP-001", shipment, orders)
        assert set(result["affected_order_ids"]) == {"ORD-001", "ORD-002", "ORD-003"}


class TestDetectDelayImpactReturnStructure:
    """Test return dict structure and types."""

    def test_return_dict_has_all_keys(self):
        """Test that return dict has all required keys."""
        shipment = {
            "promised_date": "2024-01-10",
            "current_status": "in_transit",
            "estimated_delivery": "2024-01-10"
        }
        result = detect_delay_impact("SHIP-001", shipment, [])
        
        required_keys = {
            "shipment_id",
            "is_delayed",
            "delay_days",
            "downstream_impact_score",
            "affected_order_ids",
            "severity"
        }
        assert set(result.keys()) == required_keys

    def test_return_dict_types(self):
        """Test that return values have correct types."""
        shipment = {
            "promised_date": "2024-01-10",
            "current_status": "in_transit",
            "estimated_delivery": "2024-01-10"
        }
        result = detect_delay_impact("SHIP-001", shipment, [])
        
        assert isinstance(result["shipment_id"], str)
        assert isinstance(result["is_delayed"], bool)
        assert isinstance(result["delay_days"], int)
        assert isinstance(result["downstream_impact_score"], float)
        assert isinstance(result["affected_order_ids"], list)
        assert isinstance(result["severity"], str)

    def test_shipment_id_passthrough(self):
        """Test that shipment ID is correctly passed through."""
        shipment_id = "SHIP-CUSTOM-12345"
        shipment = {
            "promised_date": "2024-01-10",
            "current_status": "in_transit",
            "estimated_delivery": "2024-01-10"
        }
        result = detect_delay_impact(shipment_id, shipment, [])
        assert result["shipment_id"] == shipment_id


class TestDetectDelayImpactSeverity:
    """Test severity assignment."""

    def test_critical_severity(self):
        """Test critical severity for high impact."""
        shipment = {
            "promised_date": "2024-01-10",
            "current_status": "delayed",
            "estimated_delivery": "2024-01-15"
        }
        # 10 premium orders = 20 weighted = 100 score = critical
        orders = [
            {
                "order_id": f"ORD-{i:03d}",
                "customer_tier": "premium",
                "sku_id": "SKU-001",
                "quantity": 10
            }
            for i in range(10)
        ]
        result = detect_delay_impact("SHIP-001", shipment, orders)
        assert result["severity"] == "critical"

    def test_moderate_severity(self):
        """Test moderate severity for medium impact."""
        shipment = {
            "promised_date": "2024-01-10",
            "current_status": "delayed",
            "estimated_delivery": "2024-01-12"
        }
        # 7 standard orders = 7 weighted = 35 score = moderate
        orders = [
            {
                "order_id": f"ORD-{i:03d}",
                "customer_tier": "standard",
                "sku_id": "SKU-001",
                "quantity": 10
            }
            for i in range(7)
        ]
        result = detect_delay_impact("SHIP-001", shipment, orders)
        assert result["severity"] == "moderate"

    def test_minor_severity(self):
        """Test minor severity for low impact."""
        shipment = {
            "promised_date": "2024-01-10",
            "current_status": "delayed",
            "estimated_delivery": "2024-01-11"
        }
        # 1 standard order = 1 weighted = 5 score = minor
        orders = [
            {"order_id": "ORD-001", "customer_tier": "standard", "sku_id": "SKU-001", "quantity": 10}
        ]
        result = detect_delay_impact("SHIP-001", shipment, orders)
        assert result["severity"] == "minor"


class TestDetectDelayImpactIntegration:
    """Integration tests with realistic scenarios."""

    def test_scenario_critical_delay_multiple_premium(self):
        """Scenario: 5-day delay affecting multiple premium customers."""
        shipment = {
            "promised_date": "2024-01-10",
            "current_status": "delayed",
            "estimated_delivery": "2024-01-15"
        }
        orders = [
            {"order_id": f"ORD-PREMIUM-{i:03d}", "customer_tier": "premium", "sku_id": "SKU-WIDGET", "quantity": 500}
            for i in range(10)  # 10 premium = 20 weighted = 100 score = critical
        ]
        result = detect_delay_impact("SHIP-CRITICAL", shipment, orders)
        
        assert result["is_delayed"] is True
        assert result["delay_days"] == 5
        assert result["severity"] == "critical"
        assert len(result["affected_order_ids"]) == 10

    def test_scenario_minor_delay_single_standard(self):
        """Scenario: 1-day delay affecting single standard customer."""
        shipment = {
            "promised_date": "2024-01-10",
            "current_status": "delayed",
            "estimated_delivery": "2024-01-11"
        }
        orders = [
            {"order_id": "ORD-STANDARD-001", "customer_tier": "standard", "sku_id": "SKU-COMPONENT", "quantity": 100}
        ]
        result = detect_delay_impact("SHIP-MINOR", shipment, orders)
        
        assert result["is_delayed"] is True
        assert result["delay_days"] == 1
        assert result["severity"] == "minor"
        assert result["affected_order_ids"] == ["ORD-STANDARD-001"]

    def test_scenario_no_delay(self):
        """Scenario: On-time delivery, no impact."""
        shipment = {
            "promised_date": "2024-01-10",
            "current_status": "in_transit",
            "estimated_delivery": "2024-01-10"
        }
        orders = [
            {"order_id": "ORD-001", "customer_tier": "premium", "sku_id": "SKU-001", "quantity": 100}
        ]
        result = detect_delay_impact("SHIP-ONTIME", shipment, orders)
        
        assert result["is_delayed"] is False
        assert result["delay_days"] == 0
        # No delay, so impact should be based on orders only
        assert result["severity"] == "minor"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
