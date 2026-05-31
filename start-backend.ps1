$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$pythonExe = Join-Path $projectRoot ".venv\Scripts\python.exe"

if (-not (Test-Path $pythonExe)) {
    Write-Error "Python virtual environment not found at .venv\Scripts\python.exe"
}

Set-Location $projectRoot
& $pythonExe "main.py"
