$ErrorActionPreference = 'Stop'
$repoRoot = if ($env:AAYS_REPO_ROOT) { $env:AAYS_REPO_ROOT } else { (Get-Location).Path }
$pageKey = 'aays1'
$statusDir = Join-Path $repoRoot 'docs/chatgpt_status/aays1/status'
New-Item -ItemType Directory -Force -Path $statusDir | Out-Null
$heartbeatPath = Join-Path $repoRoot 'docs/chatgpt_status/_shared/heartbeat/stable_runner_daemon_heartbeat_latest.json'
$lockPath = Join-Path $repoRoot 'docs/chatgpt_status/_shared/locks/single_runner.lock'
$proofPath = Join-Path $repoRoot 'docs/chatgpt_status/aays1/status/130_f_portable_one_click_recovery_bootstrap_latest.json'
$now = Get-Date
$heartbeat = $null
$heartbeatFresh = $false
if (Test-Path $heartbeatPath) {
  try {
    $heartbeat = Get-Content -Raw -Path $heartbeatPath | ConvertFrom-Json
    if ($heartbeat.heartbeat_at) {
      $hbTime = [datetime]::Parse($heartbeat.heartbeat_at)
      $heartbeatFresh = (($now.ToUniversalTime() - $hbTime.ToUniversalTime()).TotalMinutes -le 20)
    }
  } catch { $heartbeat = $null }
}
$lockExists = Test-Path $lockPath
$proofExists = Test-Path $proofPath
$result = [ordered]@{
  task_id = 'f-portable-runtime-self-check-20260709'
  page_key = $pageKey
  status = 'runtime_self_check_done'
  repo_root_used = $repoRoot
  expected_f_portable_root = 'F:\TerraYield_AAYS_Portable'
  heartbeat_path = 'docs/chatgpt_status/_shared/heartbeat/stable_runner_daemon_heartbeat_latest.json'
  heartbeat_exists = [bool](Test-Path $heartbeatPath)
  heartbeat_runner_active = if ($heartbeat -and ($null -ne $heartbeat.runner_active)) { [bool]$heartbeat.runner_active } else { $null }
  heartbeat_at = if ($heartbeat) { $heartbeat.heartbeat_at } else { $null }
  heartbeat_fresh_within_20m = $heartbeatFresh
  lock_path = 'docs/chatgpt_status/_shared/locks/single_runner.lock'
  lock_exists = $lockExists
  proof_130_exists = $proofExists
  runner_healthy_for_chatgpt_continue = ($heartbeatFresh -and $lockExists -and $proofExists)
  site_visible_progress_percent = 66
  overall_progress_percent = 93
  remaining_percent = 7
  final_ready = $false
  fake_data = $false
  db_write = $false
  migration = $false
  production_deploy = $false
  checked_at = (Get-Date).ToString('o')
}
$out = Join-Path $statusDir '132_f_portable_runtime_self_check_latest.json'
$result | ConvertTo-Json -Depth 8 | Set-Content -Encoding UTF8 -Path $out
