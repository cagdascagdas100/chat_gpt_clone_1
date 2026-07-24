@echo off
setlocal

REM AAYS EXISTING F SINGLE RUNNER LAUNCHER
REM No new runner, no new worktree, no clone, no DB write, no migration, no production deploy.
REM This starts/continues the existing F portable single runner from the canonical F root.

set "AAYS_REPO_ROOT=F:\TerraYield_AAYS_Portable\runner_system\AAYS_WT\AAYS_RUNNER_HEALTHY_20260707"
set "AAYS_WORK_ROOT=F:\TerraYield_AAYS_Portable\runner_system\AAYS_WT\AAYS_STABLE_RUNNER_WORKTREES"
set "AAYS_BRANCH=codex/aays-single-runner-v5-20260706"
set "AAYS_PORTABLE_ROOT=F:\TerraYield_AAYS_Portable"
set "AAYS_RUNNER_MODE=F_PORTABLE_SINGLE_RUNNER"

echo AAYS existing F single runner launcher
echo Repo root: %AAYS_REPO_ROOT%
echo Branch: %AAYS_BRANCH%
echo New runner: false
echo Parallel runner: false

cd /d "%AAYS_REPO_ROOT%" || exit /b 1

git -c safe.directory="%AAYS_REPO_ROOT%" fetch --no-tags --depth=1 origin "%AAYS_BRANCH%" || exit /b 1
git -c safe.directory="%AAYS_REPO_ROOT%" checkout "%AAYS_BRANCH%" || exit /b 1
git -c safe.directory="%AAYS_REPO_ROOT%" reset --hard "origin/%AAYS_BRANCH%" || exit /b 1

call "docs\chatgpt_status\_shared\automation\RUN_EXISTING_F_PORTABLE_SINGLE_RUNNER_HOTFIX_THEN_CONTINUE_20260709.cmd"
exit /b %errorlevel%
