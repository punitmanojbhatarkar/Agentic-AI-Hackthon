# Quick Start - Backend API

## For Windows Users (Easiest)

1. **Double-click** `START_API.bat` 

   A terminal will open showing:
   ```
   ============================================================
   [START] SupplySense Backend API Server
   ============================================================
   [INFO] Running on http://localhost:5000
   ```

2. **Test it works** - Open browser or new terminal and run:
   ```
   curl http://localhost:5000/health
   ```

3. **You should see**:
   ```json
   {
     "message": "SupplySense Backend API is running",
     "status": "ok",
     "timestamp": "2026-07-19T03:18:45.787033"
   }
   ```

✅ **Done!** Backend is running on http://localhost:5000

---

## For PowerShell/Command Prompt Users

```powershell
cd "C:\Users\LOQ\OneDrive\Desktop\sem 5\hackthon\supplysense"
python backend/api.py
```

---

## Common Issues & Fixes

### Issue: "No such file or directory"
**Fix**: Make sure all files are synced to your local folder. See `BACKEND_STARTUP_GUIDE.md`

### Issue: "Port 5000 already in use"
**Fix**: 
```powershell
netstat -ano | findstr :5000
taskkill /PID <PID> /F
```

### Issue: "ModuleNotFoundError: No module named 'agents'"
**Fix**: Run from project root directory where `backend/`, `agents/`, `data/` folders exist

---

## What's Running?

- **Server**: Flask development server
- **Address**: http://localhost:5000
- **Features**: 
  - Auto-reload on file changes
  - Debug mode enabled
  - CORS enabled for frontend

---

## Next: Start Frontend

In a **NEW** terminal window:

```powershell
cd frontend
npm install
npm run dev
```

Frontend will run on http://localhost:3000 and automatically connect to backend on http://localhost:5000

---

**Read more**: `BACKEND_STARTUP_GUIDE.md` or `BACKEND_API_VERIFICATION_REPORT.md`
