@echo off
setlocal
set AAYS_REPO_ROOT=C:\AAYS_WT\AAYS_RUNNER_HEALTHY_20260707
set AAYS_BRIDGE_ROOT=C:\AAYS_WT\AAYS_STABLE_RUNNER_WORKTREES
set AAYS_PAGE_KEY=aays1
set AAYS_TARGET_BRANCH=codex/aays-single-runner-v5-20260706
echo Starting existing AAYS single runner only...
echo Repo root: %AAYS_REPO_ROOT%
echo Branch: %AAYS_TARGET_BRANCH%
call "C:\Users\cagda\Documents\GitHub\AAYS\START_AAYS_RUNNER.bat"
echo Runner start command completed. Refresh 8020 with Ctrl+F5 after 5-10 minutes.
pause
endlocal
