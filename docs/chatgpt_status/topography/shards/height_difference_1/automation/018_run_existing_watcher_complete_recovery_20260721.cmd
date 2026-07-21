@echo off
setlocal EnableExtensions
set "REPO=F:\chatgpt\chat_gpt_clone_1_main"
set "RECOVERY=%REPO%\docs\chatgpt_status\topography\shards\height_difference_1\automation\016_recover_existing_watcher_complete_task_assets_20260721.ps1"
set "VERIFY=%REPO%\docs\chatgpt_status\topography\shards\height_difference_1\automation\017_verify_existing_watcher_complete_recovery_20260721.ps1"

if not exist "%RECOVERY%" (
  echo RECOVERY_SCRIPT_MISSING=%RECOVERY%
  exit /b 2
)
if not exist "%VERIFY%" (
  echo VERIFIER_SCRIPT_MISSING=%VERIFY%
  exit /b 2
)

powershell -NoProfile -ExecutionPolicy Bypass -File "%RECOVERY%" -Apply -RestoreRunner
if errorlevel 1 exit /b %errorlevel%

powershell -NoProfile -ExecutionPolicy Bypass -File "%VERIFY%" -WaitSeconds 120 -PollSeconds 5
exit /b %errorlevel%
