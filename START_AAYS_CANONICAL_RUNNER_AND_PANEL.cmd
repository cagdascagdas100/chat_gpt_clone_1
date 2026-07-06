@echo off
setlocal
set "ROOT=%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%ROOT%docs\chatgpt_status\_shared\automation\START_AAYS_CANONICAL_RUNNER_AND_PANEL_20260706.ps1" -RepoRoot "%ROOT%"
endlocal
