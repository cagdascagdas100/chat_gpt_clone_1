@echo off
setlocal
chcp 65001 >nul
set "ROOT=%~dp0"
set "TEMP=%ROOT%runtime\tmp"
set "TMP=%ROOT%runtime\tmp"
set "HOME=%ROOT%runtime\home"
set "PYTHONNOUSERSITE=1"
set "PYTHONUSERBASE=%ROOT%runtime\python-user"
set "PYTHONPYCACHEPREFIX=%ROOT%runtime\pycache"
set "PIP_CACHE_DIR=%ROOT%runtime\cache\pip"
set "UV_CACHE_DIR=%ROOT%runtime\cache\uv"
set "XDG_CACHE_HOME=%ROOT%runtime\cache\xdg"
set "MPLCONFIGDIR=%ROOT%runtime\cache\matplotlib"
set "NUMBA_CACHE_DIR=%ROOT%runtime\cache\numba"
set "JOBLIB_TEMP_FOLDER=%ROOT%runtime\tmp\joblib"
set "HF_HOME=%ROOT%runtime\cache\huggingface"
set "TORCH_HOME=%ROOT%runtime\cache\torch"
set "PLAYWRIGHT_BROWSERS_PATH=%ROOT%runtime\playwright-browsers"
if not exist "%TEMP%" mkdir "%TEMP%"
if not exist "%HOME%" mkdir "%HOME%"
if not exist "%PYTHONUSERBASE%" mkdir "%PYTHONUSERBASE%"
if not exist "%PYTHONPYCACHEPREFIX%" mkdir "%PYTHONPYCACHEPREFIX%"
if not exist "%ROOT%runtime\cache" mkdir "%ROOT%runtime\cache"
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
