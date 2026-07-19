# Backend API Server - Complete Startup Guide

## ⚠️ IMPORTANT: File Synchronization Issue

Your local machine at `C:\Users\LOQ\OneDrive\Desktop\sem 5\hackthon\supplysense` is **missing the `agents/` folder** and other critical files.

### What Happened?
The backend files on your local machine are NOT in sync with the development workspace. This is why you were getting:
```
ModuleNotFoundError: No module named 'agents'
```

### Solution: Sync Your Local Folder

#### Option 1: Force OneDrive Sync (Recommended)
1. Open File Explorer
2. Navigate to `C:\Users\LOQ\OneDrive\Desktop\sem 5\hackthon\supplysense`
3. Right-click → Sync this folder
4. Wait for all files to download

#### Option 2: Use GitHub/Git
If this project is in a Git repository:
```powershell
cd "C:\Users\LOQ\OneDrive\Desktop\sem 5\hackthon\supplysense"
git pull origin main
```

#### Option 3: Manual Copy
Copy all files from the development environment to your local folder.

---

## Once Files Are Synced: Starting the Backend

### Step 1: Verify Python and Dependencies
```powershell
python --version  # Should be 3.13+
pip install flask flask-cors
```

### Step 2: Navigate to Project
```powershell
cd "C:\Users\LOQ\OneDrive\Desktop\sem 5\hackthon\supplysense"
```

### Step 3: Run Backend API

**Option A - Double-click `START_API.bat`** (Easiest on Windows)
- Simply double-click the `START_API.bat` file in your project root
- The terminal will open and show the server running

**Option B - PowerShell**
```powershell
python backend/api.py
```

**Option C - Command Prompt**
```cmd
python backend/api.py
```

### Step 4: Verify Server is Running

In a NEW terminal/PowerShell window:
```powershell
curl http://localhost:5000/health
```

You should see:
```json
{
  "message": "SupplySense Backend API is running",
  "status": "ok",
  "timestamp": "2026-07-19T03:13:08.953685"
}
```

---

## Full Expected Output When Starting

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

 * Serving Flask app 'api'
 * Debug mode: on
WARNING: This is a development server. Do not use it in a production deployment. Use a production WSGI server instead.
 * Running on http://127.0.0.1:5000
Press CTRL+C to quit
```

---

## Testing the API

### Test 1: Health Check
```powershell
curl http://localhost:5000/health
```

### Test 2: Test Endpoint
```powershell
curl http://localhost:5000/api/test
```

### Test 3: 404 Error Handling
```powershell
curl http://localhost:5000/nonexistent
```

---

## Next Steps: Connect Frontend

Once the backend is running on `http://localhost:5000`, you can:

1. **Start the frontend** in a separate terminal:
   ```powershell
   cd frontend
   npm install
   npm run dev
   ```

2. **The frontend will connect to** `http://localhost:5000` automatically

---

## Troubleshooting

### Error: "can't open file 'backend/api.py': [Errno 2] No such file or directory"
- **Cause**: Not in the project root directory
- **Fix**: Run `cd "C:\Users\LOQ\OneDrive\Desktop\sem 5\hackthon\supplysense"` first

### Error: "ModuleNotFoundError: No module named 'agents'"
- **Cause**: Files not synced to local machine
- **Fix**: See "File Synchronization Issue" section above

### Error: "Address already in use"
- **Cause**: Port 5000 is already in use
- **Fix**: Kill existing process:
  ```powershell
  netstat -ano | findstr :5000
  taskkill /PID <PID> /F
  ```
  Or change port in `backend/api.py` line 73

### Error: "UnicodeEncodeError"
- **Cause**: Windows console encoding issue
- **Fix**: Already fixed in current version - should not occur

### Server starts but frontend can't connect
- **Check**: Is `http://localhost:5000/health` accessible?
- **Check**: Is frontend trying to connect to correct URL?
- **Check**: Is CORS properly configured?

---

## Current API Status

✅ **Backend API is fully functional**

- Health check endpoint: `/health`
- Test endpoint: `/api/test`
- CORS enabled for frontend
- Debug mode enabled for development
- Auto-reload on file changes

---

## Production Notes

For production deployment, use Gunicorn instead of Flask's development server:

```powershell
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 backend.api:app
```

---

**Last Updated**: 2026-07-19
**Status**: ✅ VERIFIED WORKING
