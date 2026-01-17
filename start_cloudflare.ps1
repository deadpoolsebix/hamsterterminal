# 💀 PSYCHIATRYK SWIZARLAND - SEKTA LIKWIDACYJNA 💀
# Using Cloudflare Tunnel (cloudflared) - BEST FOR 24/7

Write-Host "💀 PSYCHIATRYK SWIZARLAND - SEKTA LIKWIDACYJNA 💀" -ForegroundColor Cyan
Write-Host "Starting Online Dashboard with Cloudflare Tunnel..." -ForegroundColor Green
Write-Host ""

# Cloudflared path
$cloudflaredPath = "C:\Users\sebas\Desktop\finalbot\cloudflared.exe"

# Download cloudflared if not present
if (-not (Test-Path $cloudflaredPath)) {
    Write-Host "📥 Downloading Cloudflare Tunnel..." -ForegroundColor Yellow
    
    $downloadUrl = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe"
    
    try {
        Invoke-WebRequest -Uri $downloadUrl -OutFile $cloudflaredPath
        Write-Host "✅ Cloudflare Tunnel downloaded!" -ForegroundColor Green
    } catch {
        Write-Host "❌ Failed to download: $_" -ForegroundColor Red
        exit 1
    }
}

# Start HTTP server in background
Write-Host "Starting HTTP server on port 8000..." -ForegroundColor Cyan
$serverJob = Start-Job -ScriptBlock {
    Set-Location "C:\Users\sebas\Desktop\finalbot"
    & python -m http.server 8000
}

Start-Sleep -Seconds 2

Write-Host "Creating Cloudflare Tunnel..." -ForegroundColor Cyan
Write-Host "🔗 Your public URL will appear below:" -ForegroundColor Green
Write-Host "💡 This URL works from anywhere in the world!" -ForegroundColor Yellow
Write-Host "⚡ No account needed - 100% FREE!" -ForegroundColor Green
Write-Host ""

# Start cloudflared tunnel
& $cloudflaredPath tunnel --url http://localhost:8000

# Cleanup on exit
Write-Host ""
Write-Host "Stopping server..." -ForegroundColor Yellow
Stop-Job $serverJob
Remove-Job $serverJob
