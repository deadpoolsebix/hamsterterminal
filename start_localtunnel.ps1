# 💀 PSYCHIATRYK SWIZARLAND - SEKTA LIKWIDACYJNA 💀
# Alternative: Using LocalTunnel (requires Node.js)

Write-Host "💀 PSYCHIATRYK SWIZARLAND - SEKTA LIKWIDACYJNA 💀" -ForegroundColor Cyan
Write-Host "Starting Online Dashboard with LocalTunnel..." -ForegroundColor Green
Write-Host ""

# Check if Node.js is installed
try {
    $nodeVersion = node --version 2>&1
    Write-Host "✅ Node.js detected: $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Node.js not found!" -ForegroundColor Red
    Write-Host "Please install from: https://nodejs.org" -ForegroundColor Yellow
    exit 1
}

# Install localtunnel if not present
Write-Host "📦 Checking localtunnel..." -ForegroundColor Cyan
try {
    $ltCheck = npm list -g localtunnel 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "📥 Installing localtunnel..." -ForegroundColor Yellow
        npm install -g localtunnel
    }
} catch {
    Write-Host "📥 Installing localtunnel..." -ForegroundColor Yellow
    npm install -g localtunnel
}

# Start HTTP server in background
Write-Host "🚀 Starting HTTP server on port 8000..." -ForegroundColor Cyan
$serverJob = Start-Job -ScriptBlock {
    Set-Location "C:\Users\sebas\Desktop\finalbot"
    python -m http.server 8000
}

Start-Sleep -Seconds 2

# Start localtunnel
Write-Host "🌐 Creating public tunnel..." -ForegroundColor Cyan
Write-Host ""
Write-Host "🔗 Your dashboard will be accessible at the URL shown below" -ForegroundColor Green
Write-Host "💡 Keep this window open to maintain the connection" -ForegroundColor Yellow
Write-Host ""

# Generate subdomain based on current time for consistency
$subdomain = "psychiatryk-swizarland-" + (Get-Date -Format "HHmm")

npx localtunnel --port 8000 --subdomain $subdomain

# Cleanup on exit
Write-Host "Stopping server..." -ForegroundColor Yellow
Stop-Job $serverJob
Remove-Job $serverJob
