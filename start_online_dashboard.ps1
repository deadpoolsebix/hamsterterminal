# 💀 PSYCHIATRYK SWIZARLAND - SEKTA LIKWIDACYJNA 💀
# Online Dashboard Launcher with ngrok

Write-Host "💀 PSYCHIATRYK SWIZARLAND - SEKTA LIKWIDACYJNA 💀" -ForegroundColor Cyan
Write-Host "Starting Online Dashboard Server..." -ForegroundColor Green
Write-Host ""

# Check if ngrok is installed
$ngrokPath = "C:\Users\sebas\Desktop\finalbot\ngrok.exe"

if (-not (Test-Path $ngrokPath)) {
    Write-Host "📥 Downloading ngrok..." -ForegroundColor Yellow
    
    # Download ngrok
    $ngrokUrl = "https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-windows-amd64.zip"
    $zipPath = "C:\Users\sebas\Desktop\finalbot\ngrok.zip"
    
    try {
        Invoke-WebRequest -Uri $ngrokUrl -OutFile $zipPath
        
        # Extract ngrok
        Expand-Archive -Path $zipPath -DestinationPath "C:\Users\sebas\Desktop\finalbot" -Force
        Remove-Item $zipPath
        
        Write-Host "✅ ngrok downloaded successfully!" -ForegroundColor Green
    } catch {
        Write-Host "❌ Failed to download ngrok: $_" -ForegroundColor Red
        Write-Host "Please download manually from: https://ngrok.com/download" -ForegroundColor Yellow
        exit 1
    }
}

# Start HTTP server in background
Write-Host "🚀 Starting HTTP server on port 8000..." -ForegroundColor Cyan
$serverJob = Start-Job -ScriptBlock {
    Set-Location "C:\Users\sebas\Desktop\finalbot"
    python -m http.server 8000
}

Start-Sleep -Seconds 2

# Start ngrok tunnel
Write-Host "🌐 Creating ngrok tunnel..." -ForegroundColor Cyan
Write-Host ""
Write-Host "⚠️  IMPORTANT: For 24/7 access, create free ngrok account at https://ngrok.com" -ForegroundColor Yellow
Write-Host "Then run: .\ngrok.exe config add-authtoken YOUR_TOKEN" -ForegroundColor Yellow
Write-Host ""

# Start ngrok
& $ngrokPath http 8000 --log=stdout

# Cleanup on exit
Write-Host "Stopping server..." -ForegroundColor Yellow
Stop-Job $serverJob
Remove-Job $serverJob
