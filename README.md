# SupplySense — AI Supply Chain Risk & Inventory Intelligence

A production-ready hackathon demo showcasing agentic AI for real-time supply chain monitoring, risk detection, and autonomous decision support.

## 🎯 Vision

SupplySense demonstrates **genuine agentic behavior**:
- **Perception**: Real data from SQLite (demand history, inventory, supplier metrics)
- **Reasoning**: Multi-step AI reasoning chains that understand context
- **Autonomy**: Proactive monitoring runs without user prompts
- **Grounding**: All answers reference specific data (SKUs, numbers, dates)
- **Critique**: LLM reviews proposed actions before execution

## 🏗️ Architecture

```
SupplySense/
├── backend/               # Deterministic business logic
│   ├── forecasting.py     # 7-day demand forecasts with trend detection
│   ├── inventory.py       # Stockout prediction & risk scoring
│   ├── suppliers.py       # Supplier reliability scoring
│   ├── shipments.py       # Delay impact detection
│   ├── allocation.py      # Intelligent stock allocation
│   └── api.py             # Flask REST API wrapper
│
├── agents/                # AI orchestration
│   ├── orchestrator.py    # Main agent + parameter resolution
│   ├── sweep.py           # Autonomous monitoring
│   ├── planner.py         # Deterministic multi-step planning
│   ├── composer.py        # Groq-powered answer synthesis
│   ├── critic.py          # Action review & approval
│   └── groq_provider.py   # Groq llama-3.3-70b integration
│
├── data/                  # SQLite data layer
│   ├── schema.py          # Table definitions
│   ├── generator.py       # Synthetic data seeding
│   ├── queries.py         # 11 data access functions
│   ├── store.py           # Connection pooling
│   └── supplysense.db     # Seeded database (25 SKUs, 20 suppliers)
│
├── frontend/              # React dashboard (Tailwind)
│   ├── src/
│   │   ├── App.jsx        # Main dashboard (~600 lines, no external UI libs)
│   │   ├── index.css      # Tailwind + custom styles
│   │   └── main.jsx       # React entry point
│   ├── index.html
│   ├── vite.config.js
│   ├── tailwind.config.js
│   └── package.json
│
└── README.md, DASHBOARD_SETUP.md, start.sh/start.bat
```

## 🚀 Quick Start

### Option 1: Automated (Recommended)

**macOS/Linux:**
```bash
chmod +x start.sh
./start.sh
```

**Windows:**
```cmd
start.bat
```

### Option 2: Manual

**Terminal 1 — Backend:**
```bash
pip install flask flask-cors
python backend/api.py
```

