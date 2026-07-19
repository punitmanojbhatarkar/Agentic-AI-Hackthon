"""
Supply chain agent orchestrator for autonomous multi-step reasoning.

Coordinates planning, tool execution, and answer composition to provide
end-to-end agentic intelligence for supply chain queries.
"""

import logging
import re
from typing import Callable, Optional

# Import from same package (can use relative or absolute depending on context)
try:
    from agents.planner import plan_investigation
    from agents.composer import compose_answer
except ImportError:
    # Fallback for direct execution or package-context imports
    from planner import plan_investigation
    from composer import compose_answer


logger = logging.getLogger(__name__)


# Mapping of (tool_name, parameter_name) → (queries.py_function, foreign_key_params)
# Only parameters that should be fetched from DB are listed here.
# Input parameters (like sku_id, supplier_id, warehouse_id) must be provided, not fetched.
PARAMETER_DB_FETCHERS = {
    # forecast_demand: fetch historical_demand using sku_id from parameters
    ("forecast_demand", "historical_demand"): ("get_demand_history", "sku_id"),
    
    # predict_stockout: fetch current_stock using sku_id and warehouse_id
    ("predict_stockout", "current_stock"): ("get_current_stock", ["sku_id", "warehouse_id"]),
    
    # supplier_risk_score: fetch delivery_history using supplier_id
    ("supplier_risk_score", "delivery_history"): ("get_supplier_delivery_history", "supplier_id"),
    
    # detect_delay_impact: fetch shipment_data and downstream_orders using shipment_id
    ("detect_delay_impact", "shipment_id"): ("get_most_delayed_shipment_id", []),
    ("detect_delay_impact", "shipment_data"): ("get_shipment_data", "shipment_id"),
    ("detect_delay_impact", "downstream_orders"): ("get_downstream_orders", "shipment_id"),
    
    # recommend_allocation: fetch available_stock and pending_orders
    ("recommend_allocation", "available_stock"): ("get_sku_total_stock", "sku_id"),
    ("recommend_allocation", "pending_orders"): ("get_pending_orders", "sku_id"),

    # recommend_alternate_source: fetch candidate lists from DB
    ("recommend_alternate_source", "candidate_suppliers"): ("get_all_supplier_risk_scores", []),
    ("recommend_alternate_source", "candidate_warehouse_stocks"): ("get_all_warehouse_stocks_for_sku", "sku_id"),
}



