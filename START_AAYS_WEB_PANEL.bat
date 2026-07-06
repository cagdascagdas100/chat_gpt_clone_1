@echo off
setlocal
set "ROOT=%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%ROOT%START_AAYS_WEB_PANEL.ps1"
endlocal
