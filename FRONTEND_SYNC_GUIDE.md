# FRONTEND SYNC - STEP BY STEP

## The Problem

Your local machine's `frontend/` folder is missing the `index.html` file. This is why Vite shows 404.

**Missing file**: `C:\Users\LOQ\OneDrive\Desktop\sem 5\hackthon\supplysense\frontend\index.html`

## The Solution

### OPTION 1: Run the Sync Script (Easiest)

1. Find the file: `SYNC_FRONTEND_FILES.bat` (in your project root)
2. Double-click it
3. It will create the missing `index.html` file
4. Press any key to close

### OPTION 2: Manual File Sync with OneDrive

1. Open File Explorer
2. Go to: `C:\Users\LOQ\OneDrive\Desktop\sem 5\hackthon\supplysense`
3. Right-click the `frontend` folder
4. Select: **"Always keep on this device"** or **"Sync"**
5. Wait for files to download

### OPTION 3: Git Pull (If using Git)

In Command Prompt:
```
cd "C:\Users\LOQ\OneDrive\Desktop\sem 5\hackthon\supplysense"
git pull origin main
```

---

## Next Steps After File Sync

### Step 1: Stop the Dev Server
In your frontend Command Prompt, press: `Ctrl + C`

Type: `Y` and press `ENTER`

### Step 2: Restart Dev Server
```
npm run dev
```

Press: `ENTER`

### Step 3: Open Frontend
Go to browser: `http://localhost:5173`

You should see the SupplySense dashboard! 🎉

---

## Files That Must Exist

✅ `frontend/index.html` - Entry point (CRITICAL)
✅ `frontend/src/main.jsx` - React app entry
✅ `frontend/src/App.jsx` - Main app component
✅ `frontend/src/index.css` - Tailwind CSS
✅ `frontend/package.json` - Dependencies
✅ `frontend/tailwind.config.js` - Tailwind config
✅ `frontend/vite.config.js` - Vite config
✅ `frontend/tsconfig.json` - TypeScript config
✅ `frontend/tsconfig.node.json` - TS Node config

---

## Expected Result

When you visit `http://localhost:5173`, you should see:

- SupplySense header
- Three panels:
  - Inventory Shortages
  - Supplier Risk Scores
  - Agent-Proposed Actions
- Chat interface at bottom
- All connected to backend API on port 5000

---

Choose one of the 3 options above and report back when done!
