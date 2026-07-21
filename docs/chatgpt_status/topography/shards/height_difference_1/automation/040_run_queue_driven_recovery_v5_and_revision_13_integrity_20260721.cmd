@echo off
setlocal EnableExtensions
set "REPO=F:\chatgpt\chat_gpt_clone_1_main"
set "RECOVERY=%REPO%\docs\chatgpt_status\topography\shards\height_difference_1\automation\029_recover_existing_watcher_queue_driven_v5_20260721.ps1"
set "VERIFY=%REPO%\docs\chatgpt_status\topography\shards\height_difference_1\automation\030_verify_existing_watcher_queue_driven_v5_20260721.ps1"
set "INTEGRITY=%REPO%\docs\chatgpt_status\topography\shards\height_difference_1\automation\039_validate_revision_13_output_integrity_20260721.py"
set "OUTPUT=%REPO%\docs\chatgpt_status\topography\shards\height_difference_1\runner_outputs\015_revision_13_direct_os_terrain50_crosscheck_latest.json"

powershell -NoProfile -ExecutionPolicy Bypass -File "%RECOVERY%" -Apply %*
if errorlevel 1 exit /b %errorlevel%

powershell -NoProfile -ExecutionPolicy Bypass -Command "$deadline=(Get-Date).AddSeconds(300); while((Get-Date)-lt$deadline -and -not(Test-Path -LiteralPath '%OUTPUT%')){Start-Sleep -Seconds 5}"
if exist "%OUTPUT%" (
  python "%INTEGRITY%" --repo-root "%REPO%"
  if errorlevel 1 exit /b %errorlevel%
)

powershell -NoProfile -ExecutionPolicy Bypass -File "%VERIFY%" -WaitSeconds 30 -PollSeconds 5
exit /b %errorlevel%
