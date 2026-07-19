# 🚀 START HERE — SupplySense Quick Launch

## TL;DR — Get Running in 30 Seconds

### macOS / Linux
```bash
chmod +x start.sh && ./start.sh
```

### Windows
```cmd
start.bat
```

**Then open your browser:** http://localhost:3000

---

## ✅ What You'll See

1. **Dashboard** with 3 panels:
   - Critical inventory shortages
   - Supplier risk scores
   - Pending actions (AI proposals)

2. **Executive Summary** (top banner) — Groq-generated insights

3. **Chat Interface** (bottom) — Ask questions about your supply chain

4. **Live Data** — Real 90-day demand history, 25 SKUs, 20 suppliers

---

## 📖 Documentation (Pick One)

| Goal | Read This |
|------|-----------|
| **Understand what it is** | [README.md](README.md) |
| **See a demo script** | [DEMO_GUIDE.md](DEMO_GUIDE.md) |
| **Deploy it** | [DASHBOARD_SETUP.md](DASHBOARD_SETUP.md) → Deployment |
| **Understand the code** | [ARCHITECTURE.md](ARCHITECTURE.md) |
| **See all features** | [VISUAL_SUMMARY.md](VISUAL_SUMMARY.md) |
| **Navigate all docs** | [DOCUMENTATION.md](DOCUMENTATION.md) |

---

## 🎯 Key Facts

✨ **Genuine AI Agent** — Multi-step reasoning chains, not a chatbot

📊 **Production Dashboard** — SaaS-grade dark theme, responsive design

✅ **Verified** — All 3 integration tests passing with real data

🚀 **Ready to Deploy** — Frontend (Vercel/Netlify), Backend (Heroku/Railway)

---

## ❓ Common Questions

**Q: What happens if something breaks?**
> See Troubleshooting section in [DASHBOARD_SETUP.md](DASHBOARD_SETUP.md)

**Q: How do I deploy to production?**
> See Deployment section in [DASHBOARD_SETUP.md](DASHBOARD_SETUP.md) or [DELIVERY_SUMMARY.md](DELIVERY_SUMMARY.md)

**Q: What if I want to customize it?**
> See Customization section in every doc, or check [PROJECT_MANIFEST.md](PROJECT_MANIFEST.md)

**Q: Is the AI real or mocked?**
> Real Groq Llama 3.3 70B. Watch the "Show reasoning" tab to see steps.

---

## 🎬 For Demos

Read [DEMO_GUIDE.md](DEMO_GUIDE.md) — it has a full 10-minute script with talking points and Q&A.

**Pre-Demo Checklist:**
- ☑ Both servers running
- ☑ Dashboard loads
- ☑ Try 1 question in chat
- ☑ Test on mobile
- ☑ Memorize talking points

---

## 📁 Quick File Reference

```
frontend/src/App.jsx       Main dashboard (~600 lines)
backend/api.py             Flask REST API
data/supplysense.db        Seeded database
```

All API endpoints in [DASHBOARD_SETUP.md](DASHBOARD_SETUP.md)

---

## 🎓 Learn More

- **System Design:** [ARCHITECTURE.md](ARCHITECTURE.md)
- **What's Included:** [PROJECT_MANIFEST.md](PROJECT_MANIFEST.md)
- **Final Status:** [DELIVERY_SUMMARY.md](DELIVERY_SUMMARY.md)
- **Code Quality:** [COMPLETION_CHECKLIST.md](COMPLETION_CHECKLIST.md)

---

## 🚀 Status

✅ 100% complete and production ready.

**One command to start.** Everything else works.

Good luck! 🎯

---

**Next Step:** Run `./start.sh` or `start.bat`, then open http://localhost:3000
