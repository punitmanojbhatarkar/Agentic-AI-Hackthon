@echo off
REM Restart Frontend Dev Server with proper cleanup

setlocal enabledelayedexpansion

set FRONTEND_DIR=C:\Users\LOQ\OneDrive\Desktop\sem 5\hackthon\supplysense\frontend

echo.
echo ============================================================
echo SupplySense Frontend Restart Script
echo ============================================================
echo.

echo [1] Checking if index.html exists...
if exist "%FRONTEND_DIR%\index.html" (
    echo [OK] index.html found
) else (
    echo [ERROR] index.html NOT found!
    echo Please create it first.
    pause
    exit /b 1
)

echo [2] Navigating to frontend directory...
cd /d "%FRONTEND_DIR%"
echo [OK] Current directory: %cd%

echo.
echo [3] Stopping any existing processes...
REM Node processes will be stopped by Ctrl+C when running dev

echo [4] Clearing cache...
if exist dist (
    rmdir /s /q dist
    echo [OK] Cache cleared
)

if exist node_modules\.vite (
    rmdir /s /q node_modules\.vite
    echo [OK] Vite cache cleared
)

echo.
echo [5] Starting dev server...
echo.
echo ============================================================
echo Starting: npm run dev
echo ============================================================
echo.

npm run dev

pause
