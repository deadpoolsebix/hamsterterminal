Write-Host "PSYCHIATRYK SWIZARLAND - SEKTA LIKWIDACYJNA" -ForegroundColor Cyan
Write-Host "Starting Online Dashboard..." -ForegroundColor Green
Write-Host ""

$cloudflaredPath = "$PSScriptRoot\cloudflared.exe"

if (-not (Test-Path $cloudflaredPath)) {
    Write-Host "Downloading Cloudflare Tunnel..." -ForegroundColor Yellow
    $url = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe"
    Invoke-WebRequest -Uri $url -OutFile $cloudflaredPath
    Write-Host "Download complete!" -ForegroundColor Green
}

Write-Host "Starting HTTP server..." -ForegroundColor Cyan
$job = Start-Job { 
    param($path)
    Set-Location $path
    python -m http.server 8000 
} -ArgumentList $PSScriptRoot

Start-Sleep -Seconds 3

Write-Host ""
Write-Host "Creating public tunnel..." -ForegroundColor Cyan
Write-Host "Your URL will appear below:" -ForegroundColor Green
Write-Host ""

& $cloudflaredPath tunnel --url http://localhost:8000

Stop-Job $job
Remove-Job $job
