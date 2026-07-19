"""
Tool registry for agentic supply chain intelligence.

Provides LLM with structured access to all backend business logic functions,
including tool metadata, parameter descriptions, and usage guidelines.
"""

from typing import Optional


# ═══════════════════════════════════════════════════════════════════════════════
# TOOL DEFINITIONS
# ═══════════════════════════════════════════════════════════════════════════════

TOOLS = [
    {
        "name": "forecast_demand",
        "description": "Predict next 7 days of daily demand for a SKU using 90 days of historical sales data; use this to understand future demand patterns and trends before making inventory or sourcing decisions.",
        "parameters": {
            "sku_id": {
                "type": "string",
                "description": "Unique stock keeping unit identifier (e.g., 'SKU-WIDGET-100')."
            },
            "historical_demand": {
                "type": "list[dict]",
                "description": "List of historical daily sales records, each with 'date' (YYYY-MM-DD format) and 'units_sold' (integer). Typically 90 days of data; minimum 1 day required."
            }
        }
    },
    {
        "name": "predict_stockout",
        "description": "Calculate days until stockout at a specific warehouse for a given SKU and forecasted demand; use this to identify critical inventory shortages and determine urgent restock needs by location.",
        "parameters": {
            "sku_id": {
                "type": "string",
                "description": "Unique stock keeping unit identifier (e.g., 'SKU-WIDGET-100')."
            },
            "warehouse_id": {
                "type": "string",
                "description": "Unique warehouse location identifier (e.g., 'WH-MAIN', 'WH-EAST', 'WH-NORTH')."
            },
            "current_stock": {
                "type": "integer",
                "description": "Current inventory quantity in units at the warehouse (non-negative integer)."
            },
            "forecast_result": {
                "type": "dict",
                "description": "Output dictionary from forecast_demand() containing 'avg_forecasted_demand' (float, units/day), 'trend' (str), 'confidence' (float 0-1), and other forecast metrics."
            }
        }
    },
    {
        "name": "supplier_risk_score",
        "description": "Evaluate supplier reliability using a weighted composite score (0-100) based on on-time delivery percentage, lead time consistency, and product quality; use this to select trustworthy suppliers and rank alternative sources.",
        "parameters": {
            "supplier_id": {
                "type": "string",
                "description": "Unique supplier identifier (e.g., 'SUP-RELIABLE-001', 'SUP-VENDOR-B')."
            },
            "delivery_history": {
                "type": "list[dict]",
                "description": "List of past delivery records, each with 'order_id' (str), 'promised_date' (YYYY-MM-DD), 'actual_date' (YYYY-MM-DD or None if not delivered), and 'quality_rating' (integer 1-10). Minimum 1 record required."
            }
        }
    },
    {
        "name": "detect_delay_impact",
        "description": "Quantify the business impact of a shipment delay using a weighted score (0-100) based on downstream customer orders, with premium customers weighted 2x higher; use this to prioritize which delays need immediate escalation.",
        "parameters": {
            "shipment_id": {
                "type": "string",
                "description": "Unique shipment identifier (e.g., 'SHIP-123', 'SHIP-URGENT-001')."
            },
            "shipment_data": {
                "type": "dict",
                "description": "Shipment status dict with 'promised_date' (YYYY-MM-DD), 'current_status' (str, e.g., 'in_transit', 'delayed'), and 'estimated_delivery' (YYYY-MM-DD or None)."
            },
            "downstream_orders": {
                "type": "list[dict]",
                "description": "List of dependent customer orders, each with 'order_id' (str), 'customer_tier' ('premium' or 'standard'), 'sku_id' (str), and 'quantity' (integer). Minimum 0 orders (empty list allowed)."
            }
        }
    },
    {
        "name": "recommend_allocation",
        "description": "Allocate limited inventory across pending customer orders using a priority rule: premium tier customers first (earliest orders first), then standard tier (earliest first); use this to optimize fulfillment fairness while respecting stock constraints.",
        "parameters": {
            "sku_id": {
                "type": "string",
                "description": "Unique stock keeping unit identifier (e.g., 'SKU-WIDGET-100')."
            },
            "available_stock": {
                "type": "integer",
                "description": "Inventory quantity available for allocation (non-negative integer)."
            },
            "pending_orders": {
                "type": "list[dict]",
                "description": "List of pending customer orders waiting for fulfillment, each with 'order_id' (str), 'customer_tier' ('premium' or 'standard'), 'quantity_requested' (integer), and 'order_date' (YYYY-MM-DD). Minimum 0 orders (empty list allowed)."
            }
        }
    },
    {
        "name": "recommend_alternate_source",
        "description": "When a supplier is high-risk or a warehouse has insufficient stock, recommend the next-best alternative: either the top-scoring alternate supplier for the affected SKU, or the warehouse with the most surplus stock. Use this after supplier_risk_score identifies a high-risk supplier, or after predict_stockout identifies a warehouse shortage.",
        "parameters": {
            "failing_id": {
                "type": "string",
                "description": "The supplier_id (e.g., 'SUP014') or warehouse_id (e.g., 'WH-EAST') that is failing or at-risk. Must start with 'SUP' for supplier scenarios or 'WH' for warehouse scenarios."
            },
            "sku_id": {
                "type": "string",
                "description": "The SKU affected by the failure or shortage (e.g., 'SKU008')."
            },
            "candidate_suppliers": {
                "type": "list[dict]",
                "description": "List of evaluated supplier risk dicts from supplier_risk_score(), each with 'supplier_id', 'score', 'risk_category', and 'breakdown'. Pass [] for warehouse scenarios."
            },
            "candidate_warehouse_stocks": {
                "type": "list[dict]",
                "description": "List of warehouse stock dicts, each with 'warehouse_id' and 'current_stock'. Pass [] for supplier scenarios."
            }
        }
    }
]


