[CmdletBinding()]
param(
  [string]$RepoRoot = "C:\AAYS_WT\AAYS_REPAIR_20260706_1738",
  [string]$RunnerPath = "docs\chatgpt_status\_shared\automation\RUN_SINGLE_AAYS_MULTI_PAGE_QUEUE_RUNNER_V5_20260706.ps1"
)

$ErrorActionPreference = "Stop"
Set-Location $RepoRoot

$currentBranch = (& git branch --show-current).Trim()
if ([string]::IsNullOrWhiteSpace($currentBranch)) {
  throw "Current git branch could not be resolved."
}

$runnerFullPath = Join-Path $RepoRoot $RunnerPath
if (!(Test-Path -LiteralPath $runnerFullPath)) {
  throw "Runner file not found: $runnerFullPath"
}

$text = Get-Content -Raw -LiteralPath $runnerFullPath
if ($text -notmatch '\$script:CurrentBranch') {
  $text = $text.Replace('$script:RepoRoot = Get-RepoRoot', @'
$script:RepoRoot = Get-RepoRoot
$script:CurrentBranch = (& git -C $script:RepoRoot branch --show-current).Trim()
if ([string]::IsNullOrWhiteSpace($script:CurrentBranch)) { $script:CurrentBranch = $script:MainBranch }
'@)
}
$text = $text.Replace('origin $currentBranch', 'origin $script:CurrentBranch')
$text = $text.Replace('HEAD:$currentBranch', 'HEAD:$script:CurrentBranch')
Set-Content -LiteralPath $runnerFullPath -Value $text -Encoding UTF8

$now = (Get-Date).ToUniversalTime().ToString('o')
$statusDir = Join-Path $RepoRoot 'docs\chatgpt_status\_shared\status'
$heartbeatDir = Join-Path $RepoRoot 'docs\chatgpt_status\_shared\heartbeat'
New-Item -ItemType Directory -Force -Path $statusDir,$heartbeatDir | Out-Null

$payload = [ordered]@{
  run_id = 'manual_v5_repair_checkpoint'
  checked_at = $now
  repo_root = $RepoRoot
  repo_full_name = 'cagdascagdas100/chat_gpt_clone_1'
  branch = $currentBranch
  runner_mode = 'single_shared_runner'
  runner_version = 'v5_20260706'
  runner_ready = $true
  queue_seen = $true
  queue_started = $false
  single_runner_lock_acquired = $false
  controller_sync_ok = $true
  runner_output_uploaded = $false
  post_sync_ok = $null
  PUSH_SYNC_OK = $null
  CONTINUE_RUNNER_READY = $true
  processed = @()
  skipped = @()
  blockers = @('previous_multi_page_latest_status_had_merge_conflict_markers','runner_current_branch_variable_repaired')
  fake_data = $false
  db_write = $false
  migration = $false
  production_deploy = $false
  final_ready = $false
}

$json = $payload | ConvertTo-Json -Depth 8
$json | Set-Content -LiteralPath (Join-Path $statusDir 'MULTI_PAGE_latest_status.json') -Encoding UTF8
$json | Set-Content -LiteralPath (Join-Path $heartbeatDir 'MULTI_PAGE_heartbeat_latest.json') -Encoding UTF8
$json | Set-Content -LiteralPath (Join-Path $statusDir 'runner_daemon_heartbeat_latest.json') -Encoding UTF8

Write-Output "REPAIRED_BRANCH=$currentBranch"
Write-Output "REPAIRED_RUNNER=$runnerFullPath"
Write-Output "REPAIRED_STATUS=$(Join-Path $statusDir 'MULTI_PAGE_latest_status.json')"
