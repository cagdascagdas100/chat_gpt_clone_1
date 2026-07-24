@echo off
setlocal EnableExtensions
chcp 65001 >nul
set "HERE=%~dp0"
set "SCRIPT=%HERE%START_AAYS_ON_ANY_WINDOWS_PC.ps1"
if not exist "%SCRIPT%" (
  echo AAYS portable baslatma dosyasi bulunamadi: "%SCRIPT%"
  pause
  exit /b 1
)
"%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT%"
set "RC=%ERRORLEVEL%"
if not "%RC%"=="0" (
  echo.
  echo Baslatma tamamlanamadi. Ayrinti: state\portable_any_pc_bootstrap_latest.json
  pause
)
exit /b %RC%

