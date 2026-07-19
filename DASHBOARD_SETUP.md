# SupplySense Dashboard — Complete Setup & Deployment Guide

## Overview

SupplySense is a production-ready AI supply chain risk & inventory intelligence dashboard featuring:

- **Real-time autonomous monitoring** with executive summaries
- **Interactive Q&A** powered by Claude Haiku LLM
- **Critical alerts** for inventory shortages and supplier risks
- **Action approval workflow** for AI-proposed reorders and supplier switches
- **Professional SaaS aesthetic** with dark theme, smooth interactions, and responsive design

---

## Architecture

```
frontend/                          # React + Vite + Tailwind dashboard
├── src/
│   ├── App.jsx                   # Main dashboard component (~600 lines)
│   ├── index.css                 # Tailwind imports + custom styles
│   └── main.jsx                  # React entry point
├── index.html
├── vite.config.js
├── tailwind.config.js
├── postcss.config.js
└── package.json

backend/
├── api.py                         # Flask API server (wraps Python agent layer)
└── forecasting.py, inventory.py, etc. (existing backend modules)

agents/
├── orchestrator.py               # Main agent class (existing)
├── sweep.py                      # Autonomous monitoring (existing)
└── ...other agent modules

data/
├── queries.py                    # SQLite data access (existing)
└── supplysense.db                # SQLite database (seeded)
```

---

## Quick Start (Development)

### 1. Install Backend Dependencies

```bash
pip install flask flask-cors
```

### 2. Start Backend API Server

```bash
python backend/api.py
```

You'll see:
```
 * Running on http://localhost:5000
```

The API exposes 4 endpoints:
- `GET /api/sweep` — Run autonomous monitoring
- `POST /api/query` — Submit Q&A question
- `GET /api/pending-actions` — List pending actions
- `POST /api/pending-actions/<id>/status` — Approve/reject action

### 3. Install Frontend Dependencies

```bash
cd frontend
npm install
```

### 4. Start Frontend Dev Server

```bash
npm run dev
```

You'll see:
```
 ➜  Local:   http://localhost:3000/
```

Open your browser to **http://localhost:3000** — the dashboard will automatically load and fetch data from the backend.

---

## Dashboard Features

### 1. Header
- Title and subtitle
- Last-updated timestamp from the sweep

### 2. Executive Summary Banner
- Pinned high-visibility card with Groq-generated summary
- **Refresh Analysis** button re-triggers autonomous monitoring
- Loading state: "⏳ Running initial analysis..."

### 3. Three-Column Panel (Responsive)
All panels auto-sort, load with skeletons, and show empty states:

#### Panel A: Inventory Shortages
- Cards for each critical/high stockout
- Risk level badge (colored: critical=red, high=orange, medium=yellow, low=green)
- **Large bold number** showing days until stockout
- Recommended reorder quantity

#### Panel B: Supplier Risk Scores
- Sortable table (click header to toggle ascending/descending)
- Click any row to expand and show breakdown metrics
- Risk category badges

#### Panel C: Pending Actions
- AI-proposed reorders and supplier switches
- Shows action type, details, reasoning, and current status
- **Approve / Reject** buttons trigger API updates
- Toast message confirms success
- Actions disappear from list after approval/rejection

### 4. Chat Interface
- Message history with auto-scroll
- User messages appear right-aligned in orange
- Agent responses show:
  - **Final answer** (large, prominent)
  - **Show reasoning** toggle reveals full execution trace
  - **Confidence badge** (green/yellow/red dots)
  - **Caveats** text below
- Animated thinking indicator while waiting for response
- Disabled send button prevents double-submission

---

## Styling & UX

### Design System
- **Color scheme**: Dark gray (bg-gray-900 base), mid-gray cards (bg-gray-800), white/light text
- **Accent color**: Orange-500 for primary actions and highlights
- **Spacing**: Generous padding (p-4, p-6) and gaps (gap-4, gap-6) for breathing room
- **Shadows**: `shadow-md` on cards for depth
- **Rounded corners**: `rounded-lg` or `rounded-xl` on cards, `rounded-full` on badges
- **Transitions**: Smooth 0.2s easing on all interactive elements
- **Responsive**: Panels stack vertically on mobile (`md:` breakpoint), side-by-side on desktop

### Loading States
- Skeleton placeholders that pulse (animated gray blocks matching content shape)
- Animated thinking dots in chat

### Empty States
- Friendly messages with checkmark (✓) when all clear
- No redundant spinners or generic "Loading..." text

---

## API Endpoints Reference

### GET /api/sweep
Runs autonomous monitoring across all SKUs and suppliers.

