@echo off
setlocal
set "REPO_ROOT=F:\chatgpt\chat_gpt_clone_1_main"
set "RECOVERY=%~dp0022_recover_existing_watcher_revision_aware_v4_20260721.ps1"
set "VERIFY=%~dp0023_verify_existing_watcher_revision_aware_v4_20260721.ps1"
set "INTEGRITY=%~dp0025_validate_revision_9_output_integrity_20260721.py"

powershell -NoProfile -ExecutionPolicy Bypass -File "%RECOVERY%" -Apply -RestoreRunner
if errorlevel 1 exit /b %errorlevel%

powershell -NoProfile -ExecutionPolicy Bypass -File "%VERIFY%" -WaitSeconds 180 -PollSeconds 5
if errorlevel 1 exit /b %errorlevel%

python "%INTEGRITY%" --repo-root "%REPO_ROOT%"
exit /b %errorlevel%
