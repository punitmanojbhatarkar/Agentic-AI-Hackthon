"""
Unit tests for inventory allocation and fulfillment module.

Verifies:
1. Full fulfillment when stock sufficient
2. Partial fulfillment when stock limited
3. No fulfillment when stock exhausted
4. Priority ordering: premium tier first, then by order date
5. FIFO within each tier
6. Return dict structure
7. Type hints correctness
8. Input validation and error handling
"""

import pytest
from datetime import datetime
from allocation import recommend_allocation


class TestRecommendAllocationInputValidation:
    """Test input validation and error handling."""

    def test_invalid_available_stock_type_float(self):
        """Test that float available_stock raises TypeError."""
        with pytest.raises(TypeError):
            recommend_allocation("SKU-001", 50.5, [])

    def test_invalid_available_stock_type_string(self):
        """Test that string available_stock raises TypeError."""
        with pytest.raises(TypeError):
            recommend_allocation("SKU-001", "50", [])

    def test_negative_available_stock(self):
        """Test that negative available_stock raises ValueError."""
        with pytest.raises(ValueError):
            recommend_allocation("SKU-001", -10, [])

    def test_invalid_pending_orders_type_dict(self):
        """Test that dict pending_orders raises TypeError."""
        with pytest.raises(TypeError):
            recommend_allocation("SKU-001", 100, {"order_id": "ORD-001"})

    def test_pending_orders_contains_non_dict(self):
        """Test that non-dict items in list raise TypeError."""
        with pytest.raises(TypeError):
            recommend_allocation("SKU-001", 100, ["not-a-dict"])

    def test_missing_order_id_key(self):
        """Test that missing order_id raises KeyError."""
        order = {
            "customer_tier": "premium",
            "quantity_requested": 10,
            "order_date": "2024-01-10"
        }
        with pytest.raises(KeyError):
            recommend_allocation("SKU-001", 100, [order])

    def test_invalid_customer_tier(self):
        """Test that invalid customer_tier raises ValueError."""
        order = {
            "order_id": "ORD-001",
            "customer_tier": "vip",  # Invalid
            "quantity_requested": 10,
            "order_date": "2024-01-10"
        }
        with pytest.raises(ValueError):
            recommend_allocation("SKU-001", 100, [order])

    def test_negative_quantity_requested(self):
        """Test that negative quantity_requested raises ValueError."""
        order = {
            "order_id": "ORD-001",
            "customer_tier": "premium",
            "quantity_requested": -10,
            "order_date": "2024-01-10"
        }
        with pytest.raises(ValueError):
            recommend_allocation("SKU-001", 100, [order])

    def test_invalid_order_date_format(self):
        """Test that invalid order_date format raises ValueError."""
        order = {
            "order_id": "ORD-001",
            "customer_tier": "premium",
            "quantity_requested": 10,
            "order_date": "01-10-2024"  # Wrong format
        }
        with pytest.raises(ValueError):
            recommend_allocation("SKU-001", 100, [order])


class TestFullFulfillment:
    """Test full fulfillment scenarios."""

    def test_full_fulfillment_single_order(self):
        """Test full fulfillment with single order and sufficient stock."""
        orders = [{
            "order_id": "ORD-001",
            "customer_tier": "standard",
            "quantity_requested": 50,
            "order_date": "2024-01-10"
        }]
        result = recommend_allocation("SKU-001", 100, orders)
        
        assert result["fully_satisfied"] is True
        assert result["allocations"][0]["fulfillment_status"] == "full"
        assert result["allocations"][0]["quantity_allocated"] == 50

    def test_full_fulfillment_multiple_orders(self):
        """Test full fulfillment with multiple orders and sufficient stock."""
        orders = [
            {"order_id": "ORD-001", "customer_tier": "premium", "quantity_requested": 30, "order_date": "2024-01-10"},
            {"order_id": "ORD-002", "customer_tier": "standard", "quantity_requested": 40, "order_date": "2024-01-11"},
            {"order_id": "ORD-003", "customer_tier": "standard", "quantity_requested": 20, "order_date": "2024-01-12"},
        ]
        result = recommend_allocation("SKU-001", 100, orders)
        
        assert result["fully_satisfied"] is True
        assert all(alloc["fulfillment_status"] == "full" for alloc in result["allocations"])

    def test_full_fulfillment_exact_stock(self):
        """Test full fulfillment when stock exactly matches total requested."""
        orders = [
            {"order_id": "ORD-001", "customer_tier": "premium", "quantity_requested": 50, "order_date": "2024-01-10"},
            {"order_id": "ORD-002", "customer_tier": "standard", "quantity_requested": 50, "order_date": "2024-01-11"},
        ]
        result = recommend_allocation("SKU-001", 100, orders)
        
        assert result["fully_satisfied"] is True
        assert result["total_requested"] == 100


