@echo off
REM 🚀 HAMSTER TERMINAL - WebSocket API Server Launcher
REM Professional Real-Time Data Streaming

title Hamster Terminal API Server v3.0 - WebSocket

cls
echo.
echo ================================================================================
echo 🚀 HAMSTER TERMINAL API SERVER v3.0 - WebSocket Edition
echo ================================================================================
echo.
echo 📋 Startup Checklist:
echo  [1] Twelve Data API key
echo  [2] WebSocket server
echo  [3] Real-time price streaming
echo  [4] Dashboard integration
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ ERROR: Python not installed or not in PATH
    echo   Fix: Add Python to PATH or use full path
    pause
    exit /b 1
)

echo ✅ Python found
echo.

REM Check if virtual environment exists
if not exist ".venv-8\Scripts\Activate.ps1" (
    echo ⚠️ Virtual environment not found
    echo   Creating .venv-8...
    python -m venv .venv-8
    echo ✅ Virtual environment created
)

echo.
echo 📦 Installing/checking requirements...
echo.

REM Activate venv and install requirements
call .venv-8\Scripts\activate.bat
pip install -q -r requirements.txt

if %errorlevel% neq 0 (
    echo ❌ Failed to install requirements
    pause
    exit /b 1
)

echo ✅ Requirements installed
echo.

REM Check Twelve Data API Key
if "%TWELVE_DATA_API_KEY%"=="" (
    echo ⚠️  TWELVE_DATA_API_KEY environment variable not set
    echo   Using demo key (limited to 800 calls/min)
    echo.
    echo   To set production API key:
    echo   setx TWELVE_DATA_API_KEY "your_key_here"
    echo.
) else (
    echo ✅ Twelve Data API key configured
    echo.
)

echo ================================================================================
echo 🌐 Starting WebSocket Server...
echo ================================================================================
echo.
echo 📡 Server Configuration:
echo   Host: 0.0.0.0
echo   Port: 5000
echo   Protocol: WebSocket + REST API
echo   Data Source: Twelve Data (crypto, stocks, forex)
echo.
echo 🎯 Access points:
echo   REST API:      http://localhost:5000/api/status
echo   WebSocket:     ws://localhost:5000/socket.io
echo   Dashboard:     http://localhost:8000/professional_websocket_dashboard.html
echo.
echo 📊 Real-time symbols:
echo   Crypto:  BTC/USD, ETH/USD
echo   Stocks:  AAPL, MSFT, NVDA, SPY
echo   Forex:   EUR/USD, GBP/USD
echo.
echo ⌨️  Commands:
echo   Ctrl+C = Stop server
echo   Check logs below for errors
echo.
echo ================================================================================
echo.

REM Run the server
python api_server.py

REM Error handling
if %errorlevel% neq 0 (
    echo.
    echo ❌ Server crashed with error code %errorlevel%
    echo.
    pause
    exit /b %errorlevel%
)
