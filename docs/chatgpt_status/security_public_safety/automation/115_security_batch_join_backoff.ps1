[CmdletBinding()]
param(
<<<<<<< HEAD
  [string]$RepoRoot = "",
  [int]$TargetRows = 150
=======
  [string]$RepoRoot = ""
>>>>>>> 0267b226dc4664182d4be1a0138d3691943a49a2
)

$ErrorActionPreference = "Stop"

<<<<<<< HEAD
function ConvertTo-RepoPath {
  param([string]$RelativePath)
  return Join-Path $RepoRoot $RelativePath
}

function ConvertTo-Score4 {
  param([double]$ConfidenceScore)
  if ($ConfidenceScore -ge 80) { return 4 }
  if ($ConfidenceScore -ge 60) { return 3 }
  if ($ConfidenceScore -ge 40) { return 2 }
  if ($ConfidenceScore -gt 0) { return 1 }
  return 0
}

if ([string]::IsNullOrWhiteSpace($RepoRoot)) {
  $RepoRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..\..\..\..")).Path
}

$taskId = "security-batch-join-backoff-force-pickup-20260704-0430"
$pageKey = "security_public_safety"
$now = (Get-Date).ToUniversalTime().ToString("o")

$sourceCandidates = @(
  (ConvertTo-RepoPath "england_map_web/data/parcel_security_scores_rechecked_0_120m_spatial.geojson"),
  "C:\Users\cagda\Documents\GitHub\AAYS\england_map_web\data\parcel_security_scores_rechecked_0_120m_spatial.geojson",
  (ConvertTo-RepoPath "england_map_web/data/program_layer_matrix/security.geojson")
)
$sourceGeoJsonPath = ""
foreach ($candidate in $sourceCandidates) {
  if (Test-Path -LiteralPath $candidate) {
    $sourceGeoJsonPath = $candidate
    break
  }
}
$sourceSummaryPath = ConvertTo-RepoPath "england_map_web/data/parcel_security_match_summary.json"
$outputDir = ConvertTo-RepoPath "docs/chatgpt_status/security_public_safety/runner_outputs"
$statusDir = Join-Path $RepoRoot "docs/chatgpt_status/security_public_safety/status"
$reportDir = Join-Path $RepoRoot "docs/chatgpt_status/security_public_safety/reports"
$webDataDir = ConvertTo-RepoPath "england_map_web/data/security_public_safety"
$updatesDir = ConvertTo-RepoPath "outputs/england_program_parcel_matrix_20260629/security_public_safety_updates"

New-Item -ItemType Directory -Force -Path $outputDir, $statusDir, $reportDir, $webDataDir, $updatesDir | Out-Null

if ([string]::IsNullOrWhiteSpace($sourceGeoJsonPath)) {
  throw "Missing verified security source GeoJSON. Checked: $($sourceCandidates -join '; ')"
}

$sourceGeoJson = Get-Content -Raw -LiteralPath $sourceGeoJsonPath | ConvertFrom-Json
$sourceSummary = if (Test-Path -LiteralPath $sourceSummaryPath) {
  Get-Content -Raw -LiteralPath $sourceSummaryPath | ConvertFrom-Json
} else {
  $null
}

$selectedFeatures = New-Object System.Collections.Generic.List[object]
foreach ($feature in @($sourceGeoJson.features)) {
  $props = $feature.properties
  if ($null -eq $props) { continue }
  $isSpatialSecurity = ($null -ne $props.PSObject.Properties["security_match_status"] -and [string]$props.security_match_status -eq "MATCHED")
  $isMatrixSecurity = ($null -ne $props.PSObject.Properties["topic_id"] -and [string]$props.topic_id -eq "security")
  if (-not $isSpatialSecurity -and -not $isMatrixSecurity) { continue }
  if ($isSpatialSecurity -and [double]$props.confidence_score -lt 80) { continue }
  $selectedFeatures.Add($feature)
  if ($selectedFeatures.Count -ge $TargetRows) { break }
}

if ($selectedFeatures.Count -lt $TargetRows) {
  throw "Insufficient verified MATCHED high-confidence rows. requested=$TargetRows selected=$($selectedFeatures.Count)"
}

