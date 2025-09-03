@echo off
title BID Artwork Downloader v3.5.6
color 0A

echo.
echo ==========================================
echo    BID ARTWORK DOWNLOADER v3.5.6
echo ==========================================
echo.

REM Change to script directory
cd /d "%~dp0"

REM Check if smart_app.py exists
if not exist "smart_app.py" (
    echo ERROR: smart_app.py not found!
    echo Please make sure you are in the correct directory.
    pause
    exit /b 1
)

REM Stop any existing Python processes
echo Stopping existing Python processes...
taskkill /f /im python.exe >nul 2>&1
taskkill /f /im py.exe >nul 2>&1

echo.
echo Starting BID Web Application...
echo.
echo Server URL: http://localhost:5002
echo Browser will open automatically in 3 seconds...
echo.
echo Press Ctrl+C to stop the server
echo.

REM Start the Flask app
start /b py smart_app.py

REM Wait for server to start
timeout /t 3 /nobreak >nul

REM Open browser
echo Opening browser...
start "" "http://localhost:5002" >nul 2>&1

echo.
echo ==========================================
echo  WEB APPLICATION IS RUNNING!
echo  URL: http://localhost:5002
echo  Version: 3.5.6 (Latest with fixes)
echo  Press any key to stop the server...
echo ==========================================
pause >nul

REM Stop the server
taskkill /f /im python.exe >nul 2>&1
taskkill /f /im py.exe >nul 2>&1

echo.
echo Server stopped.
echo Press any key to exit...
pause >nul
