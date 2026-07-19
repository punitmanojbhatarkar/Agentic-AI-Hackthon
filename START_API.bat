@echo off
REM ==========================================
REM SupplySense Backend API Startup Script
REM ==========================================

echo.
echo ==========================================
echo SupplySense Backend API Startup
echo ==========================================
echo.

REM Get the directory where this batch file is located
cd /d "%~dp0"

echo Starting Python Flask server...
echo Running: python backend/api.py
echo.
echo Endpoints will be available at:
echo   - http://localhost:5000/health
echo   - http://localhost:5000/api/test
echo.
echo Press Ctrl+C to stop the server
echo.

python backend/api.py

pause
