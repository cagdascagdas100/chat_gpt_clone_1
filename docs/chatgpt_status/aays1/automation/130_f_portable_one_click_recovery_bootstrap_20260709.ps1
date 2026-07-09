# AAYS portable F-disk one-click runner recovery bootstrap.
# Purpose: after PC restart, runner closure, or moving the disk to another Windows PC,
# create self-contained one-click launchers at the portable root and a status proof file.
# Safety: no new runner topology, no DB write, no migration, no production deploy, no fake final.

$ErrorActionPreference = 'Stop'

function Write-Utf8NoBom([string]$Path, [string]$Content) {
  $dir = Split-Path -Parent $Path
  if ($dir -and -not (Test-Path -LiteralPath $dir)) { New-Item -ItemType Directory -Force -Path $dir | Out-Null }
  [System.IO.File]::WriteAllText($Path, $Content, [System.Text.UTF8Encoding]::new($false))
}

$repoRoot = if ($env:AAYS_REPO_ROOT) { $env:AAYS_REPO_ROOT } else { (Get-Location).Path }
$repoRoot = [System.IO.Path]::GetFullPath($repoRoot).TrimEnd('\')

$portableRoot = $env:AAYS_PORTABLE_ROOT
if (-not $portableRoot) {
  $marker = '\runner_system\AAYS_WT\'
  $idx = $repoRoot.IndexOf($marker, [System.StringComparison]::OrdinalIgnoreCase)
  if ($idx -gt 0) {
    $portableRoot = $repoRoot.Substring(0, $idx)
  } else {
    $drive = ([System.IO.Path]::GetPathRoot($repoRoot)).TrimEnd('\')
    $candidate = Join-Path $drive 'TerraYield_AAYS_Portable'
    if (Test-Path -LiteralPath $candidate) { $portableRoot = $candidate } else { $portableRoot = 'F:\TerraYield_AAYS_Portable' }
  }
}
$portableRoot = [System.IO.Path]::GetFullPath($portableRoot).TrimEnd('\')

$healthyRepo = Join-Path $portableRoot 'runner_system\AAYS_WT\AAYS_RUNNER_HEALTHY_20260707'
$workRoot = Join-Path $portableRoot 'runner_system\AAYS_WT\AAYS_STABLE_RUNNER_WORKTREES'
$branch = 'codex/aays-single-runner-v5-20260706'
$logDir = Join-Path $portableRoot '_portable_logs'
New-Item -ItemType Directory -Force -Path $logDir,$workRoot | Out-Null

$cmdPath = Join-Path $portableRoot 'START_AAYS_SINGLE_RUNNER.cmd'
$ps1Path = Join-Path $portableRoot 'START_AAYS_SINGLE_RUNNER.ps1'
$readmePath = Join-Path $portableRoot 'README_ONE_CLICK_RUNNER_RESTART.md'
$statusPath = Join-Path $repoRoot 'docs\chatgpt_status\aays1\status\130_f_portable_one_click_recovery_bootstrap_latest.json'

$cmd = @'
@echo off
setlocal EnableExtensions EnableDelayedExpansion

REM AAYS / TerraYield portable one-click single-runner restart.
REM Put this file in TerraYield_AAYS_Portable root. It works even if the portable disk gets another drive letter.
REM No new runner topology, no DB write, no migration, no production deploy.

set "AAYS_PORTABLE_ROOT=%~dp0"
for %%I in ("%AAYS_PORTABLE_ROOT%.") do set "AAYS_PORTABLE_ROOT=%%~fI"
set "AAYS_REPO_ROOT=%AAYS_PORTABLE_ROOT%\runner_system\AAYS_WT\AAYS_RUNNER_HEALTHY_20260707"
set "AAYS_WORK_ROOT=%AAYS_PORTABLE_ROOT%\runner_system\AAYS_WT\AAYS_STABLE_RUNNER_WORKTREES"
set "AAYS_BRANCH=codex/aays-single-runner-v5-20260706"
set "AAYS_LOG_DIR=%AAYS_PORTABLE_ROOT%\_portable_logs"
if not exist "%AAYS_LOG_DIR%" mkdir "%AAYS_LOG_DIR%"
set "AAYS_LOG=%AAYS_LOG_DIR%\one_click_runner_%DATE:/=-%_%TIME::=-%.log"
set "AAYS_LOG=%AAYS_LOG: =_%"

call :log AAYS_ONE_CLICK_START=true
call :log portable_root=%AAYS_PORTABLE_ROOT%
call :log repo_root=%AAYS_REPO_ROOT%
call :log work_root=%AAYS_WORK_ROOT%
call :log branch=%AAYS_BRANCH%
call :log single_runner_only=true
call :log new_runner=false
call :log parallel_runner=false

if not exist "%AAYS_REPO_ROOT%\.git" (
  call :log ERROR=AAYS_REPO_ROOT_GIT_MISSING
  echo Repo missing: %AAYS_REPO_ROOT%
  pause
  exit /b 2
)

cd /d "%AAYS_REPO_ROOT%" || exit /b 3

git -c safe.directory="%AAYS_REPO_ROOT%" rebase --abort >nul 2>nul
git -c safe.directory="%AAYS_REPO_ROOT%" merge --abort >nul 2>nul
if exist "docs\chatgpt_status\_shared\runner_lock\MULTI_PAGE.lock" rmdir /s /q "docs\chatgpt_status\_shared\runner_lock\MULTI_PAGE.lock" >nul 2>nul

for /f "delims=" %%S in ('git -c safe.directory="%AAYS_REPO_ROOT%" status --porcelain') do set "AAYS_DIRTY=1"
if defined AAYS_DIRTY (
  call :log local_changes=stash_before_pull
  git -c safe.directory="%AAYS_REPO_ROOT%" stash push -u -m "auto_one_click_before_pull" || exit /b 4
)

git -c safe.directory="%AAYS_REPO_ROOT%" fetch origin "%AAYS_BRANCH%" || exit /b 5
git -c safe.directory="%AAYS_REPO_ROOT%" checkout "%AAYS_BRANCH%" || exit /b 6
git -c safe.directory="%AAYS_REPO_ROOT%" pull --ff-only origin "%AAYS_BRANCH%" || exit /b 7

call :log QUEUE_RUNNER_STARTING=true
powershell -NoProfile -ExecutionPolicy Bypass -File "docs\chatgpt_status\_shared\automation\RUN_EXISTING_F_PORTABLE_SINGLE_RUNNER_HOTFIX_THEN_CONTINUE_20260709.ps1" 2>&1 | tee -FilePath "%AAYS_LOG%" -Append
set "EXITCODE=%ERRORLEVEL%"
call :log QUEUE_RUNNER_EXIT=%EXITCODE%
exit /b %EXITCODE%

:log
echo %*
echo %*>>"%AAYS_LOG%"
exit /b 0
'@

$ps1 = @'
# AAYS / TerraYield portable one-click single-runner restart.
# Works from TerraYield_AAYS_Portable root even if the portable disk drive letter changes.
$ErrorActionPreference = 'Stop'
$portableRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$portableRoot = [System.IO.Path]::GetFullPath($portableRoot).TrimEnd('\')
$env:AAYS_PORTABLE_ROOT = $portableRoot
$env:AAYS_REPO_ROOT = Join-Path $portableRoot 'runner_system\AAYS_WT\AAYS_RUNNER_HEALTHY_20260707'
$env:AAYS_WORK_ROOT = Join-Path $portableRoot 'runner_system\AAYS_WT\AAYS_STABLE_RUNNER_WORKTREES'
$branch = 'codex/aays-single-runner-v5-20260706'
$logDir = Join-Path $portableRoot '_portable_logs'
New-Item -ItemType Directory -Force -Path $logDir,$env:AAYS_WORK_ROOT | Out-Null
$log = Join-Path $logDir ('one_click_runner_' + (Get-Date -Format 'yyyyMMdd_HHmmss') + '.log')
function Log([string]$m) { $m | Tee-Object -FilePath $log -Append }
Log 'AAYS_ONE_CLICK_START=true'
Log "portable_root=$portableRoot"
Log "repo_root=$env:AAYS_REPO_ROOT"
Log "work_root=$env:AAYS_WORK_ROOT"
Log "branch=$branch"
Log 'single_runner_only=true'
Log 'new_runner=false'
Log 'parallel_runner=false'
if (-not (Test-Path -LiteralPath (Join-Path $env:AAYS_REPO_ROOT '.git'))) { throw "AAYS_REPO_ROOT_GIT_MISSING: $env:AAYS_REPO_ROOT" }
Set-Location -LiteralPath $env:AAYS_REPO_ROOT
& git -c "safe.directory=$env:AAYS_REPO_ROOT" rebase --abort 2>$null | Out-Null
& git -c "safe.directory=$env:AAYS_REPO_ROOT" merge --abort 2>$null | Out-Null
$lock = 'docs\chatgpt_status\_shared\runner_lock\MULTI_PAGE.lock'
if (Test-Path -LiteralPath $lock) { Remove-Item -LiteralPath $lock -Recurse -Force -ErrorAction SilentlyContinue }
$dirty = (& git -c "safe.directory=$env:AAYS_REPO_ROOT" status --porcelain)
if ($dirty) { Log 'local_changes=stash_before_pull'; & git -c "safe.directory=$env:AAYS_REPO_ROOT" stash push -u -m 'auto_one_click_before_pull' | Tee-Object -FilePath $log -Append }
& git -c "safe.directory=$env:AAYS_REPO_ROOT" fetch origin $branch | Tee-Object -FilePath $log -Append
& git -c "safe.directory=$env:AAYS_REPO_ROOT" checkout $branch | Tee-Object -FilePath $log -Append
& git -c "safe.directory=$env:AAYS_REPO_ROOT" pull --ff-only origin $branch | Tee-Object -FilePath $log -Append
Log 'QUEUE_RUNNER_STARTING=true'
& powershell -NoProfile -ExecutionPolicy Bypass -File 'docs\chatgpt_status\_shared\automation\RUN_EXISTING_F_PORTABLE_SINGLE_RUNNER_HOTFIX_THEN_CONTINUE_20260709.ps1' 2>&1 | Tee-Object -FilePath $log -Append
$exit = $LASTEXITCODE
Log "QUEUE_RUNNER_EXIT=$exit"
exit $exit
'@

$readme = @'
# AAYS / TerraYield Portable Runner Restart

Use this when the PC restarts, the runner window closes, or the portable disk is attached to another Windows PC.

## One-click method

Open the portable disk root folder:

```text
TerraYield_AAYS_Portable
```

Double-click:

```text
START_AAYS_SINGLE_RUNNER.cmd
```

The launcher automatically:

1. Locates the portable root from its own path, so it survives drive-letter changes.
2. Uses only the existing single runner repository under `runner_system\AAYS_WT\AAYS_RUNNER_HEALTHY_20260707`.
3. Aborts stale rebase/merge states.
4. Removes stale runner lock folders.
5. Stashes local dirty runtime files before pull.
6. Pulls the configured branch from GitHub.
7. Runs the existing F portable single-runner continuation script.
8. Writes logs under `_portable_logs`.

## Safety contract

- single_runner_only=true
- new_runner=false
- parallel_runner=false
- fake_data=false
- final_ready=false unless evidence gates pass
- db_write=false
- migration=false
- production_deploy=false
'@

Write-Utf8NoBom $cmdPath $cmd
Write-Utf8NoBom $ps1Path $ps1
Write-Utf8NoBom $readmePath $readme

# Also mirror launchers into the healthy repo root for users who open PowerShell inside the repo instead of the portable root.
Write-Utf8NoBom (Join-Path $healthyRepo 'START_AAYS_SINGLE_RUNNER.cmd') $cmd
Write-Utf8NoBom (Join-Path $healthyRepo 'START_AAYS_SINGLE_RUNNER.ps1') $ps1

$status = [ordered]@{
  status = 'F_PORTABLE_ONE_CLICK_RECOVERY_BOOTSTRAP_INSTALLED'
  portable_root = $portableRoot
  repo_root = $healthyRepo
  work_root = $workRoot
  root_cmd = $cmdPath
  root_ps1 = $ps1Path
  readme = $readmePath
  single_runner_only = $true
  new_runner = $false
  parallel_runner = $false
  final_ready = $false
  product_final_ready = $false
  fake_data = $false
  db_write = $false
  migration = $false
  production_deploy = $false
  installed_at_utc = (Get-Date).ToUniversalTime().ToString('o')
}
Write-Utf8NoBom $statusPath (($status | ConvertTo-Json -Depth 20) + "`n")
$status | ConvertTo-Json -Depth 20
