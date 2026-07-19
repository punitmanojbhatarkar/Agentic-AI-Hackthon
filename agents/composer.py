"""
Answer composer for supply chain intelligence.

Synthesizes multi-step execution results into natural language answers with
confidence scoring and caveat identification.

Uses Groq's llama-3.3-70b-versatile model for intelligent synthesis.
"""

import json
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def compose_answer(
    user_question: str,
    execution_trace: list[dict],
    bedrock_client=None,
) -> dict:
    """
    Synthesize multi-step execution results into a natural language answer.

    Uses Groq (via llama-3.3-70b) to synthesize raw tool results into coherent,
    business-focused answers with confidence ratings and caveats.

    Args:
        user_question: Original user question (str).
        execution_trace: List of executed steps with results (list[dict]).
        bedrock_client: (Ignored - uses Groq instead).

    Returns:
        dict with keys:
            - "answer": str (summary with specific numbers)
            - "confidence": "high" | "medium" | "low"
            - "caveats": str (limitations/assumptions)
    """
    from agents.groq_provider import call_groq

    try:
        # Format execution trace for the LLM
        trace_summary = json.dumps(execution_trace, indent=2, default=str)

        logger.info("Composing answer from execution trace")

        system_prompt = """You are a supply chain analyst synthesizing data from tool executions.

Given the user's question and the data gathered, synthesize a clear, specific answer in 2-3 sentences using exact numbers from the data.

Then rate your confidence in this answer as 'high', 'medium', or 'low' based on data completeness and consistency.

List any caveats or limitations in one short phrase (e.g., "based on last 90 days only" or "excludes rush orders").

Respond ONLY with valid JSON, no markdown or other text:
{"answer": "...", "confidence": "high|medium|low", "caveats": "..."}"""

        user_message = f"""User's original question: {user_question}

Data gathered from tool execution:
{trace_summary}"""

        result = call_groq(
            system_prompt=system_prompt,
            user_message=user_message,
            max_tokens=1000,
            temperature=0.5,
        )

        logger.debug(f"Composer Groq response: {result[:300]}")

        # Try to extract JSON from response
        try:
            if "{" in result:
                json_start = result.index("{")
                json_end = result.rfind("}") + 1
                json_str = result[json_start:json_end]
                parsed = json.loads(json_str)

                if "answer" in parsed and "confidence" in parsed:
                    confidence = parsed.get("confidence", "medium")
                    if confidence not in ["high", "medium", "low"]:
                        confidence = "medium"

                    logger.info(f"Answer composed with confidence: {confidence}")
                    return {
                        "answer": parsed.get("answer", ""),
                        "confidence": confidence,
                        "caveats": parsed.get("caveats", ""),
                    }
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"Failed to parse composer response as JSON: {e}")
            logger.debug(f"Raw response: {result[:300]}")

        # Fallback if JSON parsing fails
        logger.warning("Composer did not return valid JSON; using fallback")
        return _get_fallback_answer(execution_trace)

    except Exception as e:
        logger.error(f"Composer error: {e}", exc_info=True)
        return _get_fallback_answer(execution_trace)


def _get_fallback_answer(execution_trace: list[dict]) -> dict:
    """
    Generate a fallback answer when Groq call fails.
    """
    try:
        summary_parts = []
        for step in execution_trace:
            if "result" in step and step["result"]:
                result = step["result"]
                if isinstance(result, dict):
                    if "risk_level" in result:
                        summary_parts.append(f"{step.get('tool')} shows {result['risk_level']} risk")
                    if "days_until_stockout" in result:
                        summary_parts.append(f"{result['days_until_stockout']:.1f} days until stockout")

        answer = "Analysis: " + "; ".join(summary_parts) if summary_parts else "Analysis executed; review trace for details."

        return {
            "answer": answer,
            "confidence": "medium",
            "caveats": "Fallback answer due to API error; may lack specificity",
        }
    except Exception as e:
        logger.error(f"Fallback failed: {e}")
        return {
            "answer": "Supply chain analysis executed; see execution trace for details.",
            "confidence": "low",
            "caveats": "Unable to synthesize answer automatically",
        }
