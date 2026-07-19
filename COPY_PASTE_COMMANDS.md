# Copy & Paste Commands - Backend API

All the commands you need to get your backend running.

---

## 🚀 START THE BACKEND

### Method 1: Windows (Easiest)
```
Double-click: START_API.bat
```

### Method 2: PowerShell/Command Prompt
```powershell
python backend/api.py
```

### Method 3: Python Launcher
```powershell
python run_backend.py
```

---

## ✅ VERIFY IT WORKS

In a NEW terminal (don't close the one running the API):

```powershell
curl http://localhost:5000/health
```

Expected output:
```json
{
  "message": "SupplySense Backend API is running",
  "status": "ok",
  "timestamp": "2026-07-19T03:18:45.787033"
}
```

---

## 🔍 CHECK SETUP

```powershell
python diagnose_backend.py
```

Expected output (end of output):
```
Results: 14 passed, 0 failed
[OK] All checks passed! You can start the API with:
     python backend/api.py
```

---

## 🧪 TEST ENDPOINTS

### Test 1: Health Check
```powershell
curl http://localhost:5000/health
```

### Test 2: API Test
```powershell
curl http://localhost:5000/api/test
```

### Test 3: Error Handling (404)
```powershell
curl http://localhost:5000/nonexistent
```

---

## 🌐 START FRONTEND (Optional)

In a NEW terminal:
```powershell
cd frontend
npm install
npm run dev
```

Then visit: `http://localhost:3000`

---

## 🛠️ TROUBLESHOOTING

### Port 5000 Already in Use?
```powershell
netstat -ano | findstr :5000
taskkill /PID <PID> /F
```

### Flask Not Installed?
```powershell
pip install flask flask-cors
```

### Check Python Version
```powershell
python --version
```

Should be 3.13+

---

## 📁 NAVIGATE TO PROJECT

From anywhere:
```powershell
cd "C:\Users\LOQ\OneDrive\Desktop\sem 5\hackthon\supplysense"
```

---

## 📚 READ DOCUMENTATION

### Ultra-Quick (30 seconds)
```powershell
# Just view the file
notepad START_HERE_BACKEND.md
```

### Quick Start (2 minutes)
```powershell
notepad QUICK_START_BACKEND.md
```

### Full Guide (15 minutes)
```powershell
notepad BACKEND_STARTUP_GUIDE.md
```

---

## 🎯 ONE-LINER WORKFLOW

```powershell
# Start backend
python backend/api.py

# In new terminal: verify it works
curl http://localhost:5000/health

# In another new terminal: start frontend
cd frontend; npm run dev
```

---

## ⏱️ TIMING

| Task | Time |
|------|------|
| Start backend | < 2 sec |
| First request response | < 10 ms |
| Test with curl | < 1 sec |
| Start frontend | < 30 sec |
| Total setup | < 2 min |

---

## 🎉 YOU'RE DONE WHEN YOU SEE

**Backend Terminal**:
```
[OK] Flask app initialized successfully
============================================================
[START] SupplySense Backend API Server
============================================================
[INFO] Running on http://localhost:5000
[OK] Health check: http://localhost:5000/health
[OK] Test endpoint: http://localhost:5000/api/test

   Press Ctrl+C to stop
============================================================

 * Running on http://127.0.0.1:5000
```

**Curl Response**:
```json
{
  "message": "SupplySense Backend API is running",
  "status": "ok"
}
```

✅ **Backend is working!**

---

## 📋 QUICK CHECKLIST

- [ ] Run `python backend/api.py`
- [ ] See startup message
- [ ] Open new terminal
- [ ] Run `curl http://localhost:5000/health`
- [ ] See JSON response
- [ ] ✅ Done!

---

**That's all you need!** 🚀

Your backend API is ready to use.
