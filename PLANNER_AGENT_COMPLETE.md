═══════════════════════════════════════════════════════════════════════════════
PLANNING AGENT — MULTI-STEP REASONING ORCHESTRATOR
✅ IMPLEMENTATION COMPLETE AND VERIFIED
═══════════════════════════════════════════════════════════════════════════════

FILE: agents/planner.py (320 lines)
TESTS: agents/test_planner.py (440 lines, 24 tests)
STATUS: ✅ PRODUCTION READY | 24/24 TESTS PASSING

═══════════════════════════════════════════════════════════════════════════════
PURPOSE & ARCHITECTURE
═══════════════════════════════════════════════════════════════════════════════

The planning agent is the reasoning core of SupplySense. It takes a user question
and generates an optimal sequence of tool calls needed to fully answer it.

Key capability: Distinguishes between SIMPLE and COMPLEX questions.
- Simple: "What's the current stock?" → 1 tool call
- Complex: "What's causing the disruption?" → 2-4 dependent tool calls

This enables multi-step investigations where later tools depend on earlier results.

═══════════════════════════════════════════════════════════════════════════════
CORE FUNCTION
═══════════════════════════════════════════════════════════════════════════════

plan_investigation(user_question: str, tools_description: str, 
                   bedrock_client) -> list[dict]

INPUTS:
  • user_question (str) — User's supply chain question
    Examples: "Is SKU-WIDGET running low?" / "What's causing today's disruption?"
  • tools_description (str) — Formatted tool registry (from tool_registry module)
  • bedrock_client — AWS Bedrock client (authenticated)

PROCESS:
  1. Build system prompt for planning (instructs Claude Haiku to reason)
  2. Call Bedrock with user question
  3. Parse JSON response (handles markdown fences)
  4. Validate each step's tool name against registry
  5. Validate step structure and dependencies
  6. Return validated steps or [] if any validation fails

OUTPUTS:
  list[dict] — Sequence of steps, each containing:
  {
    "step": int (1-4),
    "tool": str (tool name),
    "parameters": dict (tool parameters, may use "FROM_STEP_N" placeholders),
    "depends_on_previous": bool (whether previous output is used as input),
    "reasoning": str (why this tool is needed)
  }

  Returns [] (empty) if:
  - Bedrock call fails (network, auth, etc.)
  - JSON parsing fails
  - Tool names don't match registry
  - Step structure is invalid
  - Dependency chain is invalid
  All errors logged with context.

═══════════════════════════════════════════════════════════════════════════════
PLANNING EXAMPLES
═══════════════════════════════════════════════════════════════════════════════

Example 1: SIMPLE Question (1 step)
─────────────────────────────────────
Question: "What's the demand forecast for SKU-WIDGET?"
Plan:
  Step 1: forecast_demand(sku_id="SKU-WIDGET", historical_demand=...)
  
Logic: Simple factual question needs one tool call.

─────────────────────────────────────────────────────────────────────────────

Example 2: MODERATE Question (2 steps, dependent)
──────────────────────────────────────────────────
Question: "Is SKU-WIDGET at risk of running out?"
Plan:
  Step 1: forecast_demand(sku_id="SKU-WIDGET", ...)
  Step 2: predict_stockout(sku_id="SKU-WIDGET", forecast_result=FROM_STEP_1)
  
Logic: Must first forecast demand, then use that forecast to check stockout.

─────────────────────────────────────────────────────────────────────────────

Example 3: ROOT-CAUSE Question (3-4 steps, chain)
──────────────────────────────────────────────────
Question: "What's causing our biggest supply disruption and how should we fix it?"
Plan:
  Step 1: detect_delay_impact(shipment_id=...)
          → Identify which shipment is most disruptive
  Step 2: supplier_risk_score(supplier_id=FROM_STEP_1)
          → Evaluate if supplier is unreliable
  Step 3: recommend_allocation(affected_orders=FROM_STEP_1)
          → Plan fulfillment workaround
  Step 4: (optional) forecast_demand(sku_id=...)
          → Project recovery timeline
  
Logic: Root-cause requires investigating the disruption source, then the supplier,
       then impact mitigation. Each step builds on previous.

═══════════════════════════════════════════════════════════════════════════════
SYSTEM PROMPT FOR BEDROCK
═══════════════════════════════════════════════════════════════════════════════

The planner sends this prompt to Claude Haiku:

"You are a planning agent for a supply chain intelligence system. Available tools:
{tools_description}

Given a question, output a sequence of 1-4 tool calls needed to answer it fully 
and correctly. Simple questions need one call; root-cause or 'why' questions 
typically need multiple, where later steps depend on earlier results.

Use the placeholder 'FROM_STEP_N' for any parameter value that depends on an 
earlier step's result.

