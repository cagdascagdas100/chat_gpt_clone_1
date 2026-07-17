@echo off
setlocal
set "ROOT=%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%ROOT%RUN_AAYS_ADAPTIVE_15_WORKER.ps1" -Action Start
exit /b %ERRORLEVEL%