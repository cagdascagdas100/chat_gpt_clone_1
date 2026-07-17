@echo off
setlocal
chcp 65001 >nul
set "ROOT=%~dp0"
set "PYW=%ROOT%runtime\python312\pythonw.exe"
set "PY=%ROOT%runtime\python312\python.exe"
if exist "%PYW%" (
  start "AAYS Portable Panel" "%PYW%" "%ROOT%AAYS_PORTABLE_CONTROL_PANEL.py"
  exit /b 0
)
if exist "%PY%" (
  "%PY%" "%ROOT%AAYS_PORTABLE_CONTROL_PANEL.py"
  exit /b %ERRORLEVEL%
)
where py >nul 2>nul
if not errorlevel 1 (
  start "AAYS Portable Panel" py -3 "%ROOT%AAYS_PORTABLE_CONTROL_PANEL.py"
  exit /b 0
)
where python >nul 2>nul
if not errorlevel 1 (
  python "%ROOT%AAYS_PORTABLE_CONTROL_PANEL.py"
  exit /b %ERRORLEVEL%
)
echo Python bulunamadi. "%ROOT%runtime\python312" veya sistem Python gerekli.
pause
exit /b 1