class TestPartialFulfillment:
    """Test partial fulfillment scenarios."""

    def test_partial_fulfillment_single_order(self):
        """Test partial fulfillment with single order and insufficient stock."""
        orders = [{
            "order_id": "ORD-001",
            "customer_tier": "standard",
            "quantity_requested": 100,
            "order_date": "2024-01-10"
        }]
        result = recommend_allocation("SKU-001", 50, orders)
        
        assert result["fully_satisfied"] is False
        assert result["allocations"][0]["fulfillment_status"] == "partial"
        assert result["allocations"][0]["quantity_allocated"] == 50

    def test_partial_fulfillment_mixed_orders(self):
        """Test partial fulfillment with multiple orders, some full, some partial."""
        orders = [
            {"order_id": "ORD-001", "customer_tier": "premium", "quantity_requested": 30, "order_date": "2024-01-10"},
            {"order_id": "ORD-002", "customer_tier": "premium", "quantity_requested": 40, "order_date": "2024-01-11"},
            {"order_id": "ORD-003", "customer_tier": "standard", "quantity_requested": 50, "order_date": "2024-01-12"},
        ]
        result = recommend_allocation("SKU-001", 60, orders)
        
        assert result["fully_satisfied"] is False
        # First two premium orders should get full allocation (30 + 40 = 70, but only 60 available)
        # So ORD-001 gets 30 (full), ORD-002 gets 30 (partial), ORD-003 gets 0 (none)
        assert result["allocations"][0]["fulfillment_status"] == "full"
        assert result["allocations"][1]["fulfillment_status"] == "partial"


class TestNoFulfillment:
    """Test no fulfillment scenarios."""

    def test_no_fulfillment_zero_stock(self):
        """Test no fulfillment when stock is zero."""
        orders = [
            {"order_id": "ORD-001", "customer_tier": "premium", "quantity_requested": 50, "order_date": "2024-01-10"},
            {"order_id": "ORD-002", "customer_tier": "standard", "quantity_requested": 50, "order_date": "2024-01-11"},
        ]
        result = recommend_allocation("SKU-001", 0, orders)
        
        assert result["fully_satisfied"] is False
        assert all(alloc["fulfillment_status"] == "none" for alloc in result["allocations"])
        assert all(alloc["quantity_allocated"] == 0 for alloc in result["allocations"])

    def test_no_fulfillment_empty_orders(self):
        """Test with empty pending orders."""
        result = recommend_allocation("SKU-001", 100, [])
        
        assert result["fully_satisfied"] is True
        assert result["allocations"] == []
        assert result["total_requested"] == 0


