# 🚀 HAMSTER TERMINAL - WebSocket API Server Launcher
# Professional Real-Time Data Streaming

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "================================================================================`n" -ForegroundColor Yellow
Write-Host "🚀 HAMSTER TERMINAL API SERVER v3.0 - WebSocket Edition`n" -ForegroundColor Green
Write-Host "================================================================================`n" -ForegroundColor Yellow

Write-Host "📋 Startup Checklist:"
Write-Host "  [1] Twelve Data API key"
Write-Host "  [2] WebSocket server"
Write-Host "  [3] Real-time price streaming"
Write-Host "  [4] Dashboard integration`n"

# Check if Python is installed
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✅ Python found: $pythonVersion`n" -ForegroundColor Green
} catch {
    Write-Host "❌ ERROR: Python not installed or not in PATH" -ForegroundColor Red
    Write-Host "   Fix: Add Python to PATH or use full path`n"
    exit 1
}

# Check if virtual environment exists
$venvPath = ".venv-8"
if (-not (Test-Path "$venvPath\Scripts\Activate.ps1")) {
    Write-Host "⚠️ Virtual environment not found" -ForegroundColor Yellow
    Write-Host "   Creating $venvPath...`n"
    python -m venv $venvPath
    Write-Host "✅ Virtual environment created`n" -ForegroundColor Green
}

Write-Host "📦 Installing/checking requirements...`n"

# Activate venv
& "$venvPath\Scripts\Activate.ps1"

# Install requirements
pip install -q -r requirements.txt

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to install requirements" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Requirements installed`n" -ForegroundColor Green

# Check Twelve Data API Key
$apiKey = $env:TWELVE_DATA_API_KEY
if ([string]::IsNullOrEmpty($apiKey)) {
    Write-Host "⚠️ TWELVE_DATA_API_KEY environment variable not set" -ForegroundColor Yellow
    Write-Host "   Using demo key (limited to 800 calls/min)`n"
    Write-Host "   To set production API key:" -ForegroundColor Cyan
    Write-Host '   $env:TWELVE_DATA_API_KEY = "your_key_here"' -ForegroundColor Gray
    Write-Host "   Or: `setx TWELVE_DATA_API_KEY your_key_here`n`n"
} else {
    Write-Host "✅ Twelve Data API key configured`n" -ForegroundColor Green
}

Write-Host "================================================================================`n" -ForegroundColor Yellow
Write-Host "🌐 Starting WebSocket Server...`n" -ForegroundColor Green
Write-Host "================================================================================`n" -ForegroundColor Yellow

Write-Host "📡 Server Configuration:"
Write-Host "   Host: 0.0.0.0"
Write-Host "   Port: 5000"
Write-Host "   Protocol: WebSocket + REST API"
Write-Host "   Data Source: Twelve Data (crypto, stocks, forex)`n"

Write-Host "🎯 Access points:"
Write-Host "   REST API:      http://localhost:5000/api/status" -ForegroundColor Cyan
Write-Host "   WebSocket:     ws://localhost:5000/socket.io" -ForegroundColor Cyan
Write-Host "   Dashboard:     http://localhost:8000/professional_websocket_dashboard.html`n" -ForegroundColor Cyan

Write-Host "📊 Real-time symbols:"
Write-Host "   Crypto:  BTC/USD, ETH/USD"
Write-Host "   Stocks:  AAPL, MSFT, NVDA, SPY"
Write-Host "   Forex:   EUR/USD, GBP/USD`n"

Write-Host "⌨️  Commands:"
Write-Host "   Ctrl+C = Stop server"
Write-Host "   Check logs below for errors`n"

Write-Host "================================================================================`n" -ForegroundColor Yellow

# Run the server
try {
    python api_server.py
} catch {
    Write-Host "❌ Server error: $_" -ForegroundColor Red
    exit 1
}