class SupplyChainAgent:
    """
    Autonomous supply chain intelligence agent.

    This agent coordinates multi-step reasoning and tool execution:
    1. Receives a user question
    2. Plans a sequence of tool calls (via planner, using CodeBender's configured provider)
    3. Executes tools in dependency order, substituting results as parameters
    4. Composes a natural language answer with confidence (via composer)
    5. Returns a complete execution trace for transparency

    This is the single entry point for external systems (n8n, APIs, etc.).

    Attributes:
        bedrock_client: (Deprecated - kept for backward compatibility, ignored).
                       Now uses CodeBender's configured provider via spawn_agent.
        tool_functions: Mapping of tool names to callable backend functions.
                       Example:
                       {
                           "forecast_demand": backend.forecasting.forecast_demand,
                           "predict_stockout": backend.inventory.predict_stockout,
                           ...
                       }
    """

    def __init__(
        self,
        bedrock_client=None,  # Now optional - CodeBender uses spawn_agent
        tool_functions: dict[str, Callable] = None,
    ) -> None:
        """
        Initialize the supply chain agent.

        Args:
            bedrock_client: (Optional, deprecated - kept for backward compatibility).
                           Now uses CodeBender's configured provider via spawn_agent.
                           Can be None.
            tool_functions: Mapping of tool names (str) to backend functions (Callable).
                           Keys must match tool names in tool_registry.TOOLS.
                           Values are the actual Python functions to execute.
                           Example: {"forecast_demand": forecast_demand_fn, ...}

        Raises:
            TypeError: If tool_functions is not a dict or None.
            ValueError: If tool_functions is empty.
        """
        if tool_functions is None:
            raise TypeError("tool_functions cannot be None")
        if not isinstance(tool_functions, dict):
            raise TypeError(
                f"tool_functions must be dict, got {type(tool_functions).__name__}"
            )
        if len(tool_functions) == 0:
            raise ValueError("tool_functions cannot be empty")

        self.bedrock_client = bedrock_client  # May be None - spawn_agent doesn't need it
        self.tool_functions = tool_functions
        self.tool_names = set(tool_functions.keys())

        logger.info(
            f"SupplyChainAgent initialized with {len(self.tool_functions)} tools: "
            f"{', '.join(sorted(self.tool_names))}"
        )

    def answer_query(self, user_question: str) -> dict:
        """
        Answer a supply chain query end-to-end.

        This is the main entry point. The agent:
        1. Plans a sequence of tool calls to answer the question
        2. Executes tools in order, handling dependencies
        3. Collects results into an execution trace
        4. Composes a final answer with confidence and caveats
        5. Returns the complete response for transparency

        Args:
            user_question: User's supply chain question (str).
                          Examples:
                          - "Is SKU-WIDGET at risk of stockout?"
                          - "What's causing today's biggest disruption?"
                          - "Which supplier should we use for urgent restock?"

        Returns:
            dict with keys:
                - question: str — the original user question
                - execution_trace: list[dict] — each step's result:
                    {
                        "step": int,
                        "tool": str (name),
                        "parameters_used": dict (substituted params),
                        "reasoning": str (why this tool was called),
                        "result": dict (tool's output) or "error": str (if failed)
                    }
                - final_answer: str — 2-3 sentence answer
                - confidence: str — "high" | "medium" | "low"
                - caveats: str — one-phrase limitations
                - error_summary: str (only if planning/execution failed)

        Error Handling:
            - Planning failure: returns fallback response with error_summary
            - Tool execution failure: continues to next tool, records error in trace
            - Composition failure: returns fallback with error_summary
            All errors logged; agent never crashes.
        """
        logger.info(f"Received query: {user_question}")

        try:
            # ===================================================================
            # Step 1: Generate plan
            # ===================================================================
            logger.info(f"Planning investigation for question: {user_question[:60]}...")

            try:
                from agents.tool_registry import format_tools_for_prompt
            except ImportError:
                from tool_registry import format_tools_for_prompt

            tools_description = format_tools_for_prompt()

            tools_description = format_tools_for_prompt()
            planned_steps = plan_investigation(
                user_question,
                tools_description,
                self.bedrock_client
            )

            if len(planned_steps) == 0:
                error_msg = "Planning failed: could not generate tool sequence"
                logger.error(error_msg)
                return self._fallback_response(user_question, error_msg)

            logger.info(f"Generated plan with {len(planned_steps)} steps")

            # ===================================================================
            # Step 2: Execute plan
            # ===================================================================
            execution_trace: list[dict] = []
            step_results: dict = {}  # Cache results for FROM_STEP_N substitution

            for planned_step in planned_steps:
                try:
                    step_num: int = planned_step["step"]
                    tool_name: str = planned_step["tool"]
                    parameters: dict = planned_step["parameters"]
                    reasoning: str = planned_step["reasoning"]

                    logger.info(f"Executing step {step_num}: {tool_name}")

                    # ------------------------------------------------------------------
                    # Substitute FROM_STEP_N placeholders with actual results
                    # ------------------------------------------------------------------
                    substituted_params = self._substitute_dependencies(
                        parameters, step_results, tool_name
                    )

                    # ------------------------------------------------------------------
                    # Execute the tool
                    # ------------------------------------------------------------------
                    if tool_name not in self.tool_functions:
                        error_msg = f"Tool '{tool_name}' not found in tool_functions"
                        logger.error(error_msg)
                        execution_trace.append({
                            "step": step_num,
                            "tool": tool_name,
                            "parameters_used": substituted_params,
                            "reasoning": reasoning,
                            "error": error_msg,
                        })
                        continue

                    tool_func: Callable = self.tool_functions[tool_name]

                    try:
                        result = tool_func(**substituted_params)
                        logger.debug(f"Step {step_num} result: {result}")

                        # Cache result for future steps (use numeric key)
                        step_results[step_num] = result

                        execution_trace.append({
                            "step": step_num,
                            "tool": tool_name,
                            "parameters_used": substituted_params,
                            "reasoning": reasoning,
                            "result": result,
                        })

                        logger.info(f"Step {step_num} completed successfully")

                    except Exception as e:
                        error_msg = f"Tool execution failed: {str(e)}"
                        logger.error(
                            f"Step {step_num} execution failed: {e}", exc_info=True
                        )
                        execution_trace.append({
                            "step": step_num,
                            "tool": tool_name,
                            "parameters_used": substituted_params,
                            "reasoning": reasoning,
                            "error": error_msg,
                        })
                        # Continue to next step rather than crashing

                except Exception as e:
                    logger.error(
                        f"Unexpected error in step {step_num}: {e}", exc_info=True
                    )
                    # Continue with next step

            if len(execution_trace) == 0:
                error_msg = "No tools executed successfully"
                logger.error(error_msg)
                return self._fallback_response(user_question, error_msg)

            logger.info(f"Execution complete: {len(execution_trace)} steps")

            # ===================================================================
            # Step 3: Compose final answer
            # ===================================================================
            logger.info("Composing final answer")

            composed = compose_answer(
                user_question,
                execution_trace,
                self.bedrock_client
            )

            # Build final response
            response: dict = {
                "question": user_question,
                "execution_trace": execution_trace,
                "final_answer": composed.get("answer", ""),
                "confidence": composed.get("confidence", "low"),
                "caveats": composed.get("caveats", "Unknown limitations"),
            }

            logger.info(
                f"Query complete. Confidence: {response['confidence']}, "
                f"Caveats: {response['caveats']}"
            )
            return response

        except Exception as e:
            logger.error(f"Query processing failed: {e}", exc_info=True)
            return self._fallback_response(
                user_question,
                f"Query processing error: {str(e)}"
            )

    # =========================================================================
    # HELPER METHODS
    # =========================================================================

    def _substitute_dependencies(
        self,
        parameters: dict,
        step_results: dict,
        tool_name: str = None
    ) -> dict:
        """
        Substitute FROM_STEP_N and FROM_DB placeholders in parameters.

        Handles:
        - FROM_STEP_N: replaced with result from step N
        - FROM_DB: replaced with data fetched from queries.py based on tool and param name

        Args:
            parameters: Original parameters dict.
            step_results: Cache of previous step results {step_num: result_dict}.
            tool_name: Name of the tool being executed (for FROM_DB resolution).

        Returns:
            dict: Parameters with all placeholders substituted.
        """
        substituted: dict = {}

        for param_name, param_value in parameters.items():
            if isinstance(param_value, str):
                # Check for FROM_STEP_N pattern
                match = re.match(r"FROM_STEP_(\d+)(?:\['([^\]]+)'\])?", param_value)

                if match:
                    step_num_str: str = match.group(1)
                    result_key: Optional[str] = match.group(2)

                    try:
                        step_num: int = int(step_num_str)
                    except ValueError:
                        logger.error(f"Invalid step number in {param_value}")
                        substituted[param_name] = param_value
                        continue

                    if step_num not in step_results:
                        error_msg = (
                            f"FROM_STEP_{step_num} referenced but step {step_num} "
                            f"not executed or failed"
                        )
                        logger.warning(error_msg)
                        substituted[param_name] = None
                        continue

                    result = step_results[step_num]

                    if result_key:
                        substituted[param_name] = result.get(result_key)
                        logger.debug(
                            f"{param_name} = FROM_STEP_{step_num}['{result_key}'] "
                            f"→ {type(substituted[param_name]).__name__}"
                        )
                    else:
                        substituted[param_name] = result
                        logger.debug(
                            f"{param_name} = FROM_STEP_{step_num} (full result)"
                        )

                # Check for FROM_DB pattern
                elif param_value == "FROM_DB":
                    substituted[param_name] = self._fetch_from_db(
                        tool_name, param_name, parameters, step_results
                    )
                    logger.debug(
                        f"{param_name} = FROM_DB → fetched {type(substituted[param_name]).__name__}"
                    )

                else:
                    substituted[param_name] = param_value

            else:
                substituted[param_name] = param_value

        return substituted



    def _fetch_from_db(
        self,
        tool_name: str,
        param_name: str,
        parameters: dict,
        step_results: dict
    ) -> Optional[object]:
        """
        Fetch data from database for FROM_DB placeholder.

        Uses PARAMETER_DB_FETCHERS mapping to determine which queries.py function to call.

        Args:
            tool_name: Name of the tool requesting data.
            param_name: Name of the parameter to fill.
            parameters: All parameters for this step (for extracting FK values).
            step_results: Cache of previous results (for extracting FK values).

        Returns:
            Fetched data or None if fetch fails.
        """
        try:
            from data.queries import (
                get_demand_history,
                get_current_stock,
                get_supplier_delivery_history,
                get_shipment_data,
                get_downstream_orders,
                get_pending_orders,
                get_sku_total_stock,
                get_most_delayed_shipment_id,
                get_all_supplier_risk_scores,
                get_all_warehouse_stocks_for_sku,
            )

        except ImportError:
            logger.error("Could not import queries module")
            return None

        key = (tool_name, param_name)
        if key not in PARAMETER_DB_FETCHERS:
            logger.warning(
                f"No DB fetcher defined for ({tool_name}, {param_name}); "
                f"returning None"
            )
            return None

        fetcher_name, fk_param = PARAMETER_DB_FETCHERS[key]
        fetcher_map = {
            "get_demand_history": get_demand_history,
            "get_current_stock": get_current_stock,
            "get_supplier_delivery_history": get_supplier_delivery_history,
            "get_shipment_data": get_shipment_data,
            "get_downstream_orders": get_downstream_orders,
            "get_pending_orders": get_pending_orders,
            "get_sku_total_stock": get_sku_total_stock,
            "get_most_delayed_shipment_id": get_most_delayed_shipment_id,
            "get_all_supplier_risk_scores": get_all_supplier_risk_scores,
            "get_all_warehouse_stocks_for_sku": get_all_warehouse_stocks_for_sku,
        }


        fetcher = fetcher_map.get(fetcher_name)
        if not fetcher:
            logger.error(f"Fetcher {fetcher_name} not found")
            return None

        # Extract foreign key value(s) from parameters or previous results
        try:
            if isinstance(fk_param, list):
                # Multiple FKs (e.g., ["sku_id", "warehouse_id"])
                fk_values = []
                for fk in fk_param:
                    if fk in parameters:
                        fk_values.append(parameters[fk])
                    else:
                        logger.error(f"FK {fk} not found in parameters")
                        return None
                result = fetcher(*fk_values)
            else:
                # Single FK
                if fk_param in parameters:
                    fk_value = parameters[fk_param]
                else:
                    logger.error(f"FK {fk_param} not found in parameters")
                    return None
                result = fetcher(fk_value)

            logger.debug(f"Fetched {fetcher_name}({fk_param}) successfully")
            return result

        except Exception as e:
            logger.error(f"Failed to fetch {fetcher_name}: {e}", exc_info=True)
            return None

    def _fallback_response(
        self,
        user_question: str,
        error_reason: str
    ) -> dict:
        """
        Generate a graceful fallback response when the agent fails.

        Args:
            user_question: The original user question.
            error_reason: Brief explanation of what failed.

        Returns:
            dict: Response with error_summary and low confidence.
        """
        logger.warning(f"Returning fallback response: {error_reason}")
        return {
            "question": user_question,
            "execution_trace": [],
            "final_answer": "I was unable to answer your question due to an internal error.",
            "confidence": "low",
            "caveats": error_reason,
            "error_summary": error_reason,
        }

    def get_available_tools(self) -> list[str]:
        """
        Get list of available tool names.

        Returns:
            list[str]: Sorted list of tool names this agent can execute.
        """
        return sorted(self.tool_names)

    def get_tool_count(self) -> int:
        """
        Get count of available tools.

        Returns:
            int: Number of tools registered with this agent.
        """
        return len(self.tool_functions)


