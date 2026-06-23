$ErrorActionPreference = 'Continue'
$TaskId = 'topography_single_runner_contract_recovery_20260623T010000Z'
$PageKey = 'AAYS_REAL_TOPOGRAPHY_PRODUCT'
$Here = Split-Path -Parent $MyInvocation.MyCommand.Path
$PageRoot = Split-Path -Parent $Here
$RepoRoot = (Resolve-Path (Join-Path $PageRoot '..\..')).Path
$Reports = Join-Path $PageRoot 'reports'
$Status = Join-Path $PageRoot 'status'
$Heartbeat = Join-Path $PageRoot 'heartbeat'
New-Item -ItemType Directory -Force -Path $Reports,$Status,$Heartbeat | Out-Null
$ReportPath = Join-Path $Reports ($TaskId + '_existing_bridge_diagnostic_once_report.txt')
$StatusPath = Join-Path $Status ($TaskId + '_existing_bridge_diagnostic_once.status.txt')
$HeartbeatPath = Join-Path $Heartbeat ($TaskId + '_existing_bridge_diagnostic_once.heartbeat.txt')

function Add-Line([string]$Text) { Add-Content -LiteralPath $ReportPath -Value $Text -Encoding UTF8 }
Set-Content -LiteralPath $ReportPath -Value @(
  "TASK_ID=$TaskId",
  "PAGE_KEY=$PageKey",
  "REPORT=existing_bridge_diagnostic_once",
  "START_UTC=$((Get-Date).ToUniversalTime().ToString('o'))"
) -Encoding UTF8

Add-Line "PAGE_ROOT=$PageRoot"
Add-Line "REPO_ROOT=$RepoRoot"
Add-Line "QUEUE_ACTIVE_EXISTS=$(Test-Path (Join-Path $PageRoot 'queue\_ACTIVE_TASK.md'))"
Add-Line "CURRENT_ACTIVE_EXISTS=$(Test-Path (Join-Path $PageRoot 'current-task\ACTIVE_TASK.md'))"
Add-Line "RUNNER_TASK_ACTIVE_EXISTS=$(Test-Path (Join-Path $PageRoot 'runner_tasks\_ACTIVE_TASK.md'))"
Add-Line "CANONICAL_AUTOMATION_EXISTS=$(Test-Path (Join-Path $Here ($TaskId + '.ps1')))"
Add-Line "V6_AUTOMATION_EXISTS=$(Test-Path (Join-Path $Here ($TaskId + '_v6.ps1')))"
Add-Line "SHARED_RUNNER_SCRIPT_EXISTS=$(Test-Path (Join-Path $RepoRoot 'docs\chatgpt_status\_shared\automation\RUN_SINGLE_AAYS_MULTI_PAGE_QUEUE_RUNNER.ps1'))"

Push-Location $RepoRoot
try {
  Add-Line "GIT_BRANCH=$((git branch --show-current) 2>$null)"
  Add-Line "GIT_STATUS_SHORT_BEGIN"
  (git status --short 2>&1) | ForEach-Object { Add-Line $_ }
  Add-Line "GIT_STATUS_SHORT_END"
} finally {
  Pop-Location
}

Set-Content -LiteralPath $StatusPath -Value @(
  "TASK_ID=$TaskId",
  "PAGE_KEY=$PageKey",
  "STATUS=EXISTING_BRIDGE_DIAGNOSTIC_ONCE_WRITTEN",
  "PRODUCT_COMPLETENESS_ESTIMATE=93",
  "PRODUCT_100_READY=false",
  "REPORT=docs/chatgpt_status/$PageKey/reports/$($TaskId)_existing_bridge_diagnostic_once_report.txt"
) -Encoding UTF8
Set-Content -LiteralPath $HeartbeatPath -Value "existing_bridge_diagnostic_once_completed_utc=$((Get-Date).ToUniversalTime().ToString('o'))" -Encoding UTF8