class TestPriorityOrdering:
    """Test priority ordering and allocation."""

    def test_premium_priority_before_standard(self):
        """Test that premium tier orders are prioritized over standard tier."""
        orders = [
            {"order_id": "ORD-STD-001", "customer_tier": "standard", "quantity_requested": 40, "order_date": "2024-01-10"},
            {"order_id": "ORD-PREM-001", "customer_tier": "premium", "quantity_requested": 40, "order_date": "2024-01-15"},
            {"order_id": "ORD-STD-002", "customer_tier": "standard", "quantity_requested": 30, "order_date": "2024-01-11"},
        ]
        result = recommend_allocation("SKU-001", 80, orders)
        
        # Premium should be allocated first, then standard in order date sequence
        # ORD-PREM-001 (premium, 2024-01-15): gets 40
        # ORD-STD-001 (standard, 2024-01-10): gets 40
        # ORD-STD-002 (standard, 2024-01-11): gets 0
        
        # Find allocations by order_id
        alloc_map = {alloc["order_id"]: alloc for alloc in result["allocations"]}
        assert alloc_map["ORD-PREM-001"]["fulfillment_status"] == "full"
        assert alloc_map["ORD-STD-001"]["fulfillment_status"] == "full"
        assert alloc_map["ORD-STD-002"]["fulfillment_status"] == "none"

    def test_fifo_within_premium_tier(self):
        """Test FIFO ordering within premium tier."""
        orders = [
            {"order_id": "ORD-PREM-001", "customer_tier": "premium", "quantity_requested": 50, "order_date": "2024-01-15"},
            {"order_id": "ORD-PREM-002", "customer_tier": "premium", "quantity_requested": 50, "order_date": "2024-01-10"},
        ]
        result = recommend_allocation("SKU-001", 75, orders)
        
        # ORD-PREM-002 (earlier date) should be allocated first
        # ORD-PREM-002: 50 (full)
        # ORD-PREM-001: 25 (partial)
        
        alloc_map = {alloc["order_id"]: alloc for alloc in result["allocations"]}
        assert alloc_map["ORD-PREM-002"]["fulfillment_status"] == "full"
        assert alloc_map["ORD-PREM-002"]["quantity_allocated"] == 50
        assert alloc_map["ORD-PREM-001"]["fulfillment_status"] == "partial"
        assert alloc_map["ORD-PREM-001"]["quantity_allocated"] == 25

    def test_fifo_within_standard_tier(self):
        """Test FIFO ordering within standard tier."""
        orders = [
            {"order_id": "ORD-STD-001", "customer_tier": "standard", "quantity_requested": 50, "order_date": "2024-01-15"},
            {"order_id": "ORD-STD-002", "customer_tier": "standard", "quantity_requested": 50, "order_date": "2024-01-10"},
        ]
        result = recommend_allocation("SKU-001", 75, orders)
        
        # ORD-STD-002 (earlier date) should be allocated first
        alloc_map = {alloc["order_id"]: alloc for alloc in result["allocations"]}
        assert alloc_map["ORD-STD-002"]["fulfillment_status"] == "full"
        assert alloc_map["ORD-STD-001"]["fulfillment_status"] == "partial"


class TestReturnStructure:
    """Test return dict structure and types."""

    def test_return_dict_has_all_keys(self):
        """Test that return dict has all required keys."""
        orders = [{
            "order_id": "ORD-001",
            "customer_tier": "premium",
            "quantity_requested": 50,
            "order_date": "2024-01-10"
        }]
        result = recommend_allocation("SKU-001", 100, orders)
        
        required_keys = {"sku_id", "available_stock", "total_requested", "allocations", "fully_satisfied"}
        assert set(result.keys()) == required_keys

    def test_allocation_items_have_required_fields(self):
        """Test that each allocation item has required fields."""
        orders = [{
            "order_id": "ORD-001",
            "customer_tier": "premium",
            "quantity_requested": 50,
            "order_date": "2024-01-10"
        }]
        result = recommend_allocation("SKU-001", 100, orders)
        
        required_alloc_keys = {
            "order_id",
            "customer_tier",
            "quantity_requested",
            "quantity_allocated",
            "fulfillment_status"
        }
        assert set(result["allocations"][0].keys()) == required_alloc_keys

    def test_return_dict_types(self):
        """Test that return values have correct types."""
        orders = [{
            "order_id": "ORD-001",
            "customer_tier": "premium",
            "quantity_requested": 50,
            "order_date": "2024-01-10"
        }]
        result = recommend_allocation("SKU-001", 100, orders)
        
        assert isinstance(result["sku_id"], str)
        assert isinstance(result["available_stock"], int)
        assert isinstance(result["total_requested"], int)
        assert isinstance(result["allocations"], list)
        assert isinstance(result["fully_satisfied"], bool)

    def test_sku_id_passthrough(self):
        """Test that SKU ID is correctly passed through."""
        sku_id = "SKU-CUSTOM-12345"
        orders = [{
            "order_id": "ORD-001",
            "customer_tier": "standard",
            "quantity_requested": 10,
            "order_date": "2024-01-10"
        }]
        result = recommend_allocation(sku_id, 50, orders)
        assert result["sku_id"] == sku_id


