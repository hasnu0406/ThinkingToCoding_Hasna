@echo off
setlocal

set "PROJECT_ROOT=%~dp0"
set "PYTHON_EXE=%PROJECT_ROOT%.venv\Scripts\python.exe"

if not exist "%PYTHON_EXE%" (
  echo Python virtual environment not found at .venv\Scripts\python.exe
  exit /b 1
)

cd /d "%PROJECT_ROOT%"
"%PYTHON_EXE%" main.py