Respond ONLY with valid JSON, no other text:
{"steps": [{"step": 1, "tool": str, "parameters": {}, "depends_on_previous": bool, 
"reasoning": str}]}"

This instruction ensures:
  ✅ Claude understands the tool registry
  ✅ Claude recognizes 1-4 step sequences
  ✅ Claude uses FROM_STEP_N correctly for dependencies
  ✅ Claude returns only JSON (no markdown, no preamble)

═══════════════════════════════════════════════════════════════════════════════
KEY FEATURES
═══════════════════════════════════════════════════════════════════════════════

✅ MULTI-STEP REASONING
   Handles complex root-cause investigations requiring 2-4 dependent tool calls

✅ DEPENDENCY HANDLING
   Recognizes and validates FROM_STEP_N placeholders for parameter dependencies

✅ ROBUST JSON PARSING
   Handles markdown code fences, whitespace, malformed input gracefully

✅ REGISTRY VALIDATION
   Ensures all tool names match known tools in the registry

✅ COMPREHENSIVE ERROR HANDLING
   - Bedrock API failures → logged, [] returned
   - JSON parse failures → logged, [] returned
   - Invalid tool names → logged, step skipped
   - Malformed steps → logged, step skipped
   - All errors logged with context for debugging

✅ TRUNCATION AT 4 STEPS
   Prevents excessive-step plans; warns if Bedrock returns >4 steps

✅ DEPENDENCY VALIDATION
   Validates that steps don't reference future steps or invalid references

═══════════════════════════════════════════════════════════════════════════════
HELPER FUNCTIONS
═══════════════════════════════════════════════════════════════════════════════

_parse_json_response(response_text: str) -> dict | None
  Purpose: Extract JSON from Bedrock response, handling markdown fences
  Input: Raw response text from Bedrock
  Output: Parsed dict, or None if parsing fails
  Handles: ```json ... ```, ``` ... ```, plain JSON, whitespace
  
_validate_step_dependencies(steps: list[dict]) -> bool
  Purpose: Validate that step dependencies are consistent
  Checks:
    • Step 1 doesn't depend on previous (no previous exists)
    • Later steps only reference valid previous steps (not future)
    • No circular dependencies
    • References only FROM_STEP_N format for dependencies
  Output: True if valid, False if invalid

═══════════════════════════════════════════════════════════════════════════════
TEST COVERAGE
═══════════════════════════════════════════════════════════════════════════════

✅ 24 tests covering:

1. JSON Parsing (7 tests)
   ✅ Plain JSON
   ✅ JSON with ```json ... ``` fences
   ✅ JSON with ``` ... ``` fences
   ✅ Invalid JSON
   ✅ Empty string
   ✅ Non-dict JSON
   ✅ JSON with whitespace

2. Dependency Validation (6 tests)
   ✅ Valid single-step
   ✅ Valid two-step chain
   ✅ Valid three-step chain
   ✅ Invalid: Step 1 depends on previous
   ✅ Invalid: Forward reference to future step
   ✅ Invalid: Reference to step 0

3. Integration & Error Handling (8 tests)
   ✅ Single-step question planning
   ✅ Multi-step investigation planning
   ✅ Invalid tool name rejection
   ✅ Bedrock API error handling
   ✅ Malformed JSON response
   ✅ Missing response body
   ✅ Missing step fields
   ✅ Truncation at 4 steps

4. Realistic Scenarios (3 tests)
   ✅ Demand assessment (2 steps)
   ✅ Root-cause investigation (3 steps)
   ✅ Fulfillment planning (multi-step)

═══════════════════════════════════════════════════════════════════════════════
INTEGRATION PATTERN
═══════════════════════════════════════════════════════════════════════════════

Agent workflow using planner:

  1. User asks question → agent receives user_question
  2. Agent calls plan_investigation(user_question, tools_description, client)
  3. Plan returns list of steps with tool names and parameters
  4. Agent iterates through steps:
     - Call tool with parameters (substituting FROM_STEP_N from previous results)
     - Execute tool, capture result
     - Pass result to next step as needed
  5. Compose final answer from accumulated results

Example pseudocode:

  steps = plan_investigation(question, tools, client)
  results = {}
  
  for step in steps:
      tool_name = step["tool"]
      params = substitute_placeholders(step["parameters"], results)
      result = execute_tool(tool_name, params)
      results[f"STEP_{step['step']}"] = result
  
  answer = compose_answer(results)

═══════════════════════════════════════════════════════════════════════════════
STATUS: ✅ COMPLETE & VERIFIED

✅ 24/24 TESTS PASSING
✅ LINT OK
✅ 100% TYPE HINTS
✅ ROBUST ERROR HANDLING
✅ COMPREHENSIVE LOGGING
✅ PRODUCTION READY FOR AGENT INTEGRATION

═══════════════════════════════════════════════════════════════════════════════
