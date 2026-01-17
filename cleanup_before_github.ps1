# Skrypt czyszczący projekt przed wysłaniem na GitHub
# Usuwa zbędne pliki, które zajmują miejsce

Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "🧹 Czyszczenie projektu przed GitHub" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

$filesDeleted = 0
$sizeSaved = 0

# Funkcja do usuwania
function Remove-SafePath {
    param($path, $description)
    
    if (Test-Path $path) {
        $size = (Get-ChildItem $path -Recurse -File | Measure-Object -Property Length -Sum).Sum / 1MB
        Remove-Item $path -Recurse -Force
        Write-Host "[✓] Usunięto: $description ($([math]::Round($size, 2)) MB)" -ForegroundColor Green
        $script:sizeSaved += $size
        $script:filesDeleted++
    } else {
        Write-Host "[i] Pominięto: $description (nie znaleziono)" -ForegroundColor Yellow
    }
}

# Usuń virtual environments
Write-Host "Usuwam virtual environments..." -ForegroundColor Yellow
Remove-SafePath ".venv" "Virtual environment (.venv)"
Remove-SafePath ".venv-6" "Virtual environment (.venv-6)"
Remove-SafePath "venv" "Virtual environment (venv)"
Remove-SafePath "env" "Virtual environment (env)"

# Usuń cache Pythona
Write-Host ""
Write-Host "Usuwam cache Pythona..." -ForegroundColor Yellow
Get-ChildItem -Path . -Recurse -Filter "__pycache__" | ForEach-Object {
    Remove-SafePath $_.FullName "Python cache: $($_.FullName)"
}

Get-ChildItem -Path . -Recurse -Filter "*.pyc" | ForEach-Object {
    Remove-Item $_.FullName -Force
    Write-Host "[✓] Usunięto: $($_.Name)" -ForegroundColor Green
}

# Usuń pliki tymczasowe
Write-Host ""
Write-Host "Usuwam pliki tymczasowe..." -ForegroundColor Yellow
Remove-SafePath "logs" "Logi"
Remove-SafePath "*.log" "Pliki log"

# Usuń dane tradingowe (opcjonalne)
Write-Host ""
$response = Read-Host "Czy usunąć pliki CSV z danymi tradingowymi? (t/n)"
if ($response -eq "t" -or $response -eq "T") {
    Get-ChildItem -Path . -Filter "bot_trades_*.csv" | ForEach-Object {
        Remove-Item $_.FullName -Force
        Write-Host "[✓] Usunięto: $($_.Name)" -ForegroundColor Green
    }
}

# Usuń screenshoty (opcjonalne)
$response = Read-Host "Czy usunąć folder ze screenshotami? (t/n)"
if ($response -eq "t" -or $response -eq "T") {
    Remove-SafePath "dashboard_screenshots" "Screenshoty dashboardu"
}

# Podsumowanie
Write-Host ""
Write-Host "=====================================" -ForegroundColor Green
Write-Host "✨ Czyszczenie zakończone!" -ForegroundColor Green
Write-Host "=====================================" -ForegroundColor Green
Write-Host "Elementów usuniętych: $filesDeleted" -ForegroundColor White
Write-Host "Zaoszczędzone miejsce: ~$([math]::Round($sizeSaved, 2)) MB" -ForegroundColor White
Write-Host ""
Write-Host "📦 Projekt gotowy do uploadu na GitHub!" -ForegroundColor Cyan
Write-Host ""
Write-Host "Następne kroki:" -ForegroundColor Yellow
Write-Host "1. Otwórz GitHub Desktop lub git bash" -ForegroundColor White
Write-Host "2. Uruchom: .\push_to_github.ps1 (jeśli masz git)" -ForegroundColor White
Write-Host "3. LUB zobacz: GITHUB_DESKTOP_GUIDE.md" -ForegroundColor White
Write-Host "=====================================" -ForegroundColor Green
