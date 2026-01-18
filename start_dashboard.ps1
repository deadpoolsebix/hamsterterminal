<#
 Start the professional dashboard (HTML + API) with automatic venv + port selection
 Priority: .venv-7, fallback: .venv-6
 Port: try 8080, fallback to 8081 if busy
#>

$ErrorActionPreference = 'Stop'

function Get-PythonPath {
    $candidates = @(
        (Join-Path $PSScriptRoot ".venv-7\Scripts\python.exe")
        (Join-Path $PSScriptRoot ".venv-6\Scripts\python.exe")
    )
    foreach ($p in $candidates) {
        if (Test-Path $p) { return $p }
    }
    throw "Nie znaleziono venv (.venv-7 ani .venv-6). Zainstaluj wirtualne środowisko."
}

function Get-FreePort {
    param($preferred = 8080, $alternate = 8081)
    $preferredInUse = Test-NetConnection -ComputerName localhost -Port $preferred -WarningAction SilentlyContinue
    if (-not $preferredInUse.TcpTestSucceeded) { return $preferred }
    $altInUse = Test-NetConnection -ComputerName localhost -Port $alternate -WarningAction SilentlyContinue
    if (-not $altInUse.TcpTestSucceeded) { return $alternate }
    throw "Brak wolnych portów (8080 i 8081 zajęte)."
}

$python = Get-PythonPath
$port = Get-FreePort

Write-Host "[START] Dashboard Server" -ForegroundColor Cyan
Write-Host "  Python: $python" -ForegroundColor DarkGray
Write-Host "  Port:   http://localhost:$port" -ForegroundColor DarkGray

$env:PORT = "$port"

# Start Flask server (blocking)
& $python "$PSScriptRoot\run_dashboard.py"
