@echo off
setlocal EnableExtensions

REM AAYS existing F portable single-runner continuation launcher.
REM Reuses the existing canonical F runner architecture only.
REM No parallel runner, new worktree, clone, DB write, migration, or production deploy.

set "AAYS_REPO_ROOT=F:\TerraYield_AAYS_Portable\runner_system\AAYS_WT\AAYS_RUNNER_HEALTHY_20260707"
set "AAYS_WORK_ROOT=F:\TerraYield_AAYS_Portable\runner_system\AAYS_WT\AAYS_STABLE_RUNNER_WORKTREES"
set "AAYS_BRANCH=codex/aays-single-runner-v5-20260706"
set "AAYS_PORTABLE_ROOT=F:\TerraYield_AAYS_Portable"
set "AAYS_RUNNER_MODE=F_PORTABLE_SINGLE_RUNNER"

cd /d "%AAYS_REPO_ROOT%" || exit /b 1
if not exist "devam.ps1" (
  echo BLOCKED_CANONICAL_REPO_DEVAM_MISSING=true
  exit /b 2
)

for /f "delims=" %%B in ('git -c safe.directory^="%AAYS_REPO_ROOT%" rev-parse --abbrev-ref HEAD 2^>nul') do set "AAYS_ACTIVE_BRANCH=%%B"
if /i not "%AAYS_ACTIVE_BRANCH%"=="%AAYS_BRANCH%" (
  echo BLOCKED_CANONICAL_BRANCH_MISMATCH=%AAYS_ACTIVE_BRANCH%
  exit /b 3
)

if not exist "%AAYS_WORK_ROOT%" mkdir "%AAYS_WORK_ROOT%" || exit /b 4

echo AAYS_F_SINGLE_RUNNER_CONTINUE_START=true
echo repo_root=%AAYS_REPO_ROOT%
echo work_root=%AAYS_WORK_ROOT%
echo branch=%AAYS_BRANCH%
echo persistent_daemon=true
echo max_tasks_per_scan=1
echo new_runner_architecture=false
echo parallel_runner=false

powershell -NoProfile -ExecutionPolicy Bypass -File "devam.ps1"
set "RUNNER_EXIT=%errorlevel%"
echo AAYS_F_SINGLE_RUNNER_CONTINUE_EXIT=%RUNNER_EXIT%
exit /b %RUNNER_EXIT%
