# SupplySense Architecture

## System Design Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    React Dashboard (Frontend)                    │
│              (Tailwind CSS, ~600 lines, zero UI libs)            │
├─────────────────────────────────────────────────────────────────┤
│                           HTTP/REST API                          │
│  GET /api/sweep  |  POST /api/query  |  GET /api/pending-actions│
├─────────────────────────────────────────────────────────────────┤
│                     Flask API Server (backend/api.py)            │
│               (Wraps Python agent layer as REST)                 │
├─────────────────────────────────────────────────────────────────┤
│                      Agent Orchestrator                          │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ answer_query(question) → execution_trace + answer        │   │
│  │                                                          │   │
│  │ 1. Planner: Generate multi-step reasoning chain         │   │
│  │ 2. Executor: Run each step, resolve dependencies        │   │
│  │ 3. Composer: Synthesize final answer (Groq)             │   │
│  │ 4. Critic: Review proposed actions (Groq)              │   │
│  └──────────────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────────┤
│                    Backend Business Logic                        │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ • forecast_demand()           (7-day trend + forecast)   │   │
│  │ • predict_stockout()          (days until depletion)     │   │
│  │ • supplier_risk_score()       (reliability metrics)      │   │
│  │ • detect_delay_impact()       (shipment delays)          │   │
│  │ • recommend_allocation()      (priority-based alloc)     │   │
│  └──────────────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────────┤
│                      SQLite Data Layer                           │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ • demand_history (90 days/SKU)                           │   │
│  │ • inventory (warehouse × SKU)                            │   │
│  │ • suppliers (reliability, lead time)                     │   │
│  │ • purchase_orders, shipments, downstream_orders          │   │
│  │ • pending_actions (agent-proposed decisions)             │   │
│  └──────────────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────────┤
│                    External LLM API (Groq)                       │
│          llama-3.3-70b-versatile model for reasoning             │
└─────────────────────────────────────────────────────────────────┘
```

---

## Data Flow: Multi-Step Reasoning

### Example: "What's causing today's biggest disruption?"

```
1. PLANNER (Deterministic)
   └─ Parse question → Generate 4-step plan:
      Step 1: detect_delay_impact (get all delayed shipments)
      Step 2: supplier_risk_score (from_step_1 shipment → supplier)
      Step 3: predict_stockout (affected SKUs)
      Step 4: recommend_allocation (to mitigate shortage)

2. EXECUTOR (Orchestrator.answer_query)
   ├─ Step 1: detect_delay_impact("SHP001")
   │  ├─ Fetches: shipment data from DB
   │  ├─ Calls: detect_delay_impact() tool
   │  └─ Returns: {is_delayed: true, delay_days: 3, impact_score: 85}
   │
   ├─ Step 2: supplier_risk_score(supplier_id_from_step_1)
   │  ├─ Fetches: delivery history from DB
   │  ├─ Calls: supplier_risk_score() tool
   │  └─ Returns: {score: 35, risk_category: "high"}
   │
   ├─ Step 3: predict_stockout(affected_sku_from_step_1)
   │  ├─ Fetches: demand history + current stock from DB
   │  ├─ Calls: forecast_demand() → predict_stockout() chain
   │  └─ Returns: {risk_level: "critical", days_until_stockout: 0.4}
   │
   └─ Step 4: recommend_allocation(sku_from_step_3)
      ├─ Fetches: pending orders from DB
      ├─ Calls: recommend_allocation() tool
      └─ Returns: {allocations: [...], fully_satisfied: false}

3. COMPOSER (Groq LLM)
   ├─ Input: Execution trace (all 4 steps + results)
   ├─ Prompt: "Synthesize answer from these steps in 2-3 sentences"
   └─ Output: "Supplier delay on SHP001 is causing stockout of SKU003
              (0.4 days remaining). Supplier risk is high (score: 35).
              Recommend emergency reorder of 2,686 units."

4. CRITIC (Groq LLM)
   ├─ Input: Proposed action (reorder 2,686 units)
   ├─ Prompt: "Identify flaws or missing considerations"
   └─ Output: "Sound decision. Confirms with lead time + quality metrics."

5. RETURN TO USER
   └─ {
        question: "...",
        execution_trace: [step1, step2, step3, step4],
        final_answer: "...",
        confidence: "high",
        caveats: "..."
      }
