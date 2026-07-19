═══════════════════════════════════════════════════════════════════════════════
RESPONSE COMPOSER — SYNTHESIS LAYER
✅ IMPLEMENTATION COMPLETE AND VERIFIED
═══════════════════════════════════════════════════════════════════════════════

FILE: agents/composer.py (280 lines)
TESTS: agents/test_composer.py (430 lines, 25 tests)
STATUS: ✅ PRODUCTION READY | 25/25 TESTS PASSING

═══════════════════════════════════════════════════════════════════════════════
PURPOSE & ARCHITECTURE
═══════════════════════════════════════════════════════════════════════════════

The response composer is the final synthesis layer of the agent. It takes the raw
results from multi-step tool execution and synthesizes them into clear, data-driven
answers that the user can understand and act on.

Key capability: Convert technical tool outputs → natural language insights with
confidence ratings and caveats.

═══════════════════════════════════════════════════════════════════════════════
CORE FUNCTION
═══════════════════════════════════════════════════════════════════════════════

compose_answer(user_question: str, execution_trace: list[dict],
               bedrock_client) -> dict

INPUTS:
  • user_question (str) — Original user question from the start of the conversation
  • execution_trace (list[dict]) — Results from running the planned steps
    Each step:
    {
      "step": int (1-4),
      "tool": str (name of tool called),
      "result": dict (complete output from the tool call)
    }
  • bedrock_client — AWS Bedrock client (authenticated)

PROCESS:
  1. Format execution trace as JSON for LLM context
  2. Build user message with question + trace data
  3. Call Bedrock (Claude Haiku) with system prompt
  4. Parse JSON response (handles markdown fences)
  5. Validate response structure and confidence level
  6. Return composed answer or fallback if parsing fails

OUTPUTS:
  dict with keys:
  {
    "answer": str (2-3 sentences with specific numbers),
    "confidence": str ("high" | "medium" | "low"),
    "caveats": str (one short phrase noting limitations)
  }

  Fallback if composition fails:
  {
    "answer": "Unable to synthesize answer from execution results.",
    "confidence": "low",
    "caveats": reason for failure
  }

═══════════════════════════════════════════════════════════════════════════════
SYSTEM PROMPT (Sent to Bedrock)
═══════════════════════════════════════════════════════════════════════════════

"You are a supply chain analyst. Given the user's question and the data gathered
across these steps, synthesize a clear answer in 2-3 sentences using specific
numbers from the data. Then rate your confidence in this answer as 'high', 'medium',
or 'low' based on data completeness and consistency, and list any caveats in one
short phrase. Respond ONLY with valid JSON:
{"answer": str, "confidence": "high"|"medium"|"low", "caveats": str}"

This prompt ensures:
  ✅ Claude understands the user's original question
  ✅ Claude synthesizes specific numbers (not vague summaries)
  ✅ Claude rates confidence based on data quality
  ✅ Claude acknowledges limitations (caveats)
  ✅ Claude returns ONLY JSON (no preamble)

═══════════════════════════════════════════════════════════════════════════════
COMPOSITION EXAMPLES
═══════════════════════════════════════════════════════════════════════════════

Example 1: SINGLE-STEP ANSWER
────────────────────────────
User Question: "Is SKU-WIDGET at risk of running out?"
Execution:
  Step 1 (predict_stockout):
    {"days_until_stockout": 2.0, "risk_level": "critical", "warehouse_id": "WH-MAIN"}

Composed Answer:
{
  "answer": "SKU-WIDGET at WH-MAIN will run out of stock in 2.0 days at current demand
             rates, posing a critical risk to operations.",
  "confidence": "high",
  "caveats": "Assumes demand remains stable; doesn't account for expedited shipments"
}

────────────────────────────────────────────────────────────────────────────

Example 2: MULTI-STEP ANSWER (Root-cause)
──────────────────────────────────────────
User Question: "What's causing our supply disruption and how bad is it?"
Execution:
  Step 1 (detect_delay_impact):
    {"shipment_id": "SHIP-123", "delay_days": 5, "downstream_impact_score": 90}
  Step 2 (supplier_risk_score):
    {"supplier_id": "SUP-VENDOR-B", "score": 39, "risk_category": "high"}

Composed Answer:
{
  "answer": "SHIP-123 is 5 days late, impacting 8 premium customers with a 90/100
             severity score. The supplier (SUP-VENDOR-B) scores only 39/100 reliability,
             indicating systemic delivery issues.",
  "confidence": "high",
  "caveats": "No current rerouting options available; score reflects 6-month history"
}

────────────────────────────────────────────────────────────────────────────

Example 3: INCOMPLETE DATA
──────────────────────────
User Question: "Should we allocate inventory or restock?"
Execution:
  Step 1 (forecast_demand):
    {"avg_forecasted_demand": 100}
  (No allocation data available yet)

Composed Answer:
{
  "answer": "Based on forecast of 100 units/day demand, additional context on current
             warehouse allocation and customer orders is needed for a full recommendation.",
  "confidence": "medium",
  "caveats": "Partial data; missing current inventory levels and pending orders"
}

