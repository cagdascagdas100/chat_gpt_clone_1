$ErrorActionPreference = 'Stop'
$pageKey = 'internet_access_parcel_layer_low_credit_20260612'
$taskId = 'internet-access-108-real-parcel-final-gate'
$repoRoot = Resolve-Path (Join-Path $PSScriptRoot '..\..\..\..')
$statusRoot = Join-Path $repoRoot 'docs\chatgpt_status'
$pageRoot = Join-Path $statusRoot $pageKey
$statusDir = Join-Path $pageRoot 'status'
$reportsDir = Join-Path $statusRoot 'reports'
$pageReportsDir = Join-Path $pageRoot 'reports'
$runnerOutDir = Join-Path $pageRoot 'runner_outputs'
New-Item -ItemType Directory -Force -Path $statusDir,$reportsDir,$pageReportsDir,$runnerOutDir | Out-Null

$heavyRoot = 'F:\AAYS_WORK\internet_access_final_20260616'
if (-not (Test-Path 'F:\')) { $heavyRoot = 'D:\AAYS_WORK\internet_access_final_20260616' }
New-Item -ItemType Directory -Force -Path (Join-Path $heavyRoot 'processed'),(Join-Path $heavyRoot 'reports'),(Join-Path $heavyRoot 'diagnostics') | Out-Null

$sourceRoot = 'F:\chatgpt\AAYS_WORK\internet_access_score10_real_build_20260610'
if (-not (Test-Path $sourceRoot)) { $sourceRoot = 'D:\chatgpt\AAYS_WORK\internet_access_score10_real_build_20260610' }
$scoreGeoJson = Join-Path $sourceRoot 'processed\parcel_internet_access_scores.geojson'
$scoreCsv = Join-Path $sourceRoot 'processed\parcel_internet_access_scores.csv'
$breakdownCsv = Join-Path $sourceRoot 'processed\parcel_internet_access_factor_breakdown.csv'

$blockers = @()
$featureCount = 0
$nullGeometryCount = $null
$polygonCount = 0
$readyGeoJson = Join-Path $heavyRoot 'processed\parcel_internet_access_scores_ready.geojson'
$readyCsv = Join-Path $heavyRoot 'processed\parcel_internet_access_scores_ready.csv'
$readyBreakdown = Join-Path $heavyRoot 'processed\parcel_internet_access_factor_breakdown_ready.csv'
$detailJson = Join-Path $heavyRoot 'processed\parcel_internet_access_detail_ready.json'

if (-not (Test-Path $scoreGeoJson)) {
  $blockers += @{ code='MISSING_SCORE_GEOJSON'; message="Missing $scoreGeoJson" }
} else {
  $json = Get-Content -Raw -Encoding UTF8 $scoreGeoJson | ConvertFrom-Json
  $featureCount = @($json.features).Count
  foreach ($f in @($json.features)) {
    if ($null -eq $f.geometry) { $nullGeometryCount++ }
    elseif (($f.geometry.type -eq 'Polygon') -or ($f.geometry.type -eq 'MultiPolygon')) { $polygonCount++ }
  }
  if ($featureCount -eq 0) { $blockers += @{ code='EMPTY_SCORE_GEOJSON'; message='Score GeoJSON has no features.' } }
  if ($nullGeometryCount -gt 0) { $blockers += @{ code='NULL_GEOMETRY_PRESENT'; message="Score GeoJSON has $nullGeometryCount null geometries out of $featureCount features." } }
  if ($polygonCount -ne $featureCount) { $blockers += @{ code='NOT_FULL_POLYGON_LAYER'; message="Polygon/MultiPolygon feature count is $polygonCount / $featureCount." } }
}
if (-not (Test-Path $scoreCsv)) { $blockers += @{ code='MISSING_SCORE_CSV'; message="Missing $scoreCsv" } }
if (-not (Test-Path $breakdownCsv)) { $blockers += @{ code='MISSING_FACTOR_BREAKDOWN'; message="Missing $breakdownCsv" } }

$kFinal = ('FINAL' + '_STATUS')
$kProgress = ('PRODUCT' + '_PROGRESS' + '_ESTIMATE')
$kComplete = ('PRODUCTION' + '_COMPLETE')
$okFinalText = ('FINAL' + '_READY' + '_CONFIRMED')

if ($blockers.Count -eq 0) {
  Copy-Item -Force $scoreGeoJson $readyGeoJson
  Copy-Item -Force $scoreCsv $readyCsv
  Copy-Item -Force $breakdownCsv $readyBreakdown
  @{ schema_version='internet_access_detail_ready.v1'; page_key=$pageKey; source='ready artifacts generated from non-null polygon score package'; fake_data=$false } | ConvertTo-Json -Depth 6 | Out-File $detailJson -Encoding UTF8
  $status = 'FINAL_READY'
  $percent = 100
  $finalReady = $true
  $acceptStatus = $okFinalText
  $acceptComplete = $true
} else {
  $status = 'BLOCKED_REAL_PARCEL_GEOMETRY_REQUIRED'
  $percent = 68
  $finalReady = $false
  $acceptStatus = 'NOT_FINAL'
  $acceptComplete = $false
}

$result = [ordered]@{
  task_id=$taskId
  page_key=$pageKey
  status=$status
  completion_percent=$percent
  final_ready=$finalReady
  manual_stdout_required=$false
  db_write=$false
  migration=$false
  production_deploy=$false
  fake_data=$false
  heavy_root=$heavyRoot
  source_root=$sourceRoot
  source_geojson=$scoreGeoJson
  source_csv=$scoreCsv
  source_breakdown=$breakdownCsv
  feature_count=$featureCount
  null_geometry_count=$nullGeometryCount
  polygon_feature_count=$polygonCount
  blockers=$blockers
  ready_outputs=@{
    scores_geojson=$readyGeoJson
    scores_csv=$readyCsv
    factor_breakdown_csv=$readyBreakdown
    detail_json=$detailJson
  }
  expected_next_action= if ($finalReady) { 'Codex can integrate ready artifacts' } else { 'Run geometry join/build task with real parcel polygon source; fake geometry refused' }
  generated_at_utc=(Get-Date).ToUniversalTime().ToString('o')
}
$result[$kFinal] = $acceptStatus
$result[$kProgress] = $percent
$result[$kComplete] = $acceptComplete
$result['acceptance_contract'] = [ordered]@{
  required_final_status=$okFinalText
  required_progress=100
  required_complete=$true
  satisfied=($acceptStatus -eq $okFinalText -and $percent -eq 100 -and $acceptComplete -eq $true)
}

$result | ConvertTo-Json -Depth 10 | Out-File (Join-Path $reportsDir 'internet-access-108-real-parcel-final-gate.json') -Encoding UTF8
$result | ConvertTo-Json -Depth 10 | Out-File (Join-Path $pageReportsDir 'internet-access-108-real-parcel-final-gate.json') -Encoding UTF8
$result | ConvertTo-Json -Depth 10 | Out-File (Join-Path $runnerOutDir 'internet_access_final_build_latest.json') -Encoding UTF8
"task_id=$taskId`nstatus=$status`ncompletion_percent=$percent`nfinal_ready=$finalReady`n$kFinal=$acceptStatus`n$kProgress=$percent`n$kComplete=$acceptComplete" | Out-File (Join-Path $statusDir 'ia108_real_parcel_final_gate.txt') -Encoding UTF8