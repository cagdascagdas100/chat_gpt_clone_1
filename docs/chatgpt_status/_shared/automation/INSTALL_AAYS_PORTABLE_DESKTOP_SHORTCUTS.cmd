@echo off
setlocal EnableExtensions
chcp 65001 >nul
set "HERE=%~dp0"
"%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -ExecutionPolicy Bypass -File "%HERE%INSTALL_AAYS_PORTABLE_DESKTOP_SHORTCUTS.ps1"
set "RC=%ERRORLEVEL%"
if "%RC%"=="0" (
  echo.
  echo AAYS kisayollari bu bilgisayarin masaustune kuruldu.
) else (
  echo.
  echo Kisayol kurulumu basarisiz oldu.
)
pause
exit /b %RC%

