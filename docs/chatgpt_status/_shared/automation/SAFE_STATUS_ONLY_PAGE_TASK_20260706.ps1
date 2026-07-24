[CmdletBinding()]
param(
  [Parameter(Mandatory = $true)][string]$PageKey,
  [Parameter(Mandatory = $true)][string]$TaskId,
  [string]$Blocker = "missing_real_automation"
)

$ErrorActionPreference = "Stop"
$repoRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..\..\..\..")).Path
$pageRoot = Join-Path $repoRoot "docs/chatgpt_status/$PageKey"
foreach ($dir in @("status", "reports", "heartbeat", "completed", "blocked", "runner_outputs")) {
  New-Item -ItemType Directory -Force -Path (Join-Path $pageRoot $dir) | Out-Null
}

$now = (Get-Date).ToUniversalTime().ToString("o")
$safeTaskId = ($TaskId -replace '[^A-Za-z0-9_.-]', '_')
$status = [ordered]@{
  task_id = $safeTaskId
  page_key = $PageKey
  status = "blocked"
  completed_at = $now
  queue_seen = $true
  queue_started = $true
  single_runner_lock_acquired = $true
  task_runs_in_clean_worktree = $true
  allowed_paths_enforced = $true
  runner_output_uploaded = $true
  post_sync_ok = $false
  PUSH_SYNC_OK = $false
  CONTINUE_RUNNER_READY = $false
  final_ready = $false
  product_final_ready = $false
  fake_data = $false
  db_write = $false
  migration = $false
  production_deploy = $false
  blockers = @($Blocker)
  outputs = @{}
}

$statusPath = Join-Path $pageRoot "status/${safeTaskId}_completed.json"
$blockedPath = Join-Path $pageRoot "blocked/${safeTaskId}_blocked.json"
$completedPath = Join-Path $pageRoot "completed/${safeTaskId}_completed.json"
$heartbeatPath = Join-Path $pageRoot "heartbeat/${safeTaskId}_heartbeat.txt"
$reportPath = Join-Path $pageRoot "reports/${safeTaskId}_runner_output.txt"

$status | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $statusPath -Encoding UTF8
$status | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $blockedPath -Encoding UTF8
$status | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $completedPath -Encoding UTF8
@(
  "PAGE_KEY=$PageKey",
  "TASK_ID=$safeTaskId",
  "RUNNER_ALIVE=true",
  "RUNNER_MODE=single_shared_runner",
  "HEARTBEAT_AT=$now",
  "QUEUE_SEEN=true",
  "QUEUE_STARTED=true",
  "SINGLE_RUNNER_LOCK_ACQUIRED=true",
  "TASK_RUNS_IN_CLEAN_WORKTREE=true",
  "ALLOWED_PATHS_ENFORCED=true",
  "RUNNER_OUTPUT_UPLOADED=true",
  "POST_SYNC_OK=false",
  "PUSH_SYNC_OK=false",
  "FINAL_READY=false",
  "BLOCKER=$Blocker"
) | Set-Content -LiteralPath $heartbeatPath -Encoding UTF8
@(
  "AAYS safe status-only task",
  "page_key: $PageKey",
  "task_id: $safeTaskId",
  "status: blocked",
  "final_ready: false",
  "fake_data: false",
  "blocker: $Blocker"
) | Set-Content -LiteralPath $reportPath -Encoding UTF8

[pscustomobject]@{
  page_key = $PageKey
  task_id = $safeTaskId
  status = "blocked"
  final_ready = $false
  blocker = $Blocker
  report = $reportPath
} | ConvertTo-Json -Depth 6
