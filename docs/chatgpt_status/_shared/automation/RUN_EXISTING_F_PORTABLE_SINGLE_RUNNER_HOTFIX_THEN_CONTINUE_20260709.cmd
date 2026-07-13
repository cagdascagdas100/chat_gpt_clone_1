@echo off
setlocal EnableExtensions

REM AAYS existing F portable single-runner continuation launcher.
REM This does not create a new runner, worktree, queue, DB write, migration, or production deploy.
REM It pulls the active branch once, then keeps the same F-portable runner process polling serially.
REM Up to 8 queue tasks are processed sequentially inside each single-runner scan.

set "AAYS_REPO_ROOT=F:\TerraYield_AAYS_Portable\runner_system\AAYS_WT\AAYS_RUNNER_HEALTHY_20260707"
set "AAYS_WORK_ROOT=F:\TerraYield_AAYS_Portable\runner_system\AAYS_WT\AAYS_STABLE_RUNNER_WORKTREES"
set "AAYS_BRANCH=codex/aays-single-runner-v5-20260706"
set "AAYS_PORTABLE_ROOT=F:\TerraYield_AAYS_Portable"
set "AAYS_RUNNER_MODE=F_PORTABLE_SINGLE_RUNNER"
set "AAYS_RUNNER_POLL_SECONDS=15"

cd /d "%AAYS_REPO_ROOT%" || exit /b 1

echo AAYS_F_SINGLE_RUNNER_CONTINUE_START=true
echo repo_root=%AAYS_REPO_ROOT%
echo branch=%AAYS_BRANCH%
echo new_runner=false
echo parallel_runner=false
echo max_sequential_queue_tasks=8
echo poll_seconds=%AAYS_RUNNER_POLL_SECONDS%

git -c safe.directory="%AAYS_REPO_ROOT%" fetch --no-tags --depth=1 origin "%AAYS_BRANCH%" || exit /b 1
git -c safe.directory="%AAYS_REPO_ROOT%" checkout "%AAYS_BRANCH%" || exit /b 1
git -c safe.directory="%AAYS_REPO_ROOT%" reset --hard "origin/%AAYS_BRANCH%" || exit /b 1

:RUNNER_LOOP
echo QUEUE_RUNNER_SCAN_STARTING=true
powershell -NoProfile -ExecutionPolicy Bypass -File "docs\chatgpt_status\_shared\automation\RUN_SINGLE_AAYS_MULTI_PAGE_QUEUE_RUNNER_STABLE_20260707.ps1" -RepoRoot "%AAYS_REPO_ROOT%" -WorkRoot "%AAYS_WORK_ROOT%" -MainBranch "%AAYS_BRANCH%" -MaxTasks 8
set "QUEUE_EXIT=%errorlevel%"
echo QUEUE_RUNNER_SCAN_EXIT=%QUEUE_EXIT%
echo QUEUE_RUNNER_NEXT_SCAN_SECONDS=%AAYS_RUNNER_POLL_SECONDS%
timeout /t %AAYS_RUNNER_POLL_SECONDS% /nobreak >nul
goto RUNNER_LOOP
