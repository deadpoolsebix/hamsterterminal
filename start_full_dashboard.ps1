# 🚀 HAMSTER TERMINAL - Quick Start Script
# Uruchamia API server + HTML dashboard automatycznie

Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host "🚀 HAMSTER TERMINAL - FULL STACK LAUNCHER" -ForegroundColor Yellow
Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host ""

$folder = "C:\Users\sebas\Desktop\finalbot"
Set-Location $folder

# Sprawdź czy Python jest dostępny
Write-Host "📦 Checking Python..." -ForegroundColor Cyan
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✅ Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python not found! Install Python first." -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit
}

# Sprawdź wymagane pakiety
Write-Host "📦 Checking required packages..." -ForegroundColor Cyan
$packages = @("flask", "flask-cors", "requests")
$missing = @()

foreach ($pkg in $packages) {
    $check = pip show $pkg 2>$null
    if ($?) {
        Write-Host "  ✅ $pkg installed" -ForegroundColor Green
    } else {
        Write-Host "  ❌ $pkg missing" -ForegroundColor Red
        $missing += $pkg
    }
}

if ($missing.Count -gt 0) {
    Write-Host ""
    Write-Host "📥 Installing missing packages..." -ForegroundColor Yellow
    pip install $($missing -join " ") --quiet
    Write-Host "✅ Packages installed!" -ForegroundColor Green
}

Write-Host ""
Write-Host "🔥 Starting services..." -ForegroundColor Cyan
Write-Host ""

# Uruchom API Server w nowym oknie (minimized)
Write-Host "  1️⃣  Starting API Server (port 5000)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$folder'; Write-Host '🚀 API SERVER RUNNING' -ForegroundColor Green; python api_server.py" -WindowStyle Minimized
Start-Sleep -Seconds 3

# Uruchom HTTP Server w nowym oknie (minimized)
Write-Host "  2️⃣  Starting HTTP Server (port 8000)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$folder'; Write-Host '🌐 HTTP SERVER RUNNING' -ForegroundColor Green; python -m http.server 8000" -WindowStyle Minimized
Start-Sleep -Seconds 2

# Test API
Write-Host ""
Write-Host "🧪 Testing API..." -ForegroundColor Cyan
Start-Sleep -Seconds 3
try {
    $response = curl.exe http://127.0.0.1:5000/api/status 2>$null | ConvertFrom-Json
    if ($response.ok) {
        Write-Host "  ✅ API Status: RUNNING" -ForegroundColor Green
        Write-Host "  📊 BTC Price: `$$($response.cache.btcPrice)" -ForegroundColor Yellow
        Write-Host "  📊 ETH Price: `$$($response.cache.ethPrice)" -ForegroundColor Yellow
        Write-Host "  😱 Fear & Greed: $($response.cache.fearGreed)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "  ⚠️  API still starting..." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host "✅ DASHBOARD READY!" -ForegroundColor Green
Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host ""
Write-Host "🌐 Open in browser:" -ForegroundColor Cyan
Write-Host "   http://localhost:8000/professional_dashboard_final.html" -ForegroundColor White
Write-Host ""
Write-Host "📡 API Server:" -ForegroundColor Cyan
Write-Host "   http://localhost:5000/api/status" -ForegroundColor White
Write-Host ""
Write-Host "💡 Both servers are running in minimized windows" -ForegroundColor Yellow
Write-Host "   To stop: Close PowerShell windows or use Task Manager" -ForegroundColor Yellow
Write-Host ""

# Pytaj czy otworzyć przeglądarkę
$open = Read-Host "Open dashboard in browser now? (Y/n)"
if ($open -eq "" -or $open -eq "Y" -or $open -eq "y") {
    Start-Process "http://localhost:8000/professional_dashboard_final.html"
    Write-Host "🚀 Dashboard opened!" -ForegroundColor Green
}

Write-Host ""
Write-Host "Press Enter to exit this window (servers will keep running)..." -ForegroundColor Gray
Read-Host
