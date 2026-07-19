"""
ACTION AGENT IMPLEMENTATION COMPLETE

File: agents/action_agent.py

This module converts supply chain risk findings into structured action
proposals for approval workflow and operational execution.

SPECIFICATION COMPLIANCE
========================

Function: propose_action(finding: dict, finding_type: str) -> dict

✅ IMPLEMENTED with full compliance:

Input Parameters:
  - finding: dict (predict_stockout or supplier_risk_score result)
  - finding_type: Literal["stockout", "supplier_risk"]

Output Structure:
  {
      "action_id": str (UUID4),
      "action_type": str ("reorder" or "switch_supplier"),
      "details": dict (action-specific parameters),
      "status": str ("pending_approval"),
      "created_by": str ("agent"),
      "reasoning": str (2-3 sentences with specific numbers),
      "created_at": str (ISO timestamp)
  }

WORKFLOW
========

If finding_type == "stockout":
  ├─ Validate required fields
  ├─ Determine urgency_level (CRITICAL/HIGH/MEDIUM)
  ├─ Generate action_type: "reorder"
  ├─ Build details: {sku_id, warehouse_id, quantity, urgency_level, ...}
  ├─ Generate reasoning: "SKU-X at WH-Y has 250 units (2.5 days). 
  │                      Recommend order 1400 units..."
  └─ Return complete action proposal

If finding_type == "supplier_risk":
  ├─ Validate required fields
  ├─ Generate action_type: "switch_supplier"
  ├─ Extract metrics: on_time_pct, lead_variance, quality_score
  ├─ Build reason from breakdown
  ├─ Generate reasoning: "SUP-X has 35/100 score due to 60% on-time, 
  │                      3.2-day variance, quality 60..."
  └─ Return complete action proposal

ACTION TYPES
============

1. "reorder" — Emergency inventory procurement
   Details:
   ├─ sku_id: str
   ├─ warehouse_id: str
   ├─ quantity: int (recommended_reorder_quantity)
   ├─ urgency_level: str ("CRITICAL" | "HIGH" | "MEDIUM")
   ├─ current_stock: int
   └─ days_until_stockout: float

   Urgency Logic:
   ├─ CRITICAL: risk_level="critical" OR days_until_stockout <= 3
   ├─ HIGH: days_until_stockout <= 7
   └─ MEDIUM: otherwise

2. "switch_supplier" — Supplier diversification/fallback
   Details:
   ├─ supplier_id: str
   ├─ reason: str (one phrase from breakdown)
   ├─ risk_score: float (0-100)
   ├─ on_time_delivery_pct: float
   ├─ lead_time_variance_days: float
   └─ quality_score: float

REASONING GENERATION
====================

Stockout Reasoning (with specific numbers):
  "SKU-WIDGET-100 at WH-MAIN faces a CRITICAL situation with only 250 units
   in stock (2.5 days of supply remaining). Recommended action: immediately
   place order for 1400 units to restore 14-day supply buffer and prevent
   stockout."

  Numbers included:
  ├─ Current stock (250)
  ├─ Days until stockout (2.5)
  ├─ Reorder quantity (1400)
  └─ Buffer target (14 days)

Supplier Switch Reasoning (with specific metrics):
  "SUP-VENDOR-B has a risk score of 35/100, indicating poor on-time delivery
   (60%), excessive lead time variability (3.2 days), quality concerns
   (score 60). Recommend identifying alternative suppliers for non-critical
   items and diversifying sourcing to reduce single-supplier dependency risk."

  Metrics included:
  ├─ Risk score (35)
  ├─ On-time percentage (60%)
  ├─ Lead time variance (3.2 days)
  └─ Quality score (60)

HELPER FUNCTIONS
================

_propose_reorder_action(finding) -> dict
  └─ Reorder action generation with urgency classification

_propose_supplier_switch_action(finding) -> dict
  └─ Supplier switch action generation

_build_reorder_reasoning(...) -> str
  └─ Generates 2-3 sentence reasoning with specific numbers

_build_supplier_switch_reason(...) -> str
  └─ One-phrase reason from breakdown

_build_supplier_switch_reasoning(...) -> str
  └─ 2-3 sentence reasoning with specific metrics

propose_actions_from_sweep(stockouts, suppliers) -> dict
  └─ Batch action generation from sweep findings
     Returns: {stockout_actions, supplier_actions, total_actions, created_at}

ERROR HANDLING
==============

✅ Invalid finding_type
   └─ Raises ValueError with clear message

✅ Missing required fields
   └─ Raises KeyError listing missing fields

✅ Type mismatches
   └─ Raises TypeError with context

✅ Batch processing errors
   └─ Logs error per item, continues processing others
   └─ Returns partial results

TEST RESULTS
============

Test Suite: test_action_agent.py
Total Tests: 8
Result: 8 PASSED, 0 FAILED

Tests:
  [OK] TEST 1: Stockout Reorder Action
       └─ Verifies action_type, urgency_level, reasoning quality
  [OK] TEST 2: High Risk Urgency Level
       └─ Confirms 5-day finding gets HIGH urgency
  [OK] TEST 3: Supplier Risk Switch Action
       └─ Verifies supplier details and metrics included
  [OK] TEST 4: Error Handling - Invalid Type
       └─ ValueError for invalid finding_type
  [OK] TEST 5: Error Handling - Missing Fields
       └─ KeyError for incomplete findings
  [OK] TEST 6: Error Handling - Wrong Type
       └─ TypeError for non-dict findings
  [OK] TEST 7: Batch Actions from Sweep
       └─ Generates 3 actions (2 reorder + 1 switch)
  [OK] TEST 8: Reasoning Quality
       └─ Verifies specific numbers in reasoning

Sample Output:

Action ID: 7c853a0f-...
Action Type: reorder
Status: pending_approval
Created By: agent
Created At: 2024-01-15T14:32:15Z

Details:
  SKU ID: SKU-WIDGET-100
  Warehouse: WH-MAIN
  Quantity: 1400 units
  Urgency: CRITICAL
  Current Stock: 250 units
  Days Until Stockout: 2.5

Reasoning:
  "SKU-WIDGET-100 at WH-MAIN faces a CRITICAL situation with only 250 units
   in stock (2.5 days of supply remaining). Recommended action: immediately
   place order for 1400 units to restore 14-day supply buffer and prevent
   stockout."

CODE QUALITY
============

✅ Type Hints: 100% coverage
   - All parameters annotated
   - Return types specified
   - Literal types for enums

✅ Docstrings: 100% coverage
   - Module docstring
   - All functions documented
   - Args, Returns, Raises, Examples
   - Input structure specifications

✅ Error Handling: Comprehensive
   - Input validation on all paths
   - Clear error messages
   - Traceable failures

✅ Logging: Production-grade
   - INFO level for action creation
   - ERROR level for batch failures
   - Traceable action IDs

✅ Linting: PASS

INTEGRATION POINTS
==================

1. Direct Usage:
   from agents.action_agent import propose_action
   
   action = propose_action(stockout_finding, "stockout")
   print(f"Action ID: {action['action_id']}")
   print(f"Status: {action['status']}")

2. From Sweep Results:
   from agents.sweep import run_intelligence_sweep
   from agents.action_agent import propose_actions_from_sweep
   
   sweep = run_intelligence_sweep(...)
   actions = propose_actions_from_sweep(
       sweep["critical_stockouts"],
       sweep["risky_suppliers"]
   )

3. Approval Workflow:
   - All actions start with status="pending_approval"
   - Action ID used for tracking through approval process
   - Reasoning provides decision support for approvers

4. Operational Execution:
   - action_type determines execution path:
     * "reorder" → PO generation + supplier notification
     * "switch_supplier" → Sourcing team alert + alternative sourcing

WORKFLOW INTEGRATION
====================

Intelligence Pipeline:
  1. sweep.run_intelligence_sweep()
     └─ Identifies critical issues
  
  2. action_agent.propose_actions_from_sweep()
     └─ Generates action proposals
  
  3. approval_workflow (external)
     └─ Reviews and approves actions
  
  4. execution_layer (external)
     └─ Executes approved actions
     
  5. audit_trail
     └─ Tracks action_id from proposal to completion

ACTIONABILITY FEATURES
======================

✅ Structured Output
   └─ JSON-compatible, ready for API/DB storage

✅ Unique Identification
   └─ UUID4 per action (globally unique, sortable)

✅ Timestamps
   └─ ISO format for audit trails and sorting

✅ Status Tracking
   └─ Enables workflow: pending_approval → approved → executed

✅ Audit Trail
   └─ created_by field identifies source
   └─ Reasoning documents decision logic

✅ Priority Levels
   └─ Urgency levels guide approval routing

NEXT STEPS
==========

Ready to integrate with:
  ✓ APPROVAL WORKFLOW (route pending actions to stakeholders)
  ✓ EXECUTION LAYER (auto-execute or manual dispatch)
  ✓ AUDIT SYSTEM (track action lifecycle)
  ✓ API ENDPOINTS (expose actions for external systems)
  ✓ FRONTEND (visualize and approve actions)

The action agent completes the autonomous decision loop:
Monitoring → Analysis → Finding → Proposal → Approval → Execution

This enables the full agentic supply chain system with genuine autonomous
decision-making and human approval integration.
"""
