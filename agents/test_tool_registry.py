"""
Tests for the tool registry.

Verifies:
1. All tools are properly defined
2. Tool retrieval by name works
3. Tool formatting produces valid output
4. Registry metadata functions work correctly
5. Descriptions are precise and non-vague
6. Parameters are properly structured
"""

import pytest
from tool_registry import (
    TOOLS,
    get_tool_by_name,
    format_tools_for_prompt,
    get_tool_names,
    get_tool_count,
    validate_tool_exists,
    get_system_prompt,
)


class TestToolRegistry:
    """Test basic tool registry functionality."""

    def test_tools_list_exists(self):
        """Test that TOOLS list is defined."""
        assert TOOLS is not None
        assert isinstance(TOOLS, list)
        assert len(TOOLS) > 0

    def test_all_tools_have_required_fields(self):
        """Test that each tool has name, description, and parameters."""
        required_fields = {"name", "description", "parameters"}
        for tool in TOOLS:
            assert set(tool.keys()) >= required_fields, f"Tool {tool.get('name', 'unknown')} missing fields"

    def test_tool_names_are_unique(self):
        """Test that all tool names are unique."""
        names = [tool["name"] for tool in TOOLS]
        assert len(names) == len(set(names)), "Duplicate tool names found"

    def test_tool_descriptions_are_not_empty(self):
        """Test that all tool descriptions are non-empty and meaningful."""
        for tool in TOOLS:
            description = tool["description"]
            assert isinstance(description, str), f"Description not a string for {tool['name']}"
            assert len(description) > 20, f"Description too short for {tool['name']}"
            # Descriptions should be full sentences, not vague
            assert description.endswith(";") or description.endswith("."), \
                f"Description for {tool['name']} should end with period or semicolon"

    def test_all_parameters_have_type_and_description(self):
        """Test that all parameters have type and description fields."""
        for tool in TOOLS:
            parameters = tool["parameters"]
            assert isinstance(parameters, dict), f"Parameters not a dict for {tool['name']}"
            for param_name, param_info in parameters.items():
                assert "type" in param_info, f"Missing 'type' for {tool['name']}.{param_name}"
                assert "description" in param_info, f"Missing 'description' for {tool['name']}.{param_name}"
                assert isinstance(param_info["type"], str), \
                    f"Type not a string for {tool['name']}.{param_name}"
                assert isinstance(param_info["description"], str), \
                    f"Description not a string for {tool['name']}.{param_name}"
                assert len(param_info["description"]) > 10, \
                    f"Parameter description too short for {tool['name']}.{param_name}"


class TestToolRetrieval:
    """Test tool retrieval functionality."""

    def test_get_tool_by_name_forecast_demand(self):
        """Test retrieving forecast_demand tool."""
        tool = get_tool_by_name("forecast_demand")
        assert tool is not None
        assert tool["name"] == "forecast_demand"
        assert "description" in tool
        assert "parameters" in tool

    def test_get_tool_by_name_predict_stockout(self):
        """Test retrieving predict_stockout tool."""
        tool = get_tool_by_name("predict_stockout")
        assert tool is not None
        assert tool["name"] == "predict_stockout"

    def test_get_tool_by_name_supplier_risk_score(self):
        """Test retrieving supplier_risk_score tool."""
        tool = get_tool_by_name("supplier_risk_score")
        assert tool is not None
        assert tool["name"] == "supplier_risk_score"

    def test_get_tool_by_name_detect_delay_impact(self):
        """Test retrieving detect_delay_impact tool."""
        tool = get_tool_by_name("detect_delay_impact")
        assert tool is not None
        assert tool["name"] == "detect_delay_impact"

    def test_get_tool_by_name_recommend_allocation(self):
        """Test retrieving recommend_allocation tool."""
        tool = get_tool_by_name("recommend_allocation")
        assert tool is not None
        assert tool["name"] == "recommend_allocation"

    def test_get_tool_by_name_nonexistent(self):
        """Test retrieving non-existent tool returns None."""
        tool = get_tool_by_name("nonexistent_tool")
        assert tool is None

    def test_get_tool_by_name_case_sensitive(self):
        """Test that tool name retrieval is case-sensitive."""
        tool = get_tool_by_name("Forecast_Demand")  # Wrong case
        assert tool is None


class TestToolMetadata:
    """Test tool metadata functions."""

    def test_get_tool_names(self):
        """Test getting list of all tool names."""
        names = get_tool_names()
        assert isinstance(names, list)
        assert len(names) == 5
        assert "forecast_demand" in names
        assert "predict_stockout" in names
        assert "supplier_risk_score" in names
        assert "detect_delay_impact" in names
        assert "recommend_allocation" in names

    def test_get_tool_count(self):
        """Test getting count of tools."""
        count = get_tool_count()
        assert count == 5

    def test_validate_tool_exists_true(self):
        """Test validating existing tool."""
        assert validate_tool_exists("forecast_demand") is True
        assert validate_tool_exists("predict_stockout") is True

    def test_validate_tool_exists_false(self):
        """Test validating non-existent tool."""
        assert validate_tool_exists("nonexistent") is False


