"""
Critic agent for self-review of proposed actions.

Reviews proposed actions for soundness and identifies potential flaws before
they are executed or approved.

Uses Groq's llama-3.3-70b-versatile model for intelligent critique.
"""

import json
import logging

logger = logging.getLogger(__name__)


def review_proposed_action(
    proposed_action: dict,
    supporting_data: dict,
    bedrock_client=None,
) -> dict:
    """
    Review a proposed action for soundness and potential flaws.

    Uses Groq (via llama-3.3-70b) to critically evaluate proposed actions
    and identify logical flaws, missing considerations, or risks.

    Args:
        proposed_action: Action proposal dict with keys:
                        - action_id: str (UUID)
                        - action_type: str ("reorder" | "switch_supplier")
                        - details: dict (action-specific details)
                        - reasoning: str (why action was proposed)
        supporting_data: Dict with evidence/context for the review.
        bedrock_client: (Ignored - uses Groq instead).

    Returns:
        dict with keys:
            - "review": str (flaw identification, or exactly "No issues found." for approval)
            - "verdict": "approved" | "flagged"
    """
    from agents.groq_provider import call_groq

    try:
        action_json = json.dumps(proposed_action, indent=2, default=str)
        data_json = json.dumps(supporting_data, indent=2, default=str)

        logger.info(f"Reviewing action: {proposed_action.get('action_type')}")

        system_prompt = """You are a skeptical reviewer for a supply chain AI agent.

Your job is to identify potential flaws, missing considerations, or risks in proposed actions.

Given a proposed action and its supporting data, write a ONE-SENTENCE critique identifying any issues.

If the action is sound with no issues, respond exactly: "No issues found."

Respond ONLY with valid JSON, no other text:
{"review": "...", "verdict": "approved|flagged"}

IMPORTANT: If your review says "No issues found.", the verdict MUST be "approved". Otherwise, set verdict to "flagged"."""

        user_message = f"""Proposed action:
{action_json}

Supporting data:
{data_json}"""

        result = call_groq(
            system_prompt=system_prompt,
            user_message=user_message,
            max_tokens=500,
            temperature=0.3,  # Low temperature for conservative criticism
        )

        logger.debug(f"Critic Groq response: {result[:300]}")

        # Try to extract JSON from response
        try:
            if "{" in result:
                json_start = result.index("{")
                json_end = result.rfind("}") + 1
                json_str = result[json_start:json_end]
                parsed = json.loads(json_str)

                if "review" in parsed:
                    # If review says "No issues found", ensure verdict is "approved"
                    if "No issues found" in parsed.get("review", ""):
                        verdict = "approved"
                    else:
                        verdict = parsed.get("verdict", "flagged")
                        # Default to "flagged" for safety if unclear
                        if verdict not in ["approved", "flagged"]:
                            verdict = "flagged"

                    logger.info(f"Action review: {verdict}")
                    return {"review": parsed.get("review", ""), "verdict": verdict}
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"Failed to parse critic response as JSON: {e}")
            logger.debug(f"Raw response: {result[:300]}")

        # Fallback: default to flagged for safety
        logger.warning("Critic did not return valid JSON; defaulting to flagged for safety")
        return {
            "review": "Unable to parse review; flagged for manual approval.",
            "verdict": "flagged",
        }

    except Exception as e:
        logger.error(f"Critic error: {e}", exc_info=True)
        return {
            "review": "Review error; defaulting to flagged for safety.",
            "verdict": "flagged",
        }


def review_actions_batch(actions: list[dict], bedrock_client=None) -> list[dict]:
    """
    Review multiple proposed actions in batch.
    """
    reviews = []
    for action in actions:
        review = review_proposed_action(
            proposed_action=action,
            supporting_data={},
            bedrock_client=bedrock_client,
        )
        reviews.append({"action_id": action.get("action_id"), **review})
    return reviews
