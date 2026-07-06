[CmdletBinding()]
param(
  [switch]$NoPanel
)

$ErrorActionPreference = "Stop"

$repoRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..\..\..\..")).Path
$sharedRoot = Join-Path $repoRoot "docs/chatgpt_status/_shared"
$runner = Join-Path $sharedRoot "automation/RUN_SINGLE_AAYS_MULTI_PAGE_QUEUE_RUNNER.ps1"
$panel = Join-Path $sharedRoot "automation/AAYS_RUNNER_PANEL.ps1"
$builder = Join-Path $sharedRoot "automation/BUILD_AAYS_PAGE_PANEL_INDEX.ps1"
$stateDir = Join-Path $sharedRoot "state"
$statePath = Join-Path $stateDir "runner_panel_state.json"
$lockPath = Join-Path $stateDir "single_runner.lock.json"

New-Item -ItemType Directory -Force -Path $stateDir | Out-Null
& powershell -NoProfile -ExecutionPolicy Bypass -File $builder -RepoRoot $repoRoot -EnsurePageDirs | Out-Null

$runnerActive = $false
$runnerPid = $null
if (Test-Path -LiteralPath $lockPath) {
  try {
    $lock = Get-Content -Raw -LiteralPath $lockPath | ConvertFrom-Json
    $runnerPid = [int]$lock.pid
    $runnerActive = $null -ne (Get-Process -Id $runnerPid -ErrorAction SilentlyContinue)
  } catch {
    $runnerActive = $false
  }
}

if (-not $runnerActive) {
  $proc = Start-Process -FilePath powershell -ArgumentList @(
    "-NoProfile",
    "-ExecutionPolicy",
    "Bypass",
    "-File",
    $runner,
    "-Loop",
    "-IntervalSeconds",
    "60",
    "-MaxTasksPerScan",
    "1"
  ) -WorkingDirectory $repoRoot -WindowStyle Hidden -PassThru
  $runnerPid = $proc.Id
  $runnerActive = $true
  Start-Sleep -Seconds 2
} else {
  Write-Output "runner already active pid=$runnerPid"
}

if (-not $NoPanel -and (Test-Path -LiteralPath $panel)) {
  Start-Process -FilePath powershell -ArgumentList @(
    "-NoProfile",
    "-ExecutionPolicy",
    "Bypass",
    "-File",
    $panel
  ) -WorkingDirectory $repoRoot | Out-Null
}

$state = [ordered]@{
  last_updated = (Get-Date).ToUniversalTime().ToString("o")
  single_runner_active = [bool]$runnerActive
  runner_pid = $runnerPid
  runner_lock_active = (Test-Path -LiteralPath $lockPath)
  panel_index = "docs/chatgpt_status/_shared/panel/page_status_index_latest.json"
}
$state | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $statePath -Encoding UTF8

$state | ConvertTo-Json -Depth 6
