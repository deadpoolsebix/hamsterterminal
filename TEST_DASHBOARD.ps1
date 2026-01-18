# QUICK TEST - Dashboard + API Verification
# Run this after starting START_DASHBOARD.bat

Write-Host "`n=== DASHBOARD VERIFICATION TEST ===" -ForegroundColor Cyan
Write-Host "Testing: http://localhost:8080" -ForegroundColor Yellow

# Test 1: Health check
Write-Host "`n[1/4] Health endpoint..." -NoNewline
try {
    $health = (Invoke-WebRequest -UseBasicParsing http://localhost:8080/health -TimeoutSec 5).Content | ConvertFrom-Json
    if ($health.ok) {
        Write-Host " OK" -ForegroundColor Green
    } else {
        Write-Host " FAILED" -ForegroundColor Red
    }
} catch {
    Write-Host " ERROR: $_" -ForegroundColor Red
    exit 1
}

# Test 2: Commodities API
Write-Host "[2/4] Commodities API (Gold/Silver)..." -NoNewline
try {
    $comm = (Invoke-WebRequest -UseBasicParsing http://localhost:8080/api/commodities -TimeoutSec 10).Content | ConvertFrom-Json
    if ($comm.ok -and $comm.gold -and $comm.silver) {
        Write-Host " OK" -ForegroundColor Green
        Write-Host "      Gold:   `$$($comm.gold.ToString('F2')) (prev: `$$($comm.gold_previous.ToString('F2')))" -ForegroundColor DarkGray
        Write-Host "      Silver: `$$($comm.silver.ToString('F2')) (prev: `$$($comm.silver_previous.ToString('F2')))" -ForegroundColor DarkGray
    } else {
        Write-Host " FAILED: $($comm.error)" -ForegroundColor Red
    }
} catch {
    Write-Host " ERROR: $_" -ForegroundColor Red
}

# Test 3: Dashboard HTML
Write-Host "[3/4] Dashboard HTML..." -NoNewline
try {
    $html = Invoke-WebRequest -UseBasicParsing http://localhost:8080/professional_dashboard_final.html -TimeoutSec 5
    if ($html.StatusCode -eq 200 -and $html.Content.Length -gt 10000) {
        $sizeKB = [math]::Round($html.Content.Length/1024, 1)
        Write-Host " OK ($sizeKB KB)" -ForegroundColor Green
    } else {
        Write-Host " FAILED" -ForegroundColor Red
    }
} catch {
    Write-Host " ERROR: $_" -ForegroundColor Red
}

# Test 4: JavaScript presence
Write-Host "[4/4] JavaScript functions..." -NoNewline
$hasAPI = $html.Content -match "fetchCommoditiesFromServer"
$hasUI = $html.Content -match "updateCommodityDisplay"
if ($hasAPI -and $hasUI) {
    Write-Host " OK" -ForegroundColor Green
} else {
    Write-Host " MISSING" -ForegroundColor Red
}

Write-Host "`n=== SUMMARY ===" -ForegroundColor Cyan
Write-Host "Dashboard URL: " -NoNewline
Write-Host "http://localhost:8080/professional_dashboard_final.html" -ForegroundColor Yellow
Write-Host "`nOpen in browser and check:" -ForegroundColor White
Write-Host "  1. Top ticker shows GOLD and SILVER prices updating" -ForegroundColor Gray
Write-Host "  2. Console log shows: 'Commodity prices fetched from server'" -ForegroundColor Gray
Write-Host "  3. Prices change every 3 seconds" -ForegroundColor Gray

Write-Host "`nPress any key to open in default browser..." -ForegroundColor Cyan
$null = $Host.UI.RawUI.ReadKey('NoEcho,IncludeKeyDown')
Start-Process "http://localhost:8080/professional_dashboard_final.html"
