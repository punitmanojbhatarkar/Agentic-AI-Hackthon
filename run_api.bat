@echo off
REM SupplySense Backend Startup Script

setlocal enabledelayedexpansion

REM Get the current directory
set PROJECTDIR=%cd%

REM Set PYTHONPATH to include the project root
set PYTHONPATH=%PROJECTDIR%;%PYTHONPATH%

echo ================================
echo SupplySense Backend API Startup
echo ================================
echo.
echo Project Directory: %PROJECTDIR%
echo Python Path: %PYTHONPATH%
echo.

REM Run the Python script with proper path setup
python -c "import sys; sys.path.insert(0, r'%PROJECTDIR%'); exec(open('start_api.py').read())"

pause
