@echo off
setlocal

set "PROJECT_ROOT=%~dp0"
set "FRONTEND_ROOT=%PROJECT_ROOT%frontend"

if not exist "%FRONTEND_ROOT%" (
  echo Frontend folder not found.
  exit /b 1
)

cd /d "%FRONTEND_ROOT%"
npm.cmd start
