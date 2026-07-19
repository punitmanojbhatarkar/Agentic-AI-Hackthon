@echo off
REM Clean kill all node processes and restart fresh

echo ========================================
echo KILLING ALL NODE PROCESSES
echo ========================================

taskkill /F /IM node.exe 2>nul

echo.
echo Waiting 3 seconds...
timeout /t 3 /nobreak

echo.
echo ========================================
echo NAVIGATING TO FRONTEND DIRECTORY
echo ========================================
echo.

cd /d "C:\Users\LOQ\OneDrive\Desktop\sem 5\hackthon\supplysense\frontend"

echo Current directory: %cd%

echo.
echo ========================================
echo CLEARING CACHE
echo ========================================
echo.

if exist dist rmdir /s /q dist
if exist node_modules\.vite rmdir /s /q node_modules\.vite

echo Cache cleared!

echo.
echo ========================================
echo STARTING DEV SERVER
echo ========================================
echo.
echo Running: npm run dev
echo.
echo Go to browser: http://localhost:5173
echo.

npm run dev

pause