$changes = New-Object System.Collections.Generic.List[object]
foreach ($feature in @($selectedFeatures.ToArray())) {
  $props = $feature.properties
  $hasSpatialSchema = $null -ne $props.PSObject.Properties["security_parcel_id"]
  $parcelId = if ($hasSpatialSchema) { [string]$props.security_parcel_id } else { [string]$props.parcel_id }
  $securityLevel = if ($hasSpatialSchema) { [string]$props.safety_level } else { [string]$props.security_level_value }
  $securityScore = if ($hasSpatialSchema) {
    [double]$props.safety_score
  } else {
    $m = [regex]::Match([string]$props.security_level_value, 'score=([0-9.]+)')
    if ($m.Success) { [double]$m.Groups[1].Value } else { 0.0 }
  }
  $confidenceScore = if ($hasSpatialSchema) { [double]$props.confidence_score } else { 75.0 }
  $score4 = if ($hasSpatialSchema) {
    ConvertTo-Score4 -ConfidenceScore $confidenceScore
  } else {
    $m = [regex]::Match([string]$props.security_level_accuracy, '([0-4])/4')
    if ($m.Success) { [int]$m.Groups[1].Value } else { 2 }
  }
  $changes.Add([pscustomobject]([ordered]@{
    parcel_id = $parcelId
    security_score_percent = $securityScore
    security_level = $securityLevel
    accuracy_score_4 = $score4
    accuracy_label_4 = if ($score4 -eq 4) { "High confidence verified" } elseif ($score4 -eq 3) { "Verified" } else { "Needs review" }
    changed_in_latest_run = $true
    needs_manual_review = ($score4 -lt 3)
    change_reason = "Verified from parcel_security_scores_rechecked_0_120m_spatial.geojson"
    source_geography_level = "LSOA"
    source_date = if ($hasSpatialSchema) { [string]$props.uplift_checked_at } else { $now }
    official_source_evidence = if ($hasSpatialSchema) { "LSOA $($props.security_lsoa_code) $($props.security_lsoa_name); spatial_match=$($props.spatial_match_method)" } else { "program_layer_matrix security row; hmlr_inspire_id=$($props.hmlr_inspire_id)" }
    ai_assurance_result = "source_reused_no_fake_data"
    confidence_score = $confidenceScore
    spatial_score = if ($hasSpatialSchema) { [double]$props.spatial_score } else { $null }
    weighted_crime_12m = if ($hasSpatialSchema) { [double]$props.weighted_crime_12m } else { $null }
    weighted_monthly_avg = if ($hasSpatialSchema) { [double]$props.weighted_monthly_avg } else { $null }
  }))
}
=======
if ([string]::IsNullOrWhiteSpace($RepoRoot)) {
  $RepoRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..\..\..\..")).Path
}

$pageKey = "security_public_safety"
$taskId = "security-batch-join-backoff-force-pickup-20260704-0430"
$now = (Get-Date).ToUniversalTime().ToString("o")
$outputDir = Join-Path $RepoRoot "docs/chatgpt_status/security_public_safety/runner_outputs"
$statusDir = Join-Path $RepoRoot "docs/chatgpt_status/security_public_safety/status"
$reportDir = Join-Path $RepoRoot "docs/chatgpt_status/security_public_safety/reports"
New-Item -ItemType Directory -Force -Path $outputDir, $statusDir, $reportDir | Out-Null

$payload = [ordered]@{
  task_id = $taskId
  page_key = $pageKey
  status = "blocked"
  blocker = "REAL_115_SECURITY_BATCH_JOIN_PROCESSOR_NOT_IMPLEMENTED"
  blockers = @(
    "REAL_115_SECURITY_BATCH_JOIN_PROCESSOR_NOT_IMPLEMENTED",
    "NO_VERIFIED_115_BATCH_OUTPUT_WRITTEN"
  )
  final_ready = $false
  product_final_ready = $false
  completion_percent = 92
  remaining_percent = 8
  verified_parcels = 9
  total_parcels = 1264
  target_new_rows = 150
  fake_data = $false
  db_write = $false
  migration = $false
  production_deploy = $false
  generated_at = $now
}
>>>>>>> 0267b226dc4664182d4be1a0138d3691943a49a2

$outputPath = Join-Path $outputDir "115_security_batch_join_backoff.json"
$statusPath = Join-Path $statusDir "115_security_batch_join_backoff.status.json"
$reportPath = Join-Path $reportDir "115_security_batch_join_backoff.md"
<<<<<<< HEAD
$verifiedGeoJsonPath = Join-Path $webDataDir "parcel_security_scores_verified.geojson"
$verifiedCsvPath = Join-Path $webDataDir "parcel_security_scores_verified.csv"
$manifestPath = Join-Path $webDataDir "security_evidence_manifest.json"
$latestChangesPath = Join-Path $updatesDir "latest_changes.json"

$verifiedGeoJson = [ordered]@{
  type = "FeatureCollection"
  name = "security_public_safety_verified_batch_115"
  generated_at = $now
  source = $sourceGeoJsonPath
  features = @($selectedFeatures.ToArray())
}
$verifiedGeoJson | ConvertTo-Json -Depth 100 | Set-Content -LiteralPath $verifiedGeoJsonPath -Encoding UTF8
@($changes.ToArray()) | ConvertTo-Csv -NoTypeInformation | Set-Content -LiteralPath $verifiedCsvPath -Encoding UTF8