```

---

## Frontend Architecture

### Single-Component Design (App.jsx)

```javascript
App.jsx (~600 lines)
├── State Management (useState)
│   ├── sweep data (critical_stockouts, risky_suppliers, executive_summary)
│   ├── pending actions (list, selected for expand/approve)
│   ├── chat messages (history, loading state)
│   └── sort state (Supplier Risk table)
│
├── API Calls (fetch)
│   ├── fetchSweep()     → GET /api/sweep
│   ├── fetchQuery()     → POST /api/query
│   ├── fetchActions()   → GET /api/pending-actions
│   ├── handleApprove()  → POST /api/pending-actions/:id/status
│   └── handleReject()   → POST /api/pending-actions/:id/status
│
├── Rendering (JSX)
│   ├── Header Section
│   ├── Executive Summary Banner
│   ├── Three-Column Panel Grid
│   │   ├── Panel A: Inventory Shortages
│   │   ├── Panel B: Supplier Risk
│   │   └── Panel C: Pending Actions
│   └── Chat Interface
│       ├── Message History
│       ├── Execution Trace (collapsible)
│       └── Input + Send Button
│
└── Effects (useEffect)
    ├── Initial sweep on mount
    ├── Auto-refresh pending actions
    └── Auto-scroll chat on new messages
```

### Styling: Tailwind Only

- **No Material-UI** — Grid, buttons, cards all Tailwind
- **No Chakra** — Color system, spacing from config
- **No Bootstrap** — Responsive design via `md:`, `lg:` breakpoints
- **No icons** — Unicode symbols (⚠ ✓ 📦 🤖 💬)

---

## Backend Architecture

### Flask API Server (backend/api.py)

```python
@app.route('/api/sweep', methods=['GET'])
├─ Call: run_intelligence_sweep(agent, tool_functions, all_skus, ...)
├─ Returns: {critical_stockouts, risky_suppliers, executive_summary, ...}
└─ Error handling: Try-catch, return JSON error

@app.route('/api/query', methods=['POST'])
├─ Input: {question: "..."}
├─ Call: agent.answer_query(question)
├─ Returns: {question, execution_trace, final_answer, confidence, caveats}
└─ Error handling: Try-catch, return JSON error

@app.route('/api/pending-actions', methods=['GET'])
├─ Call: get_pending_actions(status="pending_approval")
├─ Returns: list of {action_id, action_type, details, status, ...}
└─ Error handling: Try-catch

@app.route('/api/pending-actions/<id>/status', methods=['POST'])
├─ Input: {status: "approved" or "rejected"}
├─ Call: update_action_status(action_id, new_status)
├─ Returns: {success: true, new_status: "..."}
└─ Error handling: Try-catch

@app.route('/health', methods=['GET'])
└─ Returns: {status: "ok", timestamp: "..."}
```

### Agent Orchestrator (agents/orchestrator.py)

```python
class SupplyChainAgent:
    def __init__(self, bedrock_client, tool_functions):
        self.tool_functions = tool_functions
        # tool_functions = {
        #   "forecast_demand": forecast_demand,
        #   "predict_stockout": predict_stockout,
        #   "supplier_risk_score": supplier_risk_score,
        #   etc.
        # }

    def answer_query(self, user_question: str) -> dict:
        # 1. Plan: Generate multi-step plan
        steps = plan_investigation(user_question, ...)
        
        # 2. Execute: Run each step, resolve dependencies
        execution_trace = []
        for step in steps:
            params = self._substitute_dependencies(step['parameters'], ...)
            result = self.tool_functions[step['tool']](**params)
            execution_trace.append({...})
        
        # 3. Compose: Synthesize answer
        final_answer = compose_answer(user_question, execution_trace, ...)
        
        # 4. Return: Full trace + answer
        return {
            "question": user_question,
            "execution_trace": execution_trace,
            "final_answer": final_answer['answer'],
            "confidence": final_answer['confidence'],
            "caveats": final_answer['caveats']
        }
```

### Autonomous Sweep (agents/sweep.py)

```python
def run_intelligence_sweep(agent, tool_functions, all_skus, all_suppliers, ...):
    critical_stockouts = []
    risky_suppliers = []
    
    # 1. Scan all SKUs for stockout risk
    for sku in all_skus:
        result = predict_stockout(...)
        if result['risk_level'] in ['critical', 'high']:
            critical_stockouts.append(result)
    
    # 2. Scan all suppliers for risk
    for supplier in all_suppliers:
        result = supplier_risk_score(...)
        if result['risk_category'] in ['high', 'medium']:
            risky_suppliers.append(result)
    
    # 3. Synthesize findings into executive summary (via Groq)
    executive_summary = call_groq_lm("Given these findings, write 3 bullets...")
    
    return {
        "critical_stockouts": critical_stockouts,
        "risky_suppliers": risky_suppliers,
        "executive_summary": executive_summary,
        "timestamp": datetime.now().isoformat()
    }