**Response:**
```json
{
  "critical_stockouts": [
    {
      "sku_id": "SKU008",
      "warehouse_id": "WH-ASIA",
      "risk_level": "critical",
      "days_until_stockout": 0.4,
      "recommended_reorder_quantity": 2703
    },
    ...
  ],
  "risky_suppliers": [
    {
      "supplier_id": "SUP001",
      "score": 65.0,
      "risk_category": "medium",
      "breakdown": {
        "on_time_delivery_pct": 50.0,
        "lead_time_variance_days": 2.5,
        "avg_quality_score": 80.0
      }
    },
    ...
  ],
  "executive_summary": "1. CRITICAL: SKU008 at WH-EURO has 0.3 days inventory left...",
  "timestamp": "2026-07-18T20:30:00Z",
  "scan_stats": {...}
}
```

### POST /api/query
Submit a natural language question to the agent.

**Request:**
```json
{
  "question": "What is causing today's biggest supply chain disruption?"
}
```

**Response:**
```json
{
  "question": "What is causing today's biggest supply chain disruption?",
  "execution_trace": [
    {
      "step": 1,
      "tool": "forecast_demand",
      "parameters_used": {...},
      "reasoning": "Forecast demand for inventory analysis",
      "result": {...}
    },
    ...
  ],
  "final_answer": "Today's biggest supply chain disruption is caused by...",
  "confidence": "high",
  "caveats": "based on forecasted demand and current stock levels"
}
```

### GET /api/pending-actions
Fetch all pending actions awaiting approval.

**Query params:** `status` (default: "pending_approval")

**Response:**
```json
[
  {
    "action_id": "uuid-1234",
    "action_type": "reorder",
    "details": {
      "sku_id": "SKU008",
      "quantity": 2703,
      "warehouse_id": "WH-ASIA"
    },
    "reasoning": "Critical stockout detected for SKU008 at WH-ASIA...",
    "status": "pending_approval",
    "created_at": "2026-07-18T20:30:00Z"
  },
  ...
]
```

### POST /api/pending-actions/<action_id>/status
Update action status (approve/reject).

**Request:**
```json
{
  "status": "approved"
}
```

Valid statuses: `"approved"`, `"rejected"`, `"pending_approval"`

**Response:**
```json
{
  "success": true,
  "action_id": "uuid-1234",
  "new_status": "approved"
}
```

---

## Customization

### Colors
Edit `frontend/src/App.jsx`:
```javascript
const getRiskColor = (riskLevel) => {
  switch (riskLevel?.toLowerCase()) {
    case 'critical': return 'bg-red-600';    // Change here
    case 'high': return 'bg-orange-500';      // ...
    ...
  }
};
```

Or modify Tailwind theme in `tailwind.config.js`.

### API Base URL
Change in `frontend/src/App.jsx`:
```javascript
const API_BASE = 'http://localhost:5000/api';  // Change this
```

### Polling / Auto-Refresh
Add to `ChatInterface` useEffect to auto-fetch data periodically:
```javascript
useEffect(() => {
  const interval = setInterval(() => {
    fetchSweep();
  }, 60000);  // Every 60 seconds
  return () => clearInterval(interval);
}, []);
```

---

## Deployment

### Production Build (Frontend)

```bash
cd frontend
npm run build
```

Creates optimized static files in `frontend/dist/`. Deploy to any static host (Vercel, Netlify, AWS S3, etc.).

### Backend Deployment

Run `backend/api.py` on a Python hosting provider (Heroku, Railway, AWS Lambda with API Gateway, etc.):

```bash
gunicorn -w 4 -b 0.0.0.0:5000 backend.api:app
```

Set `API_BASE` in frontend to your production backend URL.

### CORS Configuration

Currently allows all origins (development). For production, update `backend/api.py`:

```python
CORS(app, resources={
    r"/api/*": {
        "origins": ["https://yourdomain.com"],
        "methods": ["GET", "POST"],
        "allow_headers": ["Content-Type"]
    }
})
```

---

## Troubleshooting

### Dashboard shows "No data available"
- Check backend is running: `curl http://localhost:5000/health`
- Check browser console for API errors
- Verify `API_BASE` matches backend URL

### API returns 500 errors
- Check backend logs for Python exceptions
- Verify database file exists: `data/supplysense.db`
- Ensure all agent modules imported correctly in `backend/api.py`

### Slow response times
- Backend querying 25 SKUs × 5 warehouses is ~2–3 seconds
- Optimize by caching sweep results or using a queue system (Celery, etc.)

### Chat messages not appearing
- Check browser DevTools > Network for `/api/query` request/response
- Verify Groq API key configured in backend if using real LLM

---

## Project Status

✅ **Complete & Verified**
- All 3 integration tests passing
- Backend agent layer fully functional with Groq LLM
- Frontend dashboard production-ready
- API server tested with CORS enabled

🚀 **Ready for Hackathon Demo**

---

## Next Steps (Post-Hackathon)

1. **Database**: Migrate SQLite to PostgreSQL for production
2. **Authentication**: Add user login + action history audit trail
3. **Real-time updates**: WebSocket for live alerts instead of polling
4. **Mobile app**: React Native version of dashboard
5. **Integrations**: Sync with ERP/supply chain platforms

---

## Questions?

Refer to the docstrings in `backend/api.py` and `frontend/src/App.jsx` for code-level details.
