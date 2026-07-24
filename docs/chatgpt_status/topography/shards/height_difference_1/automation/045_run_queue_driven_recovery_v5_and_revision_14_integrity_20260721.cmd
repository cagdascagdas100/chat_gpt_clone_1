@echo off
setlocal EnableExtensions
set "REPO=F:\chatgpt\chat_gpt_clone_1_main"
set "AAYS_REPO_ROOT=%REPO%"
set "RECOVERY=%REPO%\docs\chatgpt_status\topography\shards\height_difference_1\automation\029_recover_existing_watcher_queue_driven_v5_20260721.ps1"
set "VERIFY=%REPO%\docs\chatgpt_status\topography\shards\height_difference_1\automation\030_verify_existing_watcher_queue_driven_v5_20260721.ps1"
set "INTEGRITY=%REPO%\docs\chatgpt_status\topography\shards\height_difference_1\automation\044_validate_revision_14_output_integrity_entry_20260721.py"
set "OUTPUT=%REPO%\docs\chatgpt_status\topography\shards\height_difference_1\runner_outputs\016_revision_14_direct_hmlr_monthly_gml_refresh_latest.json"

powershell -NoProfile -ExecutionPolicy Bypass -File "%RECOVERY%" -Apply %*
if errorlevel 1 exit /b %errorlevel%

powershell -NoProfile -ExecutionPolicy Bypass -Command "$deadline=(Get-Date).AddSeconds(180); while((Get-Date)-lt$deadline -and -not(Test-Path -LiteralPath '%OUTPUT%')){Start-Sleep -Seconds 5}"
if exist "%OUTPUT%" (
  python "%INTEGRITY%"
  if errorlevel 1 exit /b %errorlevel%
)

powershell -NoProfile -ExecutionPolicy Bypass -File "%VERIFY%" -WaitSeconds 30 -PollSeconds 5
exit /b %errorlevel%
