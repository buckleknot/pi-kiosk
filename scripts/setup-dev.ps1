# One-time Windows dev setup: creates .venv, installs deps, initialises git.
# Usage (from the repo root):  powershell -ExecutionPolicy Bypass -File scripts\setup-dev.ps1
$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)

# Prefer Python 3.13 to match Raspberry Pi OS (trixie); fall back to newest installed.
$py = $null
foreach ($v in "-3.13", "-3.12", "-3.11", "-3") {
    try { & py $v --version *> $null; if ($LASTEXITCODE -eq 0) { $py = $v; break } } catch {}
}
if (-not $py) { throw "Python not found. Install Python 3.13 from python.org (tick 'py launcher')." }
Write-Host "Using: py $py ($(& py $py --version))"

if (-not (Test-Path .venv)) { & py $py -m venv .venv }
& .\.venv\Scripts\python.exe -m pip install --upgrade pip
& .\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
& .\.venv\Scripts\python.exe -m pip install -e .

if (-not (Test-Path .git)) {
    git init -b main
    git add -A
    git commit -m "Initial pi-kiosk scaffold"
}

Write-Host "`nDone. Next:" -ForegroundColor Green
Write-Host "  .\.venv\Scripts\Activate.ps1"
Write-Host "  python -m pi_kiosk --reload     # 800x480 window with QML hot reload"
Write-Host "  pytest                          # run tests"