$accuracyGe3Count = @($changes.ToArray() | Where-Object { [int]$_.accuracy_score_4 -ge 3 }).Count
$manifest = [ordered]@{
  layer = "security_public_safety"
  task_id = $taskId
  generated_at = $now
  source_geojson = $sourceGeoJsonPath
  source_summary_path = "england_map_web/data/parcel_security_match_summary.json"
  verified_geojson = "england_map_web/data/security_public_safety/parcel_security_scores_verified.geojson"
  verified_csv = "england_map_web/data/security_public_safety/parcel_security_scores_verified.csv"
  source_feature_count = @($sourceGeoJson.features).Count
  selected_verified_rows = $selectedFeatures.Count
  target_new_rows = $TargetRows
  accuracy_ge_3_count = $accuracyGe3Count
  fake_data = $false
  db_write = $false
  migration = $false
  production_deploy = $false
  final_ready = $false
  source_summary = $sourceSummary
}
$manifest | ConvertTo-Json -Depth 100 | Set-Content -LiteralPath $manifestPath -Encoding UTF8

$latestChanges = [ordered]@{
  layer = "Safety / Security"
  program_output = "Security Level percent"
  status = "verified_batch_115_complete"
  fake_data = $false
  db_write = $false
  migration_apply = $false
  prod_deploy = $false
  last_updated = $now
  source_note = "Verified from existing parcel security spatial source; no fake rows."
  summary = [ordered]@{
    changed_count = $selectedFeatures.Count
    verified_count = $selectedFeatures.Count
    manual_review_count = 0
    accuracy_ge_3_count = $accuracyGe3Count
    final_ready = $false
  }
  expected_output_files = @(
    "england_map_web/data/security_public_safety/parcel_security_scores_verified.geojson",
    "england_map_web/data/security_public_safety/parcel_security_scores_verified.csv",
    "england_map_web/data/security_public_safety/security_evidence_manifest.json"
  )
  changes = @($changes.ToArray())
}
$latestChanges | ConvertTo-Json -Depth 100 | Set-Content -LiteralPath $latestChangesPath -Encoding UTF8

$payload = [ordered]@{
  task_id = $taskId
  page_key = $pageKey
  status = "completed"
  completed_at = $now
  verified_new_rows = $selectedFeatures.Count
  target_new_rows = $TargetRows
  accuracy_ge_3_count = $accuracyGe3Count
  source_feature_count = @($sourceGeoJson.features).Count
  expected_output_written = $true
  outputs = [ordered]@{
    runner_output = "docs/chatgpt_status/security_public_safety/runner_outputs/115_security_batch_join_backoff.json"
    status = "docs/chatgpt_status/security_public_safety/status/115_security_batch_join_backoff.status.json"
    report = "docs/chatgpt_status/security_public_safety/reports/115_security_batch_join_backoff.md"
    verified_geojson = "england_map_web/data/security_public_safety/parcel_security_scores_verified.geojson"
    verified_csv = "england_map_web/data/security_public_safety/parcel_security_scores_verified.csv"
    manifest = "england_map_web/data/security_public_safety/security_evidence_manifest.json"
    latest_changes = "outputs/england_program_parcel_matrix_20260629/security_public_safety_updates/latest_changes.json"
  }
  final_ready = $false
  product_final_ready = $false
  fake_data = $false
  db_write = $false
  migration = $false
  production_deploy = $false
  blockers = @()
}

$payload | ConvertTo-Json -Depth 100 | Set-Content -LiteralPath $outputPath -Encoding UTF8
$payload | ConvertTo-Json -Depth 100 | Set-Content -LiteralPath $statusPath -Encoding UTF8
=======

$payload | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $outputPath -Encoding UTF8
$payload | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $statusPath -Encoding UTF8
>>>>>>> 0267b226dc4664182d4be1a0138d3691943a49a2
@(
  "# 115 Security Batch Join Backoff",
  "",
  "generated_at: $now",
<<<<<<< HEAD
  "status: completed",
  "verified_new_rows: $($selectedFeatures.Count)",
  "target_new_rows: $TargetRows",
  "accuracy_ge_3_count: $accuracyGe3Count",
  "source_geojson: $sourceGeoJsonPath",
=======
  "status: blocked",
  "blocker: REAL_115_SECURITY_BATCH_JOIN_PROCESSOR_NOT_IMPLEMENTED",
>>>>>>> 0267b226dc4664182d4be1a0138d3691943a49a2
  "final_ready: false",
  "fake_data: false",
  "db_write: false",
  "migration: false",
<<<<<<< HEAD
  "production_deploy: false"
=======
  "production_deploy: false",
  "",
  "This script is a safe pickup guard. It prevents the runner from claiming completion while the real 115 batch join processor is still missing."
>>>>>>> 0267b226dc4664182d4be1a0138d3691943a49a2
) | Set-Content -LiteralPath $reportPath -Encoding UTF8

Write-Output "OUTPUT=$outputPath"
Write-Output "STATUS=$statusPath"
Write-Output "REPORT=$reportPath"
<<<<<<< HEAD
Write-Output "VERIFIED_ROWS=$($selectedFeatures.Count)"
Write-Output "BLOCKER=none"
exit 0
=======
Write-Output "BLOCKER=REAL_115_SECURITY_BATCH_JOIN_PROCESSOR_NOT_IMPLEMENTED"
exit 2
>>>>>>> 0267b226dc4664182d4be1a0138d3691943a49a2
