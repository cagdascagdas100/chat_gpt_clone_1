$ErrorActionPreference = "Stop"
$RepoRoot = $env:AAYS_REPO_ROOT
if ([string]::IsNullOrWhiteSpace($RepoRoot)) {
  $RepoRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..\..\..\..")).Path
}
$TaskId = if ([string]::IsNullOrWhiteSpace($env:AAYS_TASK_ID)) { "aays1-runner-pickup-probe-20260707" } else { $env:AAYS_TASK_ID }
$PageKey = if ([string]::IsNullOrWhiteSpace($env:AAYS_PAGE_KEY)) { "aays1" } else { $env:AAYS_PAGE_KEY }
$stamp = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
$statusDir = Join-Path $RepoRoot "docs\chatgpt_status\$PageKey\status"
$reportDir = Join-Path $RepoRoot "docs\chatgpt_status\$PageKey\reports"
$heartbeatDir = Join-Path $RepoRoot "docs\chatgpt_status\$PageKey\heartbeat"
foreach ($dir in @($statusDir,$reportDir,$heartbeatDir)) { New-Item -ItemType Directory -Force -Path $dir | Out-Null }
$payload = [ordered]@{
  task_id = $TaskId
  page_key = $PageKey
  status = "pickup_probe_completed"
  checked_at = $stamp
  runner_pickup_verified = $true
  final_ready = $false
  product_final_ready = $false
  fake_data = $false
  db_write = $false
  migration = $false
  production_deploy = $false
  blocker = "none"
}
$payload | ConvertTo-Json -Depth 20 | Set-Content -Encoding UTF8 -LiteralPath (Join-Path $statusDir "090_runner_pickup_probe_latest.json")
$payload | ConvertTo-Json -Depth 20 | Set-Content -Encoding UTF8 -LiteralPath (Join-Path $reportDir "090_runner_pickup_probe_report.json")
("TASK_ID=$TaskId`nPAGE_KEY=$PageKey`nSTATUS=pickup_probe_completed`nRUNNER_PICKUP_VERIFIED=true`nFINAL_READY=false`nFAKE_DATA=false`nDB_WRITE=false`nMIGRATION=false`nPRODUCTION_DEPLOY=false`nHEARTBEAT_AT=$stamp`n") | Set-Content -Encoding UTF8 -LiteralPath (Join-Path $heartbeatDir "090_runner_pickup_probe_heartbeat.txt")
Write-Output "AAYS1_RUNNER_PICKUP_PROBE_OK task_id=$TaskId final_ready=false fake_data=false db_write=false migration=false production_deploy=false"
exit 0