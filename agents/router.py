"""
Router agent for intelligent request routing.

Routes user queries and automated tasks to appropriate agent handlers
based on query type, complexity, and execution context.
"""

import json
import logging
from typing import Any, Literal

logger = logging.getLogger(__name__)


def route_query(
    user_input: str,
    context: dict,
    bedrock_client: Any
) -> dict:
    """
    Route a user query to the appropriate handler.

    Uses Claude Haiku to classify the query and determine the best execution path:
    - "simple_lookup": single tool call (e.g., "What's SKU-X's forecast?")
    - "investigation": multi-step orchestration (e.g., "Why is there a delay?")
    - "monitoring": proactive scan (though typically scheduled)
    - "approval_review": critique an action
    - "clarification_needed": ambiguous, needs clarification

    Args:
        user_input: str - the user's question or request
        context: dict - session context {user_id, timestamp, previous_queries}
        bedrock_client: boto3 Bedrock runtime client

    Returns:
        dict with structure:
        {
            "route": str ("simple_lookup"|"investigation"|"monitoring"|"approval_review"|"clarification_needed"),
            "confidence": float (0.0-1.0),
            "reasoning": str (1-2 sentences),
            "recommended_tools": list[str] (e.g., ["forecast_demand", "predict_stockout"]),
            "requires_approval": bool,
            "urgent": bool
        }

    Raises:
        ValueError: If user_input is empty or None.
        TypeError: If bedrock_client is None.
    """
    if not user_input or not isinstance(user_input, str):
        raise ValueError("user_input must be a non-empty string")
    if bedrock_client is None or not hasattr(bedrock_client, "invoke_model"):
        raise TypeError("bedrock_client must be a boto3 Bedrock runtime client")

    system_prompt = (
        "You are a router for a supply chain AI agent. Given a user query, classify it "
        "into one of these routes: 'simple_lookup' (single tool), 'investigation' "
        "(multi-step root-cause), 'monitoring' (proactive scan), 'approval_review' "
        "(critique), or 'clarification_needed' (ambiguous). Respond ONLY with valid JSON: "
        '{"route": str, "confidence": float (0-1), "reasoning": str, "recommended_tools": [str], '
        '"requires_approval": bool, "urgent": bool}'
    )

    user_message = (
        f"User Query: {user_input}\n\n"
        f"Context: {json.dumps(context, default=str)}"
    )

    logger.info(f"[Router] Routing query: {user_input[:50]}...")

    try:
        response = bedrock_client.invoke_model(
            modelId="anthropic.claude-3-haiku-20240307",
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_message}
            ]
        )

        response_body = json.loads(response["body"].read().decode("utf-8"))
        response_text = response_body["content"][0]["text"]

        logger.debug(f"[Router] Bedrock response: {response_text[:100]}...")

        # Parse and validate response
        parsed = _parse_router_response(response_text)

        # Validate route is one of the allowed values
        if parsed["route"] not in [
            "simple_lookup",
            "investigation",
            "monitoring",
            "approval_review",
            "clarification_needed"
        ]:
            logger.error(f"[Router] Invalid route returned: {parsed['route']}")
            return _fallback_clarification_response(
                f"Router returned invalid route: {parsed['route']}"
            )

        logger.info(f"[Router] Routed to: {parsed['route']} (confidence: {parsed['confidence']})")
        return parsed

    except json.JSONDecodeError as e:
        logger.error(f"[Router] JSON parse error: {e}")
        return _fallback_clarification_response(f"Router parsing failed: {str(e)}")

    except Exception as e:
        logger.error(f"[Router] Unexpected error: {e}")
        return _fallback_clarification_response(f"Router error: {str(e)}")


def _parse_router_response(response_text: str) -> dict:
    """
    Parse router response, handling markdown fences.

    Args:
        response_text: Raw text from Bedrock.

    Returns:
        dict with all required fields, or raises on parse failure.
    """
    # Strip markdown code fences
    if response_text.startswith("```"):
        response_text = response_text.split("```")[1]
        if response_text.startswith("json"):
            response_text = response_text[4:]
    if response_text.endswith("```"):
        response_text = response_text[:-3]

    response_text = response_text.strip()
    parsed = json.loads(response_text)

    # Validate required fields
    required_fields = ["route", "confidence", "reasoning", "recommended_tools", "requires_approval", "urgent"]
    for field in required_fields:
        if field not in parsed:
            raise KeyError(f"Missing required field: {field}")

    return parsed


def _fallback_clarification_response(error_reason: str) -> dict:
    """
    Return a safe fallback routing to clarification.

    Args:
        error_reason: str description of the error.

    Returns:
        dict routing to clarification_needed.
    """
    return {
        "route": "clarification_needed",
        "confidence": 0.0,
        "reasoning": f"Unable to route due to: {error_reason}",
        "recommended_tools": [],
        "requires_approval": False,
        "urgent": False
    }


def should_escalate(
    route: str,
    findings: dict,
    approval_threshold: int = 3
) -> bool:
    """
    Determine if a result should be escalated for human review.

    Args:
        route: str - the route from route_query()
        findings: dict - results from execution (e.g., critical_stockouts count)
        approval_threshold: int - number of critical items triggering escalation

    Returns:
        bool - True if escalation recommended.
    """
    # Escalate if investigation found critical issues
    if route == "investigation":
        critical_count = findings.get("critical_count", 0)
        if critical_count >= approval_threshold:
            logger.warning(f"[Router] Escalating: {critical_count} critical findings")
            return True

    # Escalate if monitoring found issues
    if route == "monitoring":
        critical_stockouts = len(findings.get("critical_stockouts", []))
        risky_suppliers = len(findings.get("risky_suppliers", []))
        total_issues = critical_stockouts + risky_suppliers
        if total_issues >= approval_threshold:
            logger.warning(f"[Router] Escalating: {total_issues} total issues found")
            return True

    return False


if __name__ == "__main__":
    class MockBedrockClient:
        """Mock Bedrock client for testing."""

        def invoke_model(self, **kwargs):
            response_text = json.dumps({
                "route": "investigation",
                "confidence": 0.95,
                "reasoning": "Multi-step root-cause analysis needed.",
                "recommended_tools": ["predict_stockout", "supplier_risk_score"],
                "requires_approval": True,
                "urgent": True
            })

            class MockBody:
                def read(self):
                    return json.dumps({
                        "content": [{"text": response_text}]
                    }).encode('utf-8')

            return {"body": MockBody()}

    print("\n" + "="*80)
    print("ROUTER AGENT TEST")
    print("="*80 + "\n")

    mock_client = MockBedrockClient()

    # Test 1: Investigation query
    query1 = "Why is Widget stockout happening and which supplier is responsible?"
    context1 = {"user_id": "user-001", "timestamp": "2024-01-15T10:30:00Z"}

    result1 = route_query(query1, context1, mock_client)
    print(f"Test 1 - Investigation Query")
    print(f"  Query: {query1}")
    print(f"  Route: {result1['route']}")
    print(f"  Confidence: {result1['confidence']}")
    print(f"  Urgent: {result1['urgent']}")
    print(f"  Status: {'PASS' if result1['route'] == 'investigation' else 'FAIL'}\n")

    # Test 2: Escalation check
    findings = {
        "critical_count": 5,
        "critical_stockouts": [{"sku_id": "SKU-A"}, {"sku_id": "SKU-B"}, {"sku_id": "SKU-C"}],
        "risky_suppliers": [{"supplier_id": "SUP-X"}]
    }

    escalate = should_escalate("investigation", findings, approval_threshold=3)
    print(f"Test 2 - Escalation Check")
    print(f"  Critical Count: {findings['critical_count']}")
    print(f"  Threshold: 3")
    print(f"  Should Escalate: {escalate}")
    print(f"  Status: {'PASS' if escalate else 'FAIL'}\n")

    # Test 3: Input validation
    print(f"Test 3 - Input Validation")
    try:
        route_query("", {}, mock_client)
        print(f"  Status: FAIL (should raise ValueError)")
    except ValueError as e:
        print(f"  Caught ValueError: {str(e)[:50]}...")
        print(f"  Status: PASS\n")

    # Test 4: Fallback routing
    findings2 = {"critical_stockouts": []}
    escalate2 = should_escalate("investigation", findings2, approval_threshold=5)
    print(f"Test 4 - No Escalation Needed")
    print(f"  Critical Count: 0")
    print(f"  Should Escalate: {escalate2}")
    print(f"  Status: {'PASS' if not escalate2 else 'FAIL'}\n")

    print("="*80)
    print("ALL TESTS COMPLETED")
    print("="*80 + "\n")