# ═══════════════════════════════════════════════════════════════════════════════
# TOOL REGISTRY FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def get_tool_by_name(name: str) -> Optional[dict]:
    """
    Retrieve a tool definition by its name.

    Args:
        name: Name of the tool to retrieve (e.g., 'forecast_demand').

    Returns:
        dict: Tool definition if found, None otherwise.
        Structure: {"name", "description", "parameters"}
    """
    for tool in TOOLS:
        if tool["name"] == name:
            return tool
    return None


def format_tools_for_prompt() -> str:
    """
    Format the full tool registry as a clean numbered list suitable for
    insertion into an LLM system prompt.

    This generates a human-readable and LLM-friendly markdown-style list
    that clearly distinguishes each tool's purpose and parameters.

    Returns:
        str: Formatted tool registry (multi-line string).

    Example output:
        1. forecast_demand
           Description: Predict next 7 days of daily demand...
           Parameters:
             - sku_id (string): Unique stock keeping unit identifier...
             - historical_demand (list[dict]): List of historical daily sales...
        2. predict_stockout
           ...
    """
    lines: list[str] = []
    lines.append("=" * 80)
    lines.append("AVAILABLE TOOLS FOR SUPPLY CHAIN INTELLIGENCE")
    lines.append("=" * 80)
    lines.append("")

    for idx, tool in enumerate(TOOLS, start=1):
        tool_name: str = tool["name"]
        description: str = tool["description"]
        parameters: dict = tool["parameters"]

        # Tool header
        lines.append(f"{idx}. {tool_name}")
        lines.append(f"   Description: {description}")
        lines.append("")

        # Parameters section
        if parameters:
            lines.append("   Parameters:")
            for param_name, param_info in parameters.items():
                param_type: str = param_info["type"]
                param_desc: str = param_info["description"]
                lines.append(f"     • {param_name} ({param_type})")
                lines.append(f"       {param_desc}")
            lines.append("")
        else:
            lines.append("   Parameters: None")
            lines.append("")

    lines.append("=" * 80)

    return "\n".join(lines)


def get_tool_names() -> list[str]:
    """
    Get a list of all available tool names.

    Returns:
        list[str]: Tool names (e.g., ['forecast_demand', 'predict_stockout', ...])
    """
    return [tool["name"] for tool in TOOLS]


def get_tool_count() -> int:
    """
    Get the total number of available tools.

    Returns:
        int: Number of tools in the registry.
    """
    return len(TOOLS)


def validate_tool_exists(name: str) -> bool:
    """
    Check if a tool with the given name exists in the registry.

    Args:
        name: Tool name to check.

    Returns:
        bool: True if tool exists, False otherwise.
    """
    return get_tool_by_name(name) is not None


# ═══════════════════════════════════════════════════════════════════════════════
# SYSTEM PROMPT TEMPLATE
# ═══════════════════════════════════════════════════════════════════════════════

SYSTEM_PROMPT_TEMPLATE = """
You are SupplySense, an agentic supply chain intelligence assistant.

Your role is to analyze supply chain situations, make data-driven recommendations,
and help users optimize inventory, sourcing, and fulfillment decisions.

You have access to the following tools to gather intelligence and perform analysis:

{tools_list}

DECISION GUIDELINES:
- Use forecast_demand() first when you need to understand future demand patterns
- Use predict_stockout() when you've forecasted demand and need to identify risk
- Use supplier_risk_score() when evaluating alternative suppliers or sourcing options
- Use detect_delay_impact() when assessing the business consequence of a shipment delay
- Use recommend_allocation() when deciding how to fulfill orders with limited stock
- Use recommend_alternate_source() after supplier_risk_score identifies high-risk suppliers (pass failing_id=supplier_id, candidate_suppliers=list of scored suppliers) or after predict_stockout identifies a warehouse shortage (pass failing_id=warehouse_id, candidate_warehouse_stocks=list of {warehouse_id, current_stock})

When responding:
1. Clearly state what decision you're trying to make
2. Call the appropriate tool(s) with relevant parameters
3. Interpret the results in business context
4. Provide specific, actionable recommendations

Remember: All dates must be in YYYY-MM-DD format. All quantities are in units.
Stock levels, order quantities, and forecasts are always non-negative integers or floats.
"""


def get_system_prompt() -> str:
    """
    Generate a complete system prompt for the LLM including tool registry.

    Returns:
        str: Full system prompt with formatted tools.
    """
    tools_list = format_tools_for_prompt()
    return SYSTEM_PROMPT_TEMPLATE.format(tools_list=tools_list)