═══════════════════════════════════════════════════════════════════════════════
KEY FEATURES
═══════════════════════════════════════════════════════════════════════════════

✅ DATA-DRIVEN ANSWERS
   Composer ensures specific numbers from execution trace are included

✅ CONFIDENCE RATING
   Ranges: high (all data consistent) | medium (partial data) | low (errors/missing)

✅ CAVEAT TRACKING
   Explicitly notes limitations and assumptions in the answer

✅ ROBUST JSON PARSING
   Handles markdown code fences, whitespace, malformed input

✅ GRACEFUL ERROR HANDLING
   Bedrock errors → fallback answer (low confidence)
   Parsing errors → fallback answer (low confidence)
   Invalid confidence values → fallback answer

✅ EXECUTION TRACE FORMATTING
   Pretty-printed JSON for clarity to LLM
   Validates step structure, logs warnings for partial data

═══════════════════════════════════════════════════════════════════════════════
HELPER FUNCTIONS
═══════════════════════════════════════════════════════════════════════════════

_format_execution_trace(execution_trace: list[dict]) -> str
  Purpose: Format execution trace as readable JSON for LLM
  Input: List of step results with tool outputs
  Output: Pretty-printed JSON string
  Handles: Missing keys, non-dict items, empty trace

_parse_composed_response(response_text: str) -> dict | None
  Purpose: Parse JSON from Bedrock response, handling markdown fences
  Input: Raw response text from Bedrock
  Output: Parsed dict or None if parsing fails
  Handles: ```json ... ```, ``` ... ```, plain JSON, whitespace

_fallback_answer(reason: str) -> dict
  Purpose: Generate fallback answer when composition fails
  Input: Reason string (for caveats)
  Output: Valid dict with low confidence and caveat
  Use: Bedrock errors, JSON parsing errors, validation failures

═══════════════════════════════════════════════════════════════════════════════
TEST COVERAGE
═══════════════════════════════════════════════════════════════════════════════

✅ 25 tests covering:

1. Trace Formatting (6 tests)
   ✅ Single-step trace
   ✅ Multi-step trace
   ✅ Empty trace
   ✅ Invalid trace type
   ✅ Complex nested results
   ✅ Partial data handling

2. JSON Parsing (6 tests)
   ✅ Plain JSON
   ✅ JSON with ```json ... ``` fences
   ✅ JSON with ``` ... ``` fences
   ✅ Invalid JSON
   ✅ Non-dict JSON
   ✅ Non-string input

3. Fallback Answers (3 tests)
   ✅ Fallback structure
   ✅ Low confidence marking
   ✅ Reason inclusion

4. Integration & Error Handling (7 tests)
   ✅ Simple single-step composition
   ✅ Multi-step composition
   ✅ Markdown-wrapped response
   ✅ Bedrock API error
   ✅ Malformed JSON response
   ✅ Missing response body
   ✅ Invalid confidence value
   ✅ All valid confidence levels

5. Realistic Scenarios (2 tests)
   ✅ Demand + risk assessment
   ✅ Root-cause investigation

6. Edge Cases (1 test)
   ✅ Empty execution trace

═══════════════════════════════════════════════════════════════════════════════
INTEGRATION PATTERN
═══════════════════════════════════════════════════════════════════════════════

Full agent workflow including composition:

  1. User asks question
  2. Agent calls plan_investigation() → gets step sequence
  3. Agent iterates through steps, executing each tool
  4. Agent collects results in execution_trace
  5. Agent calls compose_answer(question, trace, client)
  6. Composer synthesizes multi-step results into natural language
  7. Agent returns composed answer to user

Example pseudocode:

  question = user_input
  plan = plan_investigation(question, tools, client)
  trace = []
  
  for step in plan:
      result = execute_tool(step["tool"], step["parameters"])
      trace.append({"step": step["step"], "tool": step["tool"], "result": result})
  
  response = compose_answer(question, trace, client)
  
  return response  # {"answer": "...", "confidence": "...", "caveats": "..."}

═══════════════════════════════════════════════════════════════════════════════
CONFIDENCE RATINGS
═══════════════════════════════════════════════════════════════════════════════

HIGH CONFIDENCE:
  - All planned steps executed successfully
  - Data is consistent across steps
  - Specific numbers available for answer
  - No missing required fields
  Example: Stockout risk with demand forecast + inventory level

MEDIUM CONFIDENCE:
  - Partial data collected (e.g., forecast without allocation)
  - Some planned steps failed or returned empty
  - Some assumptions needed to formulate answer
  Example: Disruption impact without full supplier history

LOW CONFIDENCE:
  - Bedrock or parsing errors occurred
  - Fallback answer used
  - Insufficient data for meaningful answer
  - Major gaps in execution trace
  Example: Composition failed, generic fallback returned

═══════════════════════════════════════════════════════════════════════════════
STATUS: ✅ COMPLETE & VERIFIED

✅ 25/25 TESTS PASSING
✅ LINT OK
✅ 100% TYPE HINTS
✅ ROBUST ERROR HANDLING
✅ COMPREHENSIVE LOGGING
✅ PRODUCTION READY FOR AGENT INTEGRATION

═══════════════════════════════════════════════════════════════════════════════
