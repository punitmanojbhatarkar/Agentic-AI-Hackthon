@echo off
REM This script syncs missing frontend files to your local machine

setlocal enabledelayedexpansion

set FRONTEND_DIR=C:\Users\LOQ\OneDrive\Desktop\sem 5\hackthon\supplysense\frontend

echo.
echo ============================================================
echo SupplySense Frontend File Sync
echo ============================================================
echo.
echo Checking for missing files in: %FRONTEND_DIR%
echo.

REM Check if index.html exists
if not exist "%FRONTEND_DIR%\index.html" (
    echo [!] index.html is MISSING - Creating it now...
    (
        echo ^<!DOCTYPE html^>
        echo ^<html lang="en"^>
        echo   ^<head^>
        echo     ^<meta charset="UTF-8" /^>
        echo     ^<link rel="icon" type="image/svg+xml" href="/favicon.svg" /^>
        echo     ^<meta name="viewport" content="width=device-width, initial-scale=1.0" /^>
        echo     ^<title^>SupplySense — AI Supply Chain Intelligence^</title^>
        echo   ^</head^>
        echo   ^<body^>
        echo     ^<div id="root"^>^</div^>
        echo     ^<script type="module" src="/src/main.jsx"^>^</script^>
        echo   ^</body^>
        echo ^</html^>
    ) > "%FRONTEND_DIR%\index.html"
    echo [OK] index.html created!
) else (
    echo [OK] index.html exists
)

REM Check if src/main.jsx exists
if not exist "%FRONTEND_DIR%\src\main.jsx" (
    echo [!] src/main.jsx is MISSING
    echo Please manually sync from source
) else (
    echo [OK] src/main.jsx exists
)

REM Check if src/App.jsx exists
if not exist "%FRONTEND_DIR%\src\App.jsx" (
    echo [!] src/App.jsx is MISSING
    echo Please manually sync from source
) else (
    echo [OK] src/App.jsx exists
)

REM Check if src/index.css exists
if not exist "%FRONTEND_DIR%\src\index.css" (
    echo [!] src/index.css is MISSING
    echo Please manually sync from source
) else (
    echo [OK] src/index.css exists
)

REM Check if package.json exists
if not exist "%FRONTEND_DIR%\package.json" (
    echo [!] package.json is MISSING
) else (
    echo [OK] package.json exists
)

echo.
echo ============================================================
echo File sync complete!
echo ============================================================
echo.
echo Next steps:
echo 1. In frontend command prompt, press Ctrl+C to stop dev server
echo 2. Type: npm run dev
echo 3. Open browser: http://localhost:5173
echo.
pause
