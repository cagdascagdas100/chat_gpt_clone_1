@echo off
setlocal

REM AAYS existing F portable single-runner continuation launcher.
REM This does not create a new runner, worktree, queue, DB write, migration, or production deploy.
REM Setup gates are non-blocking; the actual single queue runner is always attempted.

set "AAYS_REPO_ROOT=F:\TerraYield_AAYS_Portable\runner_system\AAYS_WT\AAYS_RUNNER_HEALTHY_20260707"
set "AAYS_WORK_ROOT=F:\TerraYield_AAYS_Portable\runner_system\AAYS_WT\AAYS_STABLE_RUNNER_WORKTREES"
set "AAYS_BRANCH=codex/aays-single-runner-v5-20260706"

cd /d "%AAYS_REPO_ROOT%" || exit /b 1

echo AAYS_F_SINGLE_RUNNER_CONTINUE_START=true
echo repo_root=%AAYS_REPO_ROOT%
echo branch=%AAYS_BRANCH%
echo new_runner=false
echo parallel_runner=false

powershell -NoProfile -ExecutionPolicy Bypass -File "docs\chatgpt_status\_shared\automation\APPLY_F_PORTABLE_SINGLE_RUNNER_HOTFIX_20260709.ps1"
echo hotfix_exit=%errorlevel%

powershell -NoProfile -ExecutionPolicy Bypass -File "docs\chatgpt_status\distance_property_types\automation\patch_dpt_site_panel_status_20260709.ps1"
echo panel_patch_exit=%errorlevel%

echo QUEUE_RUNNER_STARTING=true
powershell -NoProfile -ExecutionPolicy Bypass -File "docs\chatgpt_status\_shared\automation\RUN_SINGLE_AAYS_MULTI_PAGE_QUEUE_RUNNER_STABLE_20260707.ps1" -RepoRoot "%AAYS_REPO_ROOT%" -WorkRoot "%AAYS_WORK_ROOT%" -MainBranch "%AAYS_BRANCH%" -MaxTasks 5
echo QUEUE_RUNNER_EXIT=%errorlevel%
exit /b %errorlevel%
