@echo off
setlocal EnableExtensions
set "ROOT=%~dp0"
"%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -ExecutionPolicy Bypass -File "%ROOT%RUN_AAYS_ADAPTIVE_18_SLOT.ps1" -Action Start
exit /b %ERRORLEVEL%
