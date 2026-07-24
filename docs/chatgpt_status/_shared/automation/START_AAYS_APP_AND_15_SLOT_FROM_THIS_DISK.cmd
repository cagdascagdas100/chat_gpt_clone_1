@echo off
setlocal EnableExtensions
set "ROOT=%~dp0"
"%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -ExecutionPolicy Bypass -File "%ROOT%START_AAYS_APP_AND_15_SLOT_FROM_THIS_DISK.ps1"
if errorlevel 1 pause
exit /b %ERRORLEVEL%