class TestIntegrationScenarios:
    """Integration tests with realistic scenarios."""

    def test_scenario_full_satisfaction(self):
        """Scenario: Abundant stock, all orders fully satisfied."""
        orders = [
            {"order_id": "ORD-PREM-001", "customer_tier": "premium", "quantity_requested": 100, "order_date": "2024-01-10"},
            {"order_id": "ORD-PREM-002", "customer_tier": "premium", "quantity_requested": 80, "order_date": "2024-01-11"},
            {"order_id": "ORD-STD-001", "customer_tier": "standard", "quantity_requested": 200, "order_date": "2024-01-12"},
        ]
        result = recommend_allocation("SKU-WIDGET", 500, orders)
        
        assert result["fully_satisfied"] is True
        assert result["total_requested"] == 380
        assert sum(alloc["quantity_allocated"] for alloc in result["allocations"]) == 380

    def test_scenario_limited_stock_prioritize_premium(self):
        """Scenario: Limited stock, premium gets priority."""
        orders = [
            {"order_id": "ORD-STD-001", "customer_tier": "standard", "quantity_requested": 100, "order_date": "2024-01-10"},
            {"order_id": "ORD-PREM-001", "customer_tier": "premium", "quantity_requested": 50, "order_date": "2024-01-15"},
            {"order_id": "ORD-STD-002", "customer_tier": "standard", "quantity_requested": 100, "order_date": "2024-01-11"},
        ]
        result = recommend_allocation("SKU-COMPONENT", 100, orders)
        
        assert result["fully_satisfied"] is False
        alloc_map = {alloc["order_id"]: alloc for alloc in result["allocations"]}
        # Premium should get priority
        assert alloc_map["ORD-PREM-001"]["quantity_allocated"] == 50
        # Standard orders fill remaining stock in FIFO order
        assert alloc_map["ORD-STD-001"]["quantity_allocated"] == 50
        assert alloc_map["ORD-STD-002"]["quantity_allocated"] == 0

    def test_scenario_critical_shortage(self):
        """Scenario: Critical shortage, allocate to premium only."""
        orders = [
            {"order_id": "ORD-PREM-001", "customer_tier": "premium", "quantity_requested": 30, "order_date": "2024-01-10"},
            {"order_id": "ORD-PREM-002", "customer_tier": "premium", "quantity_requested": 50, "order_date": "2024-01-11"},
            {"order_id": "ORD-STD-001", "customer_tier": "standard", "quantity_requested": 200, "order_date": "2024-01-12"},
        ]
        result = recommend_allocation("SKU-CRITICAL", 40, orders)
        
        assert result["fully_satisfied"] is False
        alloc_map = {alloc["order_id"]: alloc for alloc in result["allocations"]}
        # ORD-PREM-001 gets full (30)
        assert alloc_map["ORD-PREM-001"]["fulfillment_status"] == "full"
        # ORD-PREM-002 gets partial (10)
        assert alloc_map["ORD-PREM-002"]["fulfillment_status"] == "partial"
        assert alloc_map["ORD-PREM-002"]["quantity_allocated"] == 10
        # ORD-STD-001 gets none
        assert alloc_map["ORD-STD-001"]["fulfillment_status"] == "none"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