# ═══════════════════════════════════════════════════════════════════════════════
# UTILITY FUNCTION FOR INITIALIZATION
# ═══════════════════════════════════════════════════════════════════════════════

def create_agent(bedrock_client) -> SupplyChainAgent:
    """
    Factory function to create a fully initialized SupplyChainAgent.

    This convenience function imports all backend tools and builds the tool_functions
    mapping, making it easy to instantiate the agent in downstream systems (n8n, APIs).

    Args:
        bedrock_client: Initialized AWS Bedrock client with credentials.

    Returns:
        SupplyChainAgent: Ready-to-use agent instance.

    Raises:
        ImportError: If backend modules cannot be imported.
        RuntimeError: If agent creation fails for any other reason.

    Example:
        >>> import boto3
        >>> client = boto3.client("bedrock-runtime", region_name="us-east-1")
        >>> agent = create_agent(client)
        >>> response = agent.answer_query("Is SKU-WIDGET at risk?")
    """
    try:
        try:
            from backend.forecasting import forecast_demand
            from backend.inventory import predict_stockout
            from backend.suppliers import supplier_risk_score
            from backend.shipments import detect_delay_impact
            from backend.allocation import recommend_allocation
            from backend.recommend_alternate import recommend_alternate_source
        except ImportError:
            # Fallback for different import contexts
            import sys
            import os
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
            from backend.forecasting import forecast_demand
            from backend.inventory import predict_stockout
            from backend.suppliers import supplier_risk_score
            from backend.shipments import detect_delay_impact
            from backend.allocation import recommend_allocation
            from backend.recommend_alternate import recommend_alternate_source

        tool_functions: dict[str, Callable] = {
            "forecast_demand": forecast_demand,
            "predict_stockout": predict_stockout,
            "supplier_risk_score": supplier_risk_score,
            "detect_delay_impact": detect_delay_impact,
            "recommend_allocation": recommend_allocation,
            "recommend_alternate_source": recommend_alternate_source,
        }

        agent = SupplyChainAgent(bedrock_client, tool_functions)
        logger.info("SupplyChainAgent created successfully via create_agent()")
        return agent

    except ImportError as e:
        logger.error(f"Failed to import backend modules: {e}", exc_info=True)
        raise RuntimeError(f"Cannot create agent: backend modules not found: {e}")
    except Exception as e:
        logger.error(f"Failed to create agent: {e}", exc_info=True)
        raise


