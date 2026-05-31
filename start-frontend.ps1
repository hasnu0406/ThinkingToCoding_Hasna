$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$frontendRoot = Join-Path $projectRoot "frontend"

if (-not (Test-Path $frontendRoot)) {
    Write-Error "Frontend folder not found."
}

Set-Location $frontendRoot
npm start
