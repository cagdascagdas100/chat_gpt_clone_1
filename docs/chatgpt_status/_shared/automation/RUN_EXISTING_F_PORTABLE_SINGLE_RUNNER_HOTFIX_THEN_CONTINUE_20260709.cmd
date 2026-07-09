@echo off
setlocal

REM AAYS existing F portable single-runner continuation launcher.
REM This does not create a new runner, worktree, queue, DB write, migration, or production deploy.
REM It pulls the active branch, runs the F-portable fixed queue runner, and pushes proof/output files.

set "AAYS_REPO_ROOT=F:\TerraYield_AAYS_Portable\runner_system\AAYS_WT\AAYS_RUNNER_HEALTHY_20260707"
set "AAYS_WORK_ROOT=F:\TerraYield_AAYS_Portable\runner_system\AAYS_WT\AAYS_STABLE_RUNNER_WORKTREES"
set "AAYS_BRANCH=codex/aays-single-runner-v5-20260706"
set "AAYS_PORTABLE_ROOT=F:\TerraYield_AAYS_Portable"
set "AAYS_RUNNER_MODE=F_PORTABLE_SINGLE_RUNNER"

cd /d "%AAYS_REPO_ROOT%" || exit /b 1

echo AAYS_F_SINGLE_RUNNER_CONTINUE_START=true
echo repo_root=%AAYS_REPO_ROOT%
echo branch=%AAYS_BRANCH%
echo new_runner=false
echo parallel_runner=false

git -c safe.directory="%AAYS_REPO_ROOT%" fetch --no-tags --depth=1 origin "%AAYS_BRANCH%" || exit /b 1
git -c safe.directory="%AAYS_REPO_ROOT%" checkout "%AAYS_BRANCH%" || exit /b 1
git -c safe.directory="%AAYS_REPO_ROOT%" reset --hard "origin/%AAYS_BRANCH%" || exit /b 1

echo QUEUE_RUNNER_STARTING=true
powershell -NoProfile -ExecutionPolicy Bypass -File "docs\chatgpt_status\_shared\automation\RUN_SINGLE_AAYS_MULTI_PAGE_QUEUE_RUNNER_STABLE_20260707.ps1" -RepoRoot "%AAYS_REPO_ROOT%" -WorkRoot "%AAYS_WORK_ROOT%" -MainBranch "%AAYS_BRANCH%" -MaxTasks 5
echo QUEUE_RUNNER_EXIT=%errorlevel%
exit /b %errorlevel%
