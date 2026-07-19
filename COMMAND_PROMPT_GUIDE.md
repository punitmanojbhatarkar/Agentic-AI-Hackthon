# COMMAND PROMPT - EXACT TYPING GUIDE

This is EXACTLY what you need to type. Copy and paste every character.

---

## OPEN COMMAND PROMPT

Press: `Windows Key + R`

Type: `cmd`

Press: `ENTER`

(A black window opens)

---

## COMMAND 1: NAVIGATE TO PROJECT

**Type this exactly:**
```
cd "C:\Users\LOQ\OneDrive\Desktop\sem 5\hackthon\supplysense"
```

**Press: ENTER**

**You should see:**
```
C:\Users\LOQ\OneDrive\Desktop\sem 5\hackthon\supplysense>
```

---

## COMMAND 2: CHECK SETUP (Optional)

**Type this exactly:**
```
python diagnose_backend.py
```

**Press: ENTER**

**Wait for it to finish. Last line should say:**
```
[OK] All checks passed! You can start the API with:
     python backend/api.py
```

---

## COMMAND 3: START THE BACKEND

**Type this exactly:**
```
python backend/api.py
```

**Press: ENTER**

**You should see:**
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

✅ **BACKEND IS RUNNING!**

**DO NOT CLOSE THIS WINDOW - Leave it running!**

---

## COMMAND 4: OPEN NEW COMMAND PROMPT

Press: `Windows Key + R`

Type: `cmd`

Press: `ENTER`

(A NEW black window opens)

**This is now your second command prompt**

---

## COMMAND 5: TEST THE BACKEND

**In the NEW command prompt, type this exactly:**
```
curl http://localhost:5000/health
```

**Press: ENTER**

**You should see:**
```json
{
  "message": "SupplySense Backend API is running",
  "status": "ok",
  "timestamp": "2026-07-19T03:18:45.787033"
}
```

✅ **IT WORKS!**

---

## COMMAND 6: (OPTIONAL) START FRONTEND

Press: `Windows Key + R`

Type: `cmd`

Press: `ENTER`

(A THIRD black window opens)

**In this new command prompt, type this exactly:**
```
cd "C:\Users\LOQ\OneDrive\Desktop\sem 5\hackthon\supplysense\frontend"
```

**Press: ENTER**

**Then type this exactly:**
```
npm install
```

**Press: ENTER**

**Wait for it to finish (might take 1-2 minutes)**

**Then type this exactly:**
```
npm run dev
```

**Press: ENTER**

**You should see:**
```
  VITE v... ready in ... ms

  ➜  Local:   http://localhost:3000/
```

✅ **FRONTEND IS RUNNING!**

---

## WHAT YOU SHOULD HAVE NOW

### Window 1 (Backend)
```
C:\Users\LOQ\OneDrive\Desktop\sem 5\hackthon\supplysense>python backend/api.py
```
Shows running server

### Window 2 (Testing)
```
C:\Users\LOQ\OneDrive\Desktop\sem 5\hackthon\supplysense>curl http://localhost:5000/health
```
Shows JSON response

### Window 3 (Frontend - Optional)
```
C:\Users\LOQ\OneDrive\Desktop\sem 5\hackthon\supplysense\frontend>npm run dev
```
Shows frontend running

---

## ERROR FIXES

### If you get: "python: command not found"

**Type this exactly:**
```
python --version
```

**Press: ENTER**

If it shows version (like 3.13.14), Python is installed.

If it says "not found", Python is not installed. Google "install Python Windows" and install it.

---

### If you get: "Address already in use"

**Open a new command prompt**

**Type this exactly:**
```
netstat -ano | findstr :5000
```

**Press: ENTER**

**You'll see something like:**
```
TCP    127.0.0.1:5000    0.0.0.0:0    LISTENING    12345
```

**Copy the last number (12345 in this example)**

**Type this exactly (replace 12345 with your number):**
```
taskkill /PID 12345 /F
```

**Press: ENTER**

**Then try the backend command again**

---

### If you get: "Flask not installed"

**Type this exactly:**
```
pip install flask flask-cors
```

**Press: ENTER**

**Wait for it to finish**

**Then try the backend command again**

---

## STEP-BY-STEP WITH SCREENSHOTS

### Step 1: Open Command Prompt
- Press `Windows Key + R`
- See "Run" dialog
- Type: `cmd`
- Click OK or press ENTER
- Black window opens

### Step 2: Type First Command
- Copy: `cd "C:\Users\LOQ\OneDrive\Desktop\sem 5\hackthon\supplysense"`
- Right-click in black window, choose "Paste"
- Press ENTER
- Prompt changes to show your project path

### Step 3: Type Second Command
- Copy: `python backend/api.py`
- Right-click in black window, choose "Paste"
- Press ENTER
- Server starts

### Step 4: Open New Command Prompt
- Press `Windows Key + R`
- Type: `cmd`
- Click OK
- New black window opens

### Step 5: Type Test Command
- Copy: `curl http://localhost:5000/health`
- Right-click in black window, choose "Paste"
- Press ENTER
- See JSON response

---

## COPY-PASTE HELPER

Can't copy-paste? Here are the commands character by character:

### Command 1 (Navigate):
```
c d   " C : \ U s e r s \ L O Q \ O n e D r i v e \ D e s k t o p \ s e m   5 \ h a c k t h o n \ s u p p l y s e n s e "
```
(Remove spaces between letters)

### Command 2 (Check):
```
p y t h o n   d i a g n o s e _ b a c k e n d . p y
```
(Remove spaces between letters)

### Command 3 (Start):
```
p y t h o n   b a c k e n d / a p i . p y
```
(Remove spaces between letters)

### Command 4 (Test):
```
c u r l   h t t p : / / l o c a l h o s t : 5 0 0 0 / h e a l t h
```
(Remove spaces between letters)

---

## KEYBOARD SHORTCUTS

| Shortcut | What it does |
|----------|-------------|
| `Ctrl+C` | Stop the server (in command prompt with running server) |
| `Ctrl+V` | Paste text (in command prompt) |
| `Ctrl+A` | Select all text |
| `Right-click` | Paste option appears |
| `Windows+R` | Open Run dialog |
| `Windows+Shift+S` | Screenshot tool |

---

## FINAL CHECKLIST

- [ ] Opened command prompt
- [ ] Typed: `cd "C:\Users\LOQ\OneDrive\Desktop\sem 5\hackthon\supplysense"`
- [ ] Typed: `python backend/api.py`
- [ ] Saw: "Running on http://127.0.0.1:5000"
- [ ] Opened NEW command prompt
- [ ] Typed: `curl http://localhost:5000/health`
- [ ] Saw: JSON response with "status": "ok"
- [ ] ✅ Done!

---

## SUCCESS!

When you see the JSON response from curl, your backend is working! 🎉

You can now:
- Keep it running and use it
- Open frontend in another window
- Test with your React app

---

**Everything is ready!**

Just follow the commands above step by step.
