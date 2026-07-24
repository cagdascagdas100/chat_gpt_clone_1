@echo off
setlocal EnableExtensions
set "PORTABLE_ROOT=%~dp0"
set "LAUNCHER=%PORTABLE_ROOT%RUN_AAYS_ADAPTIVE_5_WORKER.ps1"
if not exist "%LAUNCHER%" (
  echo COORDINATOR_LAUNCHER_MISSING: %LAUNCHER%
  exit /b 1
)
"%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -ExecutionPolicy Bypass -File "%LAUNCHER%" -Action Start
exit /b %ERRORLEVEL%
