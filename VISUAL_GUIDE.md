# VISUAL STEP-BY-STEP GUIDE

## STEP 1️⃣: OPEN COMMAND PROMPT

Look at bottom of screen, you'll see taskbar:

```
[Search] [Taskbar with icons...]
```

Press on keyboard: `Windows Key` + `R`

You'll see this box:

```
┌─────────────────────────────────┐
│ Run                             │
├─────────────────────────────────┤
│ Open: _______________           │
│  [Cancel]        [OK]           │
└─────────────────────────────────┘
```

In the blank box, type: `cmd`

Then click `OK` or press `ENTER`

A BLACK window appears (Command Prompt)

```
Microsoft Windows [Version 10.0.19041]
(c) Microsoft Corporation. All rights reserved.

C:\Users\LOQ>
```

---

## STEP 2️⃣: NAVIGATE TO PROJECT

In the black window, type this EXACTLY:

```
cd "C:\Users\LOQ\OneDrive\Desktop\sem 5\hackthon\supplysense"
```

Press: `ENTER`

The prompt changes to:

```
C:\Users\LOQ\OneDrive\Desktop\sem 5\hackthon\supplysense>
```

✅ You're now in the right folder

---

## STEP 3️⃣: START THE BACKEND

In the same window, type this EXACTLY:

```
python backend/api.py
```

Press: `ENTER`

You'll see text appearing like this:

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
INFO:werkzeug: * Running on http://127.0.0.1:5000
```

✅ **BACKEND IS RUNNING!**

**DO NOT CLOSE THIS WINDOW!**

---

## STEP 4️⃣: TEST IT IN NEW WINDOW

Don't close the window above!

Open ANOTHER Command Prompt:

Press: `Windows Key` + `R`

Type: `cmd`

Click `OK`

NEW black window opens.

In this NEW window, type:

```
curl http://localhost:5000/health
```

Press: `ENTER`

You'll see:

```json
{
  "message": "SupplySense Backend API is running",
  "status": "ok",
  "timestamp": "2026-07-19T03:18:45.787033"
}
```

✅ **IT WORKS!**

---

## WHAT YOU SHOULD HAVE NOW

### Window 1 (Running in background)
```
[Backend running]
Running on http://127.0.0.1:5000
```

### Window 2 (Just tested)
```
[Test result]
{"status": "ok", ...}
```

Both windows should be OPEN and showing these messages.

---

## TO STOP THE BACKEND

Go to Window 1 (the one with the backend running).

Press on keyboard: `Ctrl` + `C`

You might see:

```
Terminate batch job (Y/N)?
```

Type: `Y`

Press: `ENTER`

Backend stops.

---

## OPTIONAL: START FRONTEND

Open ANOTHER new Command Prompt:

Press: `Windows Key` + `R`

Type: `cmd`

Click `OK`

Type:

```
cd "C:\Users\LOQ\OneDrive\Desktop\sem 5\hackthon\supplysense\frontend"
```

Press: `ENTER`

Type:

```
npm install
```

Press: `ENTER`

Wait 1-2 minutes for it to finish (lots of text will appear).

Type:

```
npm run dev
```

Press: `ENTER`

You'll see:

```
  VITE v5.0.0 ready in 321 ms

  ➜  Local:   http://localhost:3000/
  ➜  press h to show help
```

✅ Frontend is running!

Open your browser and go to: `http://localhost:3000`

---

## THREE WINDOWS RUNNING

### Window 1 (Backend)
```
Running on http://127.0.0.1:5000
```

### Window 2 (Test - can close)
```
(already tested, can close)
```

### Window 3 (Frontend - Optional)
```
VITE ready
http://localhost:3000
```

---

## ERRORS & FIXES

### See: "Address already in use"
→ See `COMMAND_PROMPT_GUIDE.md` section "Address already in use"

### See: "Flask not installed"
→ Type: `pip install flask flask-cors`

### See: "python: command not found"
→ Python not installed, need to install it first

### See: Nothing happening
→ Wait a few seconds, the server takes time to start

---

## SUCCESS INDICATORS ✅

- Window 1 shows: `Running on http://127.0.0.1:5000`
- Window 2 shows: JSON response
- Browser shows: Frontend (if you opened it)

If you see these, **EVERYTHING IS WORKING!** 🎉

---

## SUMMARY

1. Open Command Prompt → `Windows Key + R` → `cmd` → `ENTER`
2. Type: `cd "C:\Users\LOQ\OneDrive\Desktop\sem 5\hackthon\supplysense"` → `ENTER`
3. Type: `python backend/api.py` → `ENTER`
4. See: Server running message ✅
5. Open NEW Command Prompt
6. Type: `curl http://localhost:5000/health` → `ENTER`
7. See: JSON response ✅
8. Done!

---

**Everything working?** → You're done! 🎉

Your backend API is ready to use!
