import json
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def plan_investigation(
    user_question: str,
    tools_description: str,
    bedrock_client=None,
) -> list[dict]:
    """
    Generate a sequence of tool calls dynamically using Groq LLM.
    Falls back to deterministic planning if the LLM fails or returns invalid tools.
    """
    try:
        from data.queries import (
            get_all_sku_ids,
            get_all_supplier_ids,
            get_all_warehouse_ids,
        )
    except ImportError:
        logger.error("Could not import queries")
        return []

    try:
        # Fetch real IDs from database to provide as context to the LLM
        all_skus = get_all_sku_ids()
        all_suppliers = get_all_supplier_ids()
        all_warehouses = get_all_warehouse_ids()

        sku_id = all_skus[0] if all_skus else "SKU-UNKNOWN"
        supplier_id = all_suppliers[0] if all_suppliers else "SUP-UNKNOWN"
        warehouse_id = all_warehouses[0] if all_warehouses else "WH-UNKNOWN"

        logger.info(f"LLM Planning with sample context: sku={sku_id}, supplier={supplier_id}, warehouse={warehouse_id}")

        from agents.groq_provider import call_groq

        system_prompt = f"""You are a supply chain AI planner.
Your job is to break down a user's question into a sequence of tool calls.
Available tools:
{tools_description}

You must return ONLY a JSON array of step objects, like this:
[
  {{
    "step": 1,
    "tool": "tool_name",
    "parameters": {{"param": "value"}},
    "depends_on_previous": false,
    "reasoning": "Why this tool is used"
  }}
]
For parameters that require database fetching (like historical_demand or current_stock), use "FROM_DB".
For parameters that depend on a previous step's output, use "FROM_STEP_N" (where N is the step number) or "FROM_STEP_N['key']".
Available IDs you can use if needed (do not hallucinate other IDs):
- SKU: {sku_id}
- Supplier: {supplier_id}
- Warehouse: {warehouse_id}

Return ONLY valid JSON. No markdown formatting, no explanations."""

        response = call_groq(
            system_prompt=system_prompt,
            user_message=user_question,
            max_tokens=1500,
            temperature=0.2
        )

        # Parse JSON
        json_start = response.find('[')
        json_end = response.rfind(']') + 1
        
        if json_start >= 0 and json_end > json_start:
            plan_str = response[json_start:json_end]
            plan = json.loads(plan_str)
            
            # Validate plan format and tools
            try:
                from agents.tool_registry import get_tool_names
                valid_tools = set(get_tool_names())
                
                valid_plan = True
                for step in plan:
                    if step.get("tool") not in valid_tools:
                        logger.warning(f"Invalid tool returned by LLM: {step.get('tool')}")
                        valid_plan = False
                        break
                        
                if valid_plan and len(plan) > 0:
                    logger.info("Successfully generated and validated dynamic LLM plan")
                    return plan
                    
            except ImportError:
                # If we can't import registry, just assume it's valid if we parsed it
                if len(plan) > 0:
                    logger.info("Generated LLM plan (validation skipped)")
                    return plan
                    
        logger.warning("LLM response did not contain a valid JSON array or failed validation. Falling back.")
        
    except Exception as e:
        logger.error(f"Dynamic planner failed: {e}", exc_info=True)
        
    # Fallback to deterministic logic
    return _get_fallback_plan(user_question, sku_id, supplier_id, warehouse_id)


def _get_fallback_plan(user_question: str, sku_id: str, supplier_id: str, warehouse_id: str) -> list[dict]:
    """Fallback deterministic logic from the original planner."""
    q_lower = user_question.lower()

    if "stockout" in q_lower or "inventory" in q_lower:
        return [
            {
                "step": 1,
                "tool": "forecast_demand",
                "parameters": {
                    "sku_id": sku_id,
                    "historical_demand": "FROM_DB",
                },
                "depends_on_previous": False,
                "reasoning": "Forecast demand for the SKU to analyze inventory levels",
            },
            {
                "step": 2,
                "tool": "predict_stockout",
                "parameters": {
                    "sku_id": sku_id,
                    "warehouse_id": warehouse_id,
                    "current_stock": "FROM_DB",
                    "forecast_result": "FROM_STEP_1",
                },
                "depends_on_previous": True,
                "reasoning": "Predict stockout risk using the forecast",
            },
        ]

    elif "supplier" in q_lower or "reliability" in q_lower:
        return [
            {
                "step": 1,
                "tool": "supplier_risk_score",
                "parameters": {
                    "supplier_id": supplier_id,
                    "delivery_history": "FROM_DB",
                },
                "depends_on_previous": False,
                "reasoning": "Evaluate supplier reliability and performance",
            },
        ]

    elif "delay" in q_lower or "disruption" in q_lower or "biggest" in q_lower:
        return [
            {
                "step": 1,
                "tool": "forecast_demand",
                "parameters": {
                    "sku_id": sku_id,
                    "historical_demand": "FROM_DB",
                },
                "depends_on_previous": False,
                "reasoning": "Forecast demand for inventory analysis",
            },
            {
                "step": 2,
                "tool": "predict_stockout",
                "parameters": {
                    "sku_id": sku_id,
                    "warehouse_id": warehouse_id,
                    "current_stock": "FROM_DB",
                    "forecast_result": "FROM_STEP_1",
                },
                "depends_on_previous": True,
                "reasoning": "Assess stockout risk",
            },
            {
                "step": 3,
                "tool": "supplier_risk_score",
                "parameters": {
                    "supplier_id": supplier_id,
                    "delivery_history": "FROM_DB",
                },
                "depends_on_previous": False,
                "reasoning": "Evaluate supplier reliability as potential cause",
            },
            {
                "step": 4,
                "tool": "recommend_allocation",
                "parameters": {
                    "sku_id": sku_id,
                    "available_stock": "FROM_DB",
                    "pending_orders": "FROM_DB",
                },
                "depends_on_previous": False,
                "reasoning": "Recommend allocation strategy for affected SKU",
            },
        ]

    else:
        return [
            {
                "step": 1,
                "tool": "forecast_demand",
                "parameters": {
                    "sku_id": sku_id,
                    "historical_demand": "FROM_DB",
                },
                "depends_on_previous": False,
                "reasoning": "Forecast demand",
            },
            {
                "step": 2,
                "tool": "predict_stockout",
                "parameters": {
                    "sku_id": sku_id,
                    "warehouse_id": warehouse_id,
                    "current_stock": "FROM_DB",
                    "forecast_result": "FROM_STEP_1",
                },
                "depends_on_previous": True,
                "reasoning": "Predict stockout risk",
            },
        ]
