# EXACT COMMANDS TO COPY & PASTE

Copy each command exactly as shown and paste into your terminal.

---

## STEP 1: NAVIGATE TO YOUR PROJECT

Copy and paste this EXACTLY:

```
cd "C:\Users\LOQ\OneDrive\Desktop\sem 5\hackthon\supplysense"
```

Then press **ENTER**

---

## STEP 2: VERIFY SETUP (Optional but Recommended)

Copy and paste this EXACTLY:

```
python diagnose_backend.py
```

Then press **ENTER**

**Expected output ends with:**
```
Results: 14 passed, 0 failed
[OK] All checks passed!
```

---

## STEP 3: START THE BACKEND API

Copy and paste this EXACTLY:

```
python backend/api.py
```

Then press **ENTER**

**Expected output:**
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
 * Running on http://127.0.0.1:5000
Press CTRL+C to quit
```

✅ **BACKEND IS NOW RUNNING!**

---

## STEP 4: TEST IT WORKS (New Terminal/PowerShell)

**OPEN A NEW TERMINAL** (don't close the one with the API running)

Copy and paste this EXACTLY:

```
curl http://localhost:5000/health
```

Then press **ENTER**

**Expected output:**
```json
{
  "message": "SupplySense Backend API is running",
  "status": "ok",
  "timestamp": "2026-07-19T03:18:45.787033"
}
```

✅ **IT WORKS!**

---

## STEP 5: (OPTIONAL) START FRONTEND

**OPEN ANOTHER NEW TERMINAL** (keep both previous ones running)

Copy and paste this EXACTLY:

```
cd "C:\Users\LOQ\OneDrive\Desktop\sem 5\hackthon\supplysense\frontend"
```

Then press **ENTER**

Then copy and paste this EXACTLY:

```
npm install
```

Then press **ENTER** (wait for it to finish, might take a minute)

Then copy and paste this EXACTLY:

```
npm run dev
```

Then press **ENTER**

**Expected output includes:**
```
  VITE v... ready in ... ms

  ➜  Local:   http://localhost:3000/
```

---

## SUMMARY - 3 TERMINALS RUNNING

### Terminal 1 (Backend API)
```
python backend/api.py
```
Runs on: `http://localhost:5000`

### Terminal 2 (Testing)
```
curl http://localhost:5000/health
```
Shows: JSON response

### Terminal 3 (Frontend - Optional)
```
npm run dev
```
Runs on: `http://localhost:3000`

---

## IF YOU GET ERRORS

### Error: "Address already in use"

Copy and paste this EXACTLY:

```
netstat -ano | findstr :5000
```

Press **ENTER**, you'll see something like:
```
TCP    127.0.0.1:5000    0.0.0.0:0    LISTENING    12345
```

The number at the end is the PID. Copy it. Then paste this:

```
taskkill /PID 12345 /F
```

(Replace 12345 with your actual PID)

Press **ENTER**

Then try running the backend again.

---

### Error: "Flask not installed"

Copy and paste this EXACTLY:

```
pip install flask flask-cors
```

Press **ENTER**

Wait for it to finish, then try running the backend again.

---

### Error: "Python not found"

Copy and paste this EXACTLY:

```
python --version
```

Press **ENTER**

Should show: `Python 3.13.14` (or similar 3.13+)

If not found, you need to install Python first.

---

## QUICK REFERENCE

| What to do | Command |
|-----------|---------|
| Go to project | `cd "C:\Users\LOQ\OneDrive\Desktop\sem 5\hackthon\supplysense"` |
| Verify setup | `python diagnose_backend.py` |
| Start backend | `python backend/api.py` |
| Test backend | `curl http://localhost:5000/health` |
| Start frontend | `npm run dev` (from frontend folder) |
| Check what's on port 5000 | `netstat -ano \| findstr :5000` |
| Kill process on port 5000 | `taskkill /PID [PID] /F` |
| Install packages | `pip install flask flask-cors` |

---

## COMPLETE WORKFLOW (Copy & Paste in Order)

### Terminal 1: Start Backend
```
cd "C:\Users\LOQ\OneDrive\Desktop\sem 5\hackthon\supplysense"
python backend/api.py
```

### Terminal 2: Test Backend
```
curl http://localhost:5000/health
```

### Terminal 3: Start Frontend (Optional)
```
cd "C:\Users\LOQ\OneDrive\Desktop\sem 5\hackthon\supplysense\frontend"
npm install
npm run dev
```

---

## WINDOWS PATH EXPLANATION

Your project path is:
```
C:\Users\LOQ\OneDrive\Desktop\sem 5\hackthon\supplysense
```

Breaking it down:
- `C:\Users\LOQ\` = Your user folder
- `OneDrive\` = OneDrive cloud folder
- `Desktop\` = Your desktop
- `sem 5\` = Folder named "sem 5"
- `hackthon\` = Folder named "hackthon"
- `supplysense\` = Project folder

The spaces in "sem 5" are why we use quotes: `"C:\Users\LOQ\OneDrive\Desktop\sem 5\hackthon\supplysense"`

---

## HOW TO OPEN MULTIPLE TERMINALS

### Method 1: Windows Terminal (Recommended)
- Right-click on taskbar at bottom
- Select "Windows Terminal" or "PowerShell"
- Opens new terminal window
- Repeat to open multiple windows

### Method 2: Press Ctrl+Shift+N
- Opens new terminal window in many programs

### Method 3: Right-click Project Folder
- Click "Open in Terminal" or "Open PowerShell here"

---

## WHEN YOU'RE DONE

To stop everything, in each terminal press:
```
Ctrl+C
```

Then close the terminal windows.

---

## ✅ SUCCESS CHECKLIST

- [ ] Terminal 1: Backend running (no errors)
- [ ] Terminal 2: `curl` command shows JSON response
- [ ] Terminal 3 (Optional): Frontend running on http://localhost:3000

If all checkboxes checked, you're done! 🎉

---

**Status**: Ready to use  
**Next**: Copy-paste the commands above  
**Expected time**: 2 minutes
