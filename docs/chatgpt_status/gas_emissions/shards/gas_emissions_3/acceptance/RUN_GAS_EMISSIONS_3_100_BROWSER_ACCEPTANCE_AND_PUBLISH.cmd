@echo off
setlocal EnableExtensions

if "%AAYS_REPO_ROOT%"=="" (
  echo ERROR: AAYS_REPO_ROOT is not set to the existing canonical F shared-runner worktree.
  exit /b 10
)

set "WRAPPER=%~dp0publish_gas_emissions_3_100_browser_proof_v5.ps1"
if not exist "%WRAPPER%" (
  echo ERROR: V5 browser proof wrapper not found: %WRAPPER%
  exit /b 11
)

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%WRAPPER%" -RepoRoot "%AAYS_REPO_ROOT%" -Branch "codex/aays-single-runner-v5-20260706"
set "RC=%ERRORLEVEL%"
if not "%RC%"=="0" (
  echo GAS_EMISSIONS_3_BROWSER_ACCEPTANCE_V5_FAILED RC=%RC%
  exit /b %RC%
)

echo GAS_EMISSIONS_3_BROWSER_ACCEPTANCE_V5_SCREENSHOT_DURABLE_REMOTE_READBACK_COMPLETE
exit /b 0
