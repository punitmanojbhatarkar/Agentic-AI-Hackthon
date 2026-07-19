# SUPER SIMPLE - JUST DO THIS

You need to type 2 things in Command Prompt.

---

## STEP 1: OPEN COMMAND PROMPT

Press these keys: `Windows Key` + `R`

A box appears.

Type: `cmd`

Press: `ENTER`

A BLACK WINDOW opens.

---

## STEP 2: TYPE THIS (Copy and paste exactly)

```
cd "C:\Users\LOQ\OneDrive\Desktop\sem 5\hackthon\supplysense"
```

Press: `ENTER`

---

## STEP 3: TYPE THIS (Copy and paste exactly)

```
python backend/api.py
```

Press: `ENTER`

Wait 2 seconds.

---

## DONE!

You should see something like:

```
[OK] Flask app initialized successfully
[START] SupplySense Backend API Server
[INFO] Running on http://localhost:5000
```

**YOUR BACKEND IS WORKING!**

---

## TO TEST IT WORKS

Open a NEW Command Prompt (Press `Windows Key + R`, type `cmd`, press `ENTER`)

Type this:

```
curl http://localhost:5000/health
```

Press: `ENTER`

You should see JSON:

```json
{
  "message": "SupplySense Backend API is running",
  "status": "ok"
}
```

**IT WORKS!** ✅

---

## TO STOP IT

In the Command Prompt with the backend:

Press: `Ctrl + C`

Window will ask to confirm, press `Y` and `ENTER`

---

## TO START FRONTEND (Optional)

Open NEW Command Prompt.

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

Wait for it to finish (1-2 minutes).

Type:
```
npm run dev
```

Press: `ENTER`

Open browser: `http://localhost:3000`

---

## DONE! 🎉

That's it. Your backend works now.