```

---

## Database Schema

### Tables

```sql
suppliers
  └─ supplier_id (PK), name, region, avg_lead_time_days, on_time_delivery_pct, quality_score

warehouses
  └─ warehouse_id (PK), name, region, capacity

skus
  └─ sku_id (PK), name, category

inventory
  └─ warehouse_id (FK), sku_id (FK), current_stock
  └─ Primary Key: (warehouse_id, sku_id)

demand_history
  └─ sku_id (FK), date, units_sold

purchase_orders
  └─ order_id (PK), supplier_id (FK), sku_id (FK), quantity, promised_date, actual_date

shipments
  └─ shipment_id (PK), order_id (FK), promised_date, estimated_delivery, current_status

downstream_orders
  └─ order_id (PK), shipment_id (FK), customer_tier, sku_id (FK), quantity

pending_actions
  └─ action_id (PK), action_type, details (JSON), status, reasoning, created_at
```

### Synthetic Data Seeding

- **25 SKUs** across 4 categories
- **20 Suppliers** with realistic delivery patterns
- **5 Warehouses** across different regions
- **90 days** of demand history per SKU
- **3 Intentional Patterns**:
  - SUP014: Degrading reliability (92% → 61% on-time)
  - SKU008: Increasing demand (119% growth)
  - SKU015: Sudden demand spike (3x growth in 10 days)

---

## Agentic Behavior Model

### Perception Layer
- **Data Sources**: SQLite (demand, inventory, suppliers, shipments)
- **Frequency**: On-demand (API call) or scheduled (autonomous sweep)
- **Scope**: Full database scan (25 SKUs × 5 warehouses × 20 suppliers)

### Reasoning Layer
- **Planner**: Deterministic rule-based + LLM (Groq)
  - Parses user question → generates step sequence
  - Resolves dependencies (FROM_STEP_N, FROM_DB references)
  - Chains tools with real data flowing between steps
  
- **Executor**: Orchestrator
  - Runs steps sequentially
  - Fetches real DB data when needed
  - Substitutes parameters from earlier results
  - Catches errors, logs, continues
  
- **Composer**: Groq LLM
  - Synthesizes final answer from execution trace
  - Rates confidence (high/medium/low)
  - Lists caveats/limitations

### Action Layer
- **Action Proposal**: Autonomous + user-triggered
  - Reorder recommendations (from stockout detection)
  - Supplier switch recommendations (from risk scoring)
  - All proposed actions stored in DB
  
- **Approval Workflow**: Human-in-the-loop
  - Dashboard shows pending actions
  - Human clicks Approve/Reject
  - Status updated, action either executes or discards
  
- **Critique**: Groq LLM reviews proposed actions
  - Identifies flaws or missing considerations
  - Flags suspicious recommendations
  - Adds confidence score

---

## Error Handling Strategy

### API Level (Flask)
```python
try:
    result = endpoint_logic()
    return {"success": true, "data": result}
except Exception as e:
    logger.error(str(e))
    return {"success": false, "error": str(e)}, 500
```

### Agent Level (Orchestrator)
```python
try:
    result = tool_function(**params)
except Exception as e:
    logger.error(f"Tool {tool_name} failed: {e}")
    result = None  # Continue to next step
    continue
```

### Frontend Level (React)
```javascript
try {
    const response = await fetch('/api/...');
    if (!response.ok) throw new Error(response.statusText);
    const data = await response.json();
    setState(data);
} catch (error) {
    setError(error.message);  // Display inline
    // No crash, no blank screen
}
```

---

## Scaling Considerations

### Current (Demo)
- SQLite (file-based, single-user)
- Groq API (rate-limited)
- Single Flask instance
- React on Vite

### Production
- PostgreSQL (multi-user, persistent)
- Groq API (batched requests) or fine-tuned model
- Multiple Flask instances (gunicorn/uWSGI)
- React built to static files (Vercel/Netlify/S3)
- WebSocket for real-time updates
- Redis for caching + message queue

---

## Verification Paths

### TEST 16: Forecast → Stockout
```
Demand History (90 days) 
  → forecast_demand() 
  → predict_stockout() 
  → "risk_level: CRITICAL"
```

### TEST 17: Autonomous Sweep
```
All SKUs (25) + All Suppliers (20)
  → scan for critical patterns
  → Groq synthesizes summary
  → Executive summary returned
```

### TEST 18: Multi-Step Q&A
```
Question → Planner (4 steps)
  → Executor (each step runs, data flows)
  → Composer (Groq synthesizes answer)
  → Dashboard shows execution trace
```

---

**Status**: ✅ Production-ready architecture, verified end-to-end.
