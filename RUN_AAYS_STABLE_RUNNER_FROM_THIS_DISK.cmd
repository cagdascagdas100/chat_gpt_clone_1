@echo off
setlocal

REM AAYS EXISTING F SINGLE RUNNER LAUNCHER
REM No new runner, no new worktree, no clone, no DB write, no migration, no production deploy.
REM This only starts/continues the existing F portable single runner from the canonical F root.

set "AAYS_REPO_ROOT=F:\TerraYield_AAYS_Portable\runner_system\AAYS_WT\AAYS_RUNNER_HEALTHY_20260707"
set "AAYS_WORK_ROOT=F:\TerraYield_AAYS_Portable\runner_system\AAYS_WT\AAYS_STABLE_RUNNER_WORKTREES"
set "AAYS_BRANCH=codex/aays-single-runner-v5-20260706"

echo AAYS existing F single runner launcher
echo Repo root: %AAYS_REPO_ROOT%
echo Branch: %AAYS_BRANCH%

cd /d "%AAYS_REPO_ROOT%" || exit /b 1

git fetch origin "%AAYS_BRANCH%" || exit /b 1
git checkout "%AAYS_BRANCH%" || exit /b 1
git pull --ff-only origin "%AAYS_BRANCH%" || exit /b 1

powershell -NoProfile -ExecutionPolicy Bypass -File "docs\chatgpt_status\_shared\automation\RUN_EXISTING_F_PORTABLE_SINGLE_RUNNER_HOTFIX_THEN_CONTINUE_20260709.ps1"
exit /b %errorlevel%