class TestToolFormatting:
    """Test tool formatting for LLM prompts."""

    def test_format_tools_for_prompt_returns_string(self):
        """Test that format_tools_for_prompt returns a string."""
        formatted = format_tools_for_prompt()
        assert isinstance(formatted, str)
        assert len(formatted) > 0

    def test_format_tools_for_prompt_includes_all_tools(self):
        """Test that formatted output includes all tool names."""
        formatted = format_tools_for_prompt()
        assert "forecast_demand" in formatted
        assert "predict_stockout" in formatted
        assert "supplier_risk_score" in formatted
        assert "detect_delay_impact" in formatted
        assert "recommend_allocation" in formatted

    def test_format_tools_for_prompt_includes_descriptions(self):
        """Test that formatted output includes tool descriptions."""
        formatted = format_tools_for_prompt()
        assert "Description:" in formatted
        assert "demand patterns" in formatted.lower()  # From forecast_demand description

    def test_format_tools_for_prompt_includes_parameters(self):
        """Test that formatted output includes parameters."""
        formatted = format_tools_for_prompt()
        assert "Parameters:" in formatted
        assert "sku_id" in formatted
        assert "warehouse_id" in formatted
        assert "current_stock" in formatted

    def test_format_tools_for_prompt_numbered_list(self):
        """Test that formatted output has numbered list."""
        formatted = format_tools_for_prompt()
        assert "1." in formatted
        assert "2." in formatted
        assert "3." in formatted
        assert "4." in formatted
        assert "5." in formatted

    def test_format_tools_for_prompt_readable(self):
        """Test that formatted output is readable with clear structure."""
        formatted = format_tools_for_prompt()
        lines = formatted.split("\n")
        # Should have multiple lines, headers, descriptions, and parameters
        assert len(lines) > 50
        assert "=" * 80 in formatted  # Should have separator lines


class TestSystemPrompt:
    """Test system prompt generation."""

    def test_get_system_prompt_returns_string(self):
        """Test that get_system_prompt returns a string."""
        prompt = get_system_prompt()
        assert isinstance(prompt, str)
        assert len(prompt) > 100

    def test_get_system_prompt_includes_tools(self):
        """Test that system prompt includes tool registry."""
        prompt = get_system_prompt()
        assert "forecast_demand" in prompt
        assert "predict_stockout" in prompt
        assert "AVAILABLE TOOLS" in prompt

    def test_get_system_prompt_includes_guidelines(self):
        """Test that system prompt includes decision guidelines."""
        prompt = get_system_prompt()
        assert "DECISION GUIDELINES" in prompt
        assert "forecast_demand()" in prompt
        assert "predict_stockout()" in prompt

    def test_get_system_prompt_professional_tone(self):
        """Test that system prompt has professional tone."""
        prompt = get_system_prompt()
        assert "SupplySense" in prompt
        assert "supply chain" in prompt
        assert "recommendations" in prompt


class TestToolDistinction:
    """Test that tool descriptions are precise enough to distinguish usage."""

    def test_forecast_demand_distinct_from_predict_stockout(self):
        """Test that forecast_demand and predict_stockout have distinct purposes."""
        forecast_tool = get_tool_by_name("forecast_demand")
        stockout_tool = get_tool_by_name("predict_stockout")
        
        # Descriptions should be clearly different
        assert forecast_tool["description"] != stockout_tool["description"]
        # forecast_demand should mention "demand patterns"
        assert "demand" in forecast_tool["description"].lower()
        # predict_stockout should mention "days" or "shortage"
        assert "stockout" in stockout_tool["description"].lower() or "shortage" in stockout_tool["description"].lower()

    def test_supplier_risk_distinct_from_detect_delay(self):
        """Test that supplier_risk_score and detect_delay_impact are distinct."""
        supplier_tool = get_tool_by_name("supplier_risk_score")
        delay_tool = get_tool_by_name("detect_delay_impact")
        
        # supplier_risk_score should mention "supplier" or "reliability"
        assert "supplier" in supplier_tool["description"].lower() or "reliability" in supplier_tool["description"].lower()
        # detect_delay_impact should mention "delay" or "shipment"
        assert "delay" in delay_tool["description"].lower() or "shipment" in delay_tool["description"].lower()

    def test_recommend_allocation_distinct_purpose(self):
        """Test that recommend_allocation has clearly distinct purpose."""
        alloc_tool = get_tool_by_name("recommend_allocation")
        
        # Should mention allocation, fulfillment, or orders
        desc_lower = alloc_tool["description"].lower()
        assert "allocat" in desc_lower or "fulfill" in desc_lower or "order" in desc_lower

    def test_no_vague_descriptions(self):
        """Test that no tool descriptions use vague language."""
        vague_words = ["help", "assist", "support", "various", "multiple", "things", "stuff"]
        
        for tool in TOOLS:
            desc = tool["description"].lower()
            for vague in vague_words:
                # Allow "help" if it's part of a specific phrase
                if vague == "help" and "helpful" in desc:
                    continue
                assert vague not in desc, \
                    f"Tool '{tool['name']}' description contains vague word '{vague}'"


class TestParameterConsistency:
    """Test parameter consistency across tools."""

    def test_sku_id_defined_consistently(self):
        """Test that sku_id is defined consistently where used."""
        tools_with_sku = [
            get_tool_by_name("forecast_demand"),
            get_tool_by_name("predict_stockout"),
            get_tool_by_name("recommend_allocation"),
        ]
        
        for tool in tools_with_sku:
            if "sku_id" in tool["parameters"]:
                param = tool["parameters"]["sku_id"]
                assert param["type"] == "string"
                assert "identifier" in param["description"].lower()

    def test_warehouse_id_in_stockout_tool(self):
        """Test that predict_stockout has warehouse_id parameter."""
        tool = get_tool_by_name("predict_stockout")
        assert "warehouse_id" in tool["parameters"]
        assert tool["parameters"]["warehouse_id"]["type"] == "string"

    def test_forecast_result_in_stockout_tool(self):
        """Test that predict_stockout takes forecast_result parameter."""
        tool = get_tool_by_name("predict_stockout")
        assert "forecast_result" in tool["parameters"]
        param = tool["parameters"]["forecast_result"]
        assert "forecast_demand" in param["description"].lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
