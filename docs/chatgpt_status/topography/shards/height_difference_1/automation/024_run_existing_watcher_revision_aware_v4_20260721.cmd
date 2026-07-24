@echo off
setlocal
set "REPO=F:\chatgpt\chat_gpt_clone_1_main"
set "RECOVERY=%REPO%\docs\chatgpt_status\topography\shards\height_difference_1\automation\022_recover_existing_watcher_revision_aware_v4_20260721.ps1"
set "VERIFY=%REPO%\docs\chatgpt_status\topography\shards\height_difference_1\automation\023_verify_existing_watcher_revision_aware_v4_20260721.ps1"

powershell -NoProfile -ExecutionPolicy Bypass -File "%RECOVERY%"
if errorlevel 1 exit /b %errorlevel%

powershell -NoProfile -ExecutionPolicy Bypass -File "%RECOVERY%" -Apply -RestoreRunner
if errorlevel 1 exit /b %errorlevel%

powershell -NoProfile -ExecutionPolicy Bypass -File "%VERIFY%" -WaitSeconds 180 -PollSeconds 5
exit /b %errorlevel%
