@echo off
echo Starting Dashboard Server...
echo.
cd /d "%~dp0"
.venv-7\Scripts\python.exe run_dashboard.py
pause
