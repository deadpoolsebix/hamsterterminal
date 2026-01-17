# Automatyczny push na GitHub
# Skrypt dla Windows PowerShell

Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "🚀 GitHub Deployment Automation" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

# Sprawdź czy git jest zainstalowany
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Host "[ERROR] Git nie jest zainstalowany!" -ForegroundColor Red
    Write-Host "Pobierz: https://git-scm.com/download/win" -ForegroundColor Yellow
    exit 1
}

Write-Host "[✓] Git jest zainstalowany" -ForegroundColor Green

# Sprawdź czy to już repo git
if (-not (Test-Path .git)) {
    Write-Host ""
    Write-Host "[INFO] Inicjalizuję repozytorium Git..." -ForegroundColor Yellow
    git init
    Write-Host "[✓] Repozytorium Git utworzone" -ForegroundColor Green
} else {
    Write-Host "[✓] Repozytorium Git już istnieje" -ForegroundColor Green
}

# Sprawdź konfigurację Git
$gitUser = git config user.name
$gitEmail = git config user.email

if (-not $gitUser -or -not $gitEmail) {
    Write-Host ""
    Write-Host "[INFO] Konfiguracja Git..." -ForegroundColor Yellow
    $name = Read-Host "Podaj swoją nazwę (np. Jan Kowalski)"
    $email = Read-Host "Podaj swój email GitHub"
    
    git config --global user.name "$name"
    git config --global user.email "$email"
    
    Write-Host "[✓] Git skonfigurowany" -ForegroundColor Green
}

# Sprawdź czy istnieje remote
$remoteUrl = git remote get-url origin 2>$null

if (-not $remoteUrl) {
    Write-Host ""
    Write-Host "=====================================" -ForegroundColor Yellow
    Write-Host "📝 INSTRUKCJA:" -ForegroundColor Yellow
    Write-Host "=====================================" -ForegroundColor Yellow
    Write-Host "1. Wejdź na: https://github.com/new" -ForegroundColor White
    Write-Host "2. Nazwa repo: trading-bot-pro" -ForegroundColor White
    Write-Host "3. Ustaw: Public lub Private" -ForegroundColor White
    Write-Host "4. NIE zaznaczaj 'Initialize with README'" -ForegroundColor White
    Write-Host "5. Kliknij 'Create repository'" -ForegroundColor White
    Write-Host "=====================================" -ForegroundColor Yellow
    Write-Host ""
    
    $repoUrl = Read-Host "Podaj URL swojego repo (np. https://github.com/username/trading-bot-pro.git)"
    
    git remote add origin $repoUrl
    Write-Host "[✓] Remote origin dodany" -ForegroundColor Green
} else {
    Write-Host "[✓] Remote origin już istnieje: $remoteUrl" -ForegroundColor Green
}

# Dodaj wszystkie pliki
Write-Host ""
Write-Host "[INFO] Dodaję pliki do commita..." -ForegroundColor Yellow

git add .

# Sprawdź status
$status = git status --short
if ($status) {
    Write-Host "[✓] Pliki do commita:" -ForegroundColor Green
    Write-Host $status -ForegroundColor Gray
} else {
    Write-Host "[INFO] Brak zmian do commitowania" -ForegroundColor Yellow
}

# Commit
Write-Host ""
$commitMsg = Read-Host "Wpisz opis commita (Enter = domyślny)"
if (-not $commitMsg) {
    $commitMsg = "🚀 Initial commit - Professional Trading Dashboard"
}

git commit -m "$commitMsg"
Write-Host "[✓] Commit utworzony" -ForegroundColor Green

# Sprawdź czy branch main istnieje
$currentBranch = git branch --show-current
if ($currentBranch -ne "main") {
    Write-Host "[INFO] Zmieniam branch na 'main'..." -ForegroundColor Yellow
    git branch -M main
}

# Push
Write-Host ""
Write-Host "[INFO] Wysyłam na GitHub..." -ForegroundColor Yellow
Write-Host "[INFO] Możesz zostać poproszony o logowanie..." -ForegroundColor Yellow

$pushResult = git push -u origin main 2>&1

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "=====================================" -ForegroundColor Green
    Write-Host "✨ SUKCES! Projekt na GitHub!" -ForegroundColor Green
    Write-Host "=====================================" -ForegroundColor Green
    Write-Host ""
    
    $repoUrl = git remote get-url origin
    $webUrl = $repoUrl -replace '\.git$', ''
    
    Write-Host "🌐 Twoje repo: $webUrl" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "📋 Następne kroki:" -ForegroundColor Yellow
    Write-Host "1. Deploy na Railway: railway init && railway up" -ForegroundColor White
    Write-Host "2. Deploy na Render: Połącz repo w dashboard" -ForegroundColor White
    Write-Host "3. Zobacz: DEPLOYMENT_GUIDE.md" -ForegroundColor White
    Write-Host ""
} else {
    Write-Host ""
    Write-Host "[ERROR] Problem z push'em:" -ForegroundColor Red
    Write-Host $pushResult -ForegroundColor Red
    Write-Host ""
    Write-Host "Możliwe rozwiązania:" -ForegroundColor Yellow
    Write-Host "1. Sprawdź czy masz dostęp do repo" -ForegroundColor White
    Write-Host "2. Użyj: git push -u origin main --force (jeśli repo puste)" -ForegroundColor White
    Write-Host "3. Skonfiguruj Personal Access Token:" -ForegroundColor White
    Write-Host "   https://github.com/settings/tokens" -ForegroundColor Cyan
}
