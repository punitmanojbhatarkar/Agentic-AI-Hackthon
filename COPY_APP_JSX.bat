@echo off
REM This script copies the App.jsx file to your local machine
REM Run this from your workspace directory

echo Copying App.jsx to your local frontend folder...

copy "frontend\src\App.jsx" "C:\Users\LOQ\OneDrive\Desktop\sem 5\hackthon\supplysense\frontend\src\App.jsx"

if %errorlevel% equ 0 (
    echo.
    echo SUCCESS! App.jsx has been copied to:
    echo C:\Users\LOQ\OneDrive\Desktop\sem 5\hackthon\supplysense\frontend\src\App.jsx
    echo.
    echo You can now start your dev server:
    echo npm run dev
) else (
    echo ERROR: Failed to copy file. Check the paths.
)

pause
