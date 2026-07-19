@echo off
REM SupplySense Quick Start Script (Windows)
REM Starts both backend API server and frontend dev server

echo.
echo 🚀 SupplySense Quick Start
echo =========================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python not found. Please install Python 3.8+
    exit /b 1
)

REM Check if npm is installed
npm --version >nul 2>&1
if errorlevel 1 (
    echo ❌ npm not found. Please install Node.js
    exit /b 1
)

echo ✅ Python and Node.js found
echo.

REM Install backend dependencies
echo 📦 Installing backend dependencies...
pip install flask flask-cors -q

REM Start backend in background
echo 🔧 Starting backend API server (http://localhost:5000)...
start cmd /k python backend/api.py

REM Wait a moment for backend to start
timeout /t 2 /nobreak >nul

REM Install frontend dependencies if node_modules doesn't exist
if not exist "frontend\node_modules" (
    echo 📦 Installing frontend dependencies...
    cd frontend
    call npm install -q
    cd ..
)

REM Start frontend
echo ⚡ Starting frontend dev server (http://localhost:3000)...
cd frontend
start cmd /k npm run dev
cd ..

echo.
echo ✨ SupplySense is running!
echo    Frontend:  http://localhost:3000
echo    Backend:   http://localhost:5000
echo.
echo Two command windows should open. Close them to stop the servers.
echo.
pause
