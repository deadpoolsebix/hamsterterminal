@echo off
cd /d "%~dp0"

echo ========================================
echo  HAMSTER TERMINAL - FULL STACK SERVER
echo ========================================
echo.

REM Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python not installed!
    pause
    exit /b 1
)

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt --quiet

REM Clear old processes
taskkill /F /IM python.exe >nul 2>&1

echo.
echo Starting servers...
echo.

REM Start Flask API on 5000
echo [1/2] Starting API Server on port 5000...
start "Hamster API" cmd /k "python app.py"

REM Wait for API to start
timeout /t 2 /nobreak

REM Start HTTP Server on 8000
echo [2/2] Starting HTTP Server on port 8000...
start "Hamster Dashboard" cmd /k "python -m http.server 8000"

echo.
echo ========================================
echo    SERVERS RUNNING
echo ========================================
echo.
echo Dashboard: http://localhost:8000
echo API: http://localhost:5000/api/prices
echo.
echo Prices auto-updating every 30 seconds
echo.
timeout /t 3 /nobreak
start http://localhost:8000
