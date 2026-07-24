$ErrorActionPreference = 'Stop'
$RepoRoot = $env:AAYS_REPO_ROOT
if ([string]::IsNullOrWhiteSpace($RepoRoot)) { $RepoRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..\..\..\..')).Path }
$PageKey = 'aays1'
$TaskId = if ([string]::IsNullOrWhiteSpace($env:AAYS_TASK_ID)) { 'aays1-site-status-sync-20260707' } else { $env:AAYS_TASK_ID }
$Now = (Get-Date).ToUniversalTime().ToString('o')
function P($x) { Join-Path $RepoRoot $x }
$statusDir = P 'docs\chatgpt_status\aays1\status'
$reportDir = P 'docs\chatgpt_status\aays1\reports'
$heartbeatDir = P 'docs\chatgpt_status\aays1\heartbeat'
New-Item -ItemType Directory -Force -Path $statusDir,$reportDir,$heartbeatDir | Out-Null
$sitePath = P 'england_map_web\data\runner_panel\page_status_index.json'
if (Test-Path -LiteralPath $sitePath) {
  $idx = Get-Content -Raw -LiteralPath $sitePath | ConvertFrom-Json -ErrorAction Stop
  foreach ($pg in @($idx.pages)) {
    if ([string]$pg.page_key -eq $PageKey) {
      $pg.runner_status = 'RunningEvidence'
      $pg.single_runner_status = 'RunningEvidence'
      $pg.latest_queue_status = 'pending'
      $pg.latest_task_id = 'aays1-real-product-evidence-fetch-20260707'
      $pg.latest_queue_task = 'docs/chatgpt_status/aays1/queue/091_aays1_real_product_evidence_fetch_20260707.task.json'
      $pg.completion_percent = 35
      $pg.remaining_percent = 65
      $pg.final_ready = $false
      $pg.latest_report = 'docs/chatgpt_status/aays1/reports/065_parallel_source_evidence_batch_blocked_latest.md'
      $pg.latest_blocker = 'real_product_source_fetch_implementation_required'
      $pg.blockers = @('real_product_source_fetch_implementation_required')
      $pg.heartbeat_at = $Now
      $pg.last_heartbeat_at = $Now
    }
  }
  $idx.updated_at = $Now
  $idx.generated_at = $Now
  $idx.single_runner_active = $true
  $idx.single_runner_status = 'runner_active'
  $idx.repo_root = 'C:\AAYS_WT\AAYS_RUNNER_HEALTHY_20260707'
  $idx.branch = 'codex/aays-single-runner-v5-20260706'
  $idx | ConvertTo-Json -Depth 100 | Set-Content -Encoding UTF8 -LiteralPath $sitePath
}
@{
  page_key=$PageKey
  task_id=$TaskId
  status='site_status_synced_to_real_pending_state'
  updated_at=$Now
  final_ready=$false
  fake_data=$false
  db_write=$false
  migration=$false
  production_deploy=$false
  blocker='real_product_source_fetch_implementation_required'
} | ConvertTo-Json -Depth 20 | Set-Content -Encoding UTF8 -LiteralPath (Join-Path $statusDir '092_aays1_site_status_sync_latest.json')
"# aays1 site status sync`n`nstatus: site_status_synced_to_real_pending_state`nblocker: real_product_source_fetch_implementation_required`nfinal_ready: false`nfake_data: false`ndb_write: false`nmigration: false`nproduction_deploy: false`n" | Set-Content -Encoding UTF8 -LiteralPath (Join-Path $reportDir '092_aays1_site_status_sync_latest.md')
"aays1 site status synced $Now final_ready=false" | Set-Content -Encoding UTF8 -LiteralPath (Join-Path $heartbeatDir '092_aays1_site_status_sync_latest.txt')
Write-Output 'AAYS1_SITE_STATUS_SYNCED final_ready=false blocker=real_product_source_fetch_implementation_required'
exit 0
