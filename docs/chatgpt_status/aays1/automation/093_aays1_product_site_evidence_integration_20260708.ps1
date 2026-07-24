$ErrorActionPreference = 'Stop'
$RepoRoot = $env:AAYS_REPO_ROOT
if ([string]::IsNullOrWhiteSpace($RepoRoot)) { $RepoRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..\..\..\..')).Path }
$PageKey = 'aays1'
$TaskId = if ([string]::IsNullOrWhiteSpace($env:AAYS_TASK_ID)) { 'aays1-product-site-evidence-integration-20260708' } else { $env:AAYS_TASK_ID }
$Now = (Get-Date).ToUniversalTime().ToString('o')
function JP([string]$p) { Join-Path $RepoRoot $p }
$statusDir = JP 'docs\chatgpt_status\aays1\status'
$reportDir = JP 'docs\chatgpt_status\aays1\reports'
$heartbeatDir = JP 'docs\chatgpt_status\aays1\heartbeat'
$siteDir = JP 'england_map_web\data\aays1'
New-Item -ItemType Directory -Force -Path $statusDir,$reportDir,$heartbeatDir,$siteDir | Out-Null
$manifestRel = 'england_map_web/data/security_public_safety/security_evidence_manifest.json'
$csvRel = 'england_map_web/data/security_public_safety/parcel_security_scores_verified.csv'
$geoRel = 'england_map_web/data/security_public_safety/parcel_security_scores_verified.geojson'
$manifestPath = JP ($manifestRel -replace '/', '\')
$csvPath = JP ($csvRel -replace '/', '\')
$geoPath = JP ($geoRel -replace '/', '\')
$missing = @()
foreach ($p in @($manifestPath,$csvPath,$geoPath)) { if (-not (Test-Path -LiteralPath $p)) { $missing += $p } }
if ($missing.Count -gt 0) {
  $status = [ordered]@{ page_key=$PageKey; task_id=$TaskId; status='blocked_missing_existing_evidence_files'; missing=$missing; final_ready=$false; fake_data=$false; db_write=$false; migration=$false; production_deploy=$false; updated_at=$Now }
  $status | ConvertTo-Json -Depth 20 | Set-Content -Encoding UTF8 -LiteralPath (Join-Path $statusDir '093_aays1_product_site_evidence_integration_latest.json')
  Write-Output 'AAYS1_PRODUCT_SITE_EVIDENCE_BLOCKED missing_existing_evidence_files final_ready=false'
  exit 0
}
$manifest = Get-Content -Raw -LiteralPath $manifestPath | ConvertFrom-Json -ErrorAction Stop
$rows = @(Import-Csv -LiteralPath $csvPath)
$verifiedRows = $rows.Count
$targetRows = [int]$manifest.target_new_rows
if ($targetRows -le 0) { $targetRows = [int]$manifest.selected_verified_rows }
$productStatus = [ordered]@{
  page_key=$PageKey
  task_id=$TaskId
  status='existing_verified_evidence_integrated_to_site'
  verified_rows=$verifiedRows
  target_rows=$targetRows
  evidence_manifest=$manifestRel
  verified_csv=$csvRel
  verified_geojson=$geoRel
  final_ready=$false
  blocker='real_product_source_fetch_implementation_required_for_next_batches'
  fake_data=$false
  db_write=$false
  migration=$false
  production_deploy=$false
  updated_at=$Now
}
$productStatus | ConvertTo-Json -Depth 20 | Set-Content -Encoding UTF8 -LiteralPath (Join-Path $siteDir 'aays1_product_status_latest.json')
$productStatus | ConvertTo-Json -Depth 20 | Set-Content -Encoding UTF8 -LiteralPath (Join-Path $statusDir '093_aays1_product_site_evidence_integration_latest.json')
$panelPath = JP 'england_map_web\data\runner_panel\page_status_index.json'
if (Test-Path -LiteralPath $panelPath) {
  $idx = Get-Content -Raw -LiteralPath $panelPath | ConvertFrom-Json -ErrorAction Stop
  foreach ($pg in @($idx.pages)) {
    if ([string]$pg.page_key -eq $PageKey) {
      $pg.runner_status = 'ProductEvidenceVisible'
      $pg.single_runner_status = 'ProductEvidenceVisible'
      $pg.latest_queue_status = 'done'
      $pg.latest_task_id = $TaskId
      $pg.latest_report = 'docs/chatgpt_status/aays1/reports/093_aays1_product_site_evidence_integration_latest.md'
      $pg.latest_blocker = 'real_product_source_fetch_implementation_required_for_next_batches'
      $pg.blockers = @('real_product_source_fetch_implementation_required_for_next_batches')
      $pg.completion_percent = 35
      $pg.remaining_percent = 65
      $pg.final_ready = $false
      $pg.heartbeat_at = $Now
      $pg.last_heartbeat_at = $Now
      $pg.verified_new_rows = $verifiedRows
      $pg.target_new_rows = $targetRows
      $pg.evidence_paths = @($manifestRel,$csvRel,$geoRel,'england_map_web/data/aays1/aays1_product_status_latest.json')
    }
  }
  $idx.updated_at = $Now
  $idx | ConvertTo-Json -Depth 100 | Set-Content -Encoding UTF8 -LiteralPath $panelPath
}
@"
# aays1 product site evidence integration

status: existing_verified_evidence_integrated_to_site
verified_rows: $verifiedRows
target_rows: $targetRows
site_output: england_map_web/data/aays1/aays1_product_status_latest.json
blocker: real_product_source_fetch_implementation_required_for_next_batches
final_ready: false
fake_data: false
db_write: false
migration: false
production_deploy: false
"@ | Set-Content -Encoding UTF8 -LiteralPath (Join-Path $reportDir '093_aays1_product_site_evidence_integration_latest.md')
"aays1 product site evidence integrated $Now rows=$verifiedRows final_ready=false" | Set-Content -Encoding UTF8 -LiteralPath (Join-Path $heartbeatDir '093_aays1_product_site_evidence_integration_latest.txt')
Write-Output "AAYS1_PRODUCT_SITE_EVIDENCE_INTEGRATED rows=$verifiedRows target=$targetRows final_ready=false"
exit 0
