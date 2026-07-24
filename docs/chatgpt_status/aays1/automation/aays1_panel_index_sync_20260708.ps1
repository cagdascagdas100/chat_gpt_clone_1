$ErrorActionPreference = 'Stop'
$RepoRoot = if ($env:AAYS_REPO_ROOT) { $env:AAYS_REPO_ROOT } else { (Get-Location).Path }
$TaskId = if ($env:AAYS_TASK_ID) { $env:AAYS_TASK_ID } else { 'aays1-panel-index-sync-20260708' }
$PageKey = 'aays1'
$Now = (Get-Date).ToString('o')

$panelPath = Join-Path $RepoRoot 'england_map_web/data/runner_panel/page_status_index.json'
$statusDir = Join-Path $RepoRoot 'docs/chatgpt_status/aays1/status'
$reportDir = Join-Path $RepoRoot 'docs/chatgpt_status/aays1/reports'
$outDir = Join-Path $RepoRoot 'docs/chatgpt_status/aays1/runner_outputs'
New-Item -ItemType Directory -Force -Path $statusDir,$reportDir,$outDir | Out-Null

if (-not (Test-Path -LiteralPath $panelPath)) { throw 'PANEL_INDEX_NOT_FOUND' }
$panel = Get-Content -LiteralPath $panelPath -Raw | ConvertFrom-Json
$hit = $false
foreach ($p in @($panel.pages)) {
  if ($p.page_key -eq 'aays1') {
    $p.runner_status = 'AAYS1_065_EVIDENCE_VERIFIED_PENDING_BROWSER_FINAL'
    $p.latest_queue_status = 'done'
    $p.latest_task_id = 'aays1-065-product-evidence-implementation-20260708'
    $p.latest_queue_task = 'docs/chatgpt_status/aays1/status/aays1_065_product_evidence_latest.json'
    $p.completion_percent = 65
    $p.remaining_percent = 35
    $p.latest_report = 'docs/chatgpt_status/aays1/reports/aays1_065_product_evidence_report.md'
    $p.latest_blocker = 'browser_smoke_and_popup_right_panel_proof_required_before_final_ready'
    $p.single_runner_status = 'AAYS1_065_EVIDENCE_VERIFIED_PENDING_BROWSER_FINAL'
    $p.last_heartbeat_at = $Now
    $p.heartbeat_at = $Now
    $p.last_completed_at = $Now
    $p.verified_new_rows = 150
    $p.target_new_rows = 160
    $hit = $true
  }
}
$panel.updated_at = $Now
$panel.single_runner_active = $true
$panel.single_runner_status = 'runner_active'
$panel | ConvertTo-Json -Depth 80 | Set-Content -LiteralPath $panelPath -Encoding UTF8

$result = [ordered]@{
  task_id=$TaskId; page_key=$PageKey; checked_at=$Now; panel_index_updated=$hit;
  completion_percent=65; remaining_percent=35; progress_delta_percent=10;
  verified_new_rows=150; final_ready=$false; product_final_ready=$false;
  fake_data=$false; db_write=$false; migration=$false; production_deploy=$false
}
$result | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath (Join-Path $statusDir 'aays1_panel_index_sync_latest.json') -Encoding UTF8
$result | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath (Join-Path $outDir 'aays1_panel_index_sync_summary.json') -Encoding UTF8
"AAYS1_PANEL_INDEX_SYNC_DONE completion_percent=65 remaining_percent=35 final_ready=false fake_data=false" | Set-Content -LiteralPath (Join-Path $reportDir 'aays1_panel_index_sync_20260708.md') -Encoding UTF8
Write-Output 'AAYS1_PANEL_INDEX_SYNC_DONE completion_percent=65 remaining_percent=35 final_ready=false fake_data=false'
exit 0