**Terminal 2 — Frontend:**
```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:3000** in your browser.

## 📊 Dashboard Features

### 1. **Executive Summary Banner**
- Real-time Groq-generated business summary
- "Refresh Analysis" button re-triggers autonomous sweep
- High-visibility pinned card

### 2. **Three-Column Responsive Panels**

#### Inventory Shortages
- Critical/high stockouts sorted by urgency
- Risk level badges (red/orange/yellow/green)
- Days until stockout (large, bold)
- Recommended reorder quantity

#### Supplier Risk Scores
- Sortable table (click header to sort)
- Expandable rows showing breakdown metrics:
  - On-time delivery %
  - Lead time variance (days)
  - Average quality score
- Risk category badges

#### Pending Actions
- AI-proposed reorders & supplier switches
- Action details, reasoning, and current status
- **Approve / Reject** buttons with instant feedback
- Toast notifications on action completion

### 3. **Interactive Q&A Chat**
- Ask natural language questions about your supply chain
- Collapsible "Show reasoning" reveals full execution trace
- Confidence badge (green/yellow/red)
- Caveats/limitations shown below answer
- Auto-scroll message history
- Animated thinking indicator while waiting

## 🎨 Design Highlights

- **Dark SaaS aesthetic**: Gray-900 base, gray-800 cards, white text
- **Generous spacing**: Comfortable padding and gaps throughout
- **Smooth interactions**: 0.2s transitions on all interactive elements
- **Smart empty states**: Friendly checkmark messages, no vague spinners
- **Loading skeletons**: Actual placeholder shapes with pulse animation
- **Responsive design**: Stacks vertically on mobile, side-by-side on desktop
- **Zero external UI libraries**: Pure Tailwind CSS + React hooks

## 📡 API Endpoints

```
GET  /api/sweep                              # Run autonomous monitoring
POST /api/query                              # Submit Q&A question
GET  /api/pending-actions                    # List pending actions
POST /api/pending-actions/<id>/status        # Approve/reject action
GET  /health                                 # Health check
```

See [DASHBOARD_SETUP.md](./DASHBOARD_SETUP.md) for full API docs.

## 🔬 Verified Capabilities

✅ **All 3 Integration Tests Passing**
- TEST 16: Forecast → Stockout chain (real demand history detected)
- TEST 17: Autonomous sweep with all 3 baked-in patterns detected
- TEST 18: End-to-end multi-step reasoning with Groq synthesis

✅ **Baked-In Patterns** (intentional seed data for demo)
1. **SUP014**: Supplier degradation (92% → 61% on-time delivery)
2. **SKU008**: Increasing demand trend (119% growth over 90 days)
3. **SKU015**: Sudden demand spike (3x in last 10 days)

✅ **Real Data Flow**
- 90 days of demand history per SKU
- 25 SKUs across 5 warehouses
- 20 suppliers with varied reliability
- SQLite persistently seeded (not re-generated on startup)

## 🛠️ Customization

### Change API Base URL
Edit `frontend/src/App.jsx`:
```javascript
const API_BASE = 'http://your-backend-url/api';
```

### Change Accent Color
In `frontend/src/App.jsx`, replace `orange-500` with your color throughout (bg-orange-500, hover:bg-orange-600, etc.).

### Add Polling / Auto-Refresh
```javascript
// In ChatInterface or main App component
useEffect(() => {
  const interval = setInterval(fetchSweep, 60000); // Every 60s
  return () => clearInterval(interval);
}, []);
```

### Production Deployment

**Frontend:**
```bash
cd frontend
npm run build
# Deploy dist/ folder to Vercel, Netlify, or S3
```

**Backend:**
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 backend.api:app
```

Configure CORS in `backend/api.py` for production origins.

## 🧪 Development & Testing

### Run Tests
```bash
# All 3 integration tests
python backend/test_chain_1.py    # TEST 16
python agents/test_sweep.py       # TEST 17
python agents/test_multistep.py   # TEST 18
```

### Check Code Quality
```bash
python -m pylint backend/ agents/ data/
```

### View Database
```bash
# Using sqlite3 CLI
sqlite3 data/supplysense.db
sqlite> SELECT * FROM inventory LIMIT 5;
```

## 📚 Key Files

| File | Purpose |
|------|---------|
| `backend/api.py` | Flask REST API server (wraps agent layer) |
| `frontend/src/App.jsx` | Main dashboard (~600 lines, single-file) |
| `agents/orchestrator.py` | Main agent class with parameter resolution |
| `data/queries.py` | SQLite data access (11 functions) |
| `DASHBOARD_SETUP.md` | Complete setup & API reference |

## 🚦 Next Steps (Post-Hackathon)

1. **Scale Database**: PostgreSQL instead of SQLite
2. **Real-time Alerts**: WebSocket instead of polling
3. **Audit Trail**: Log all action approvals/rejections
4. **Mobile App**: React Native version
5. **Integrations**: ERP/supply chain platform sync
6. **Analytics**: Track AI recommendations vs. actual outcomes

## 📝 License

This project is a hackathon entry demonstrating agentic AI capabilities. Feel free to fork, modify, and use as a foundation.

---

**Built with**: Python · React · Tailwind · Groq AI · SQLite

**Status**: ✅ Hackathon Ready · All tests passing · Production-ready code
