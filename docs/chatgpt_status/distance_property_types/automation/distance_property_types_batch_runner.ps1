# AAYS / TerraYield - Distance to Nearby Property Types batch runner
# Safe bootstrap/validation runner. It does not invent parcel/property evidence.

$ErrorActionPreference = "Stop"

$pageKey = "distance_property_types"
$layerName = "Distance to Nearby Property Types"
$taskId = if ($env:DISTANCE_PROPERTY_TYPES_TASK_ID) { $env:DISTANCE_PROPERTY_TYPES_TASK_ID } else { "distance_property_types_bootstrap_20260703" }
$repoRoot = if ($env:AAYS_REPO_ROOT) { $env:AAYS_REPO_ROOT } else { "F:\chatgpt\chat_gpt_clone_1_main" }
$runStartedAt = (Get-Date).ToUniversalTime().ToString("o")

$dataDir = Join-Path $repoRoot "england_map_web\data\distance_property_types"
$reportDir = Join-Path $repoRoot "docs\chatgpt_status\distance_property_types\reports"
$inputDir = Join-Path $repoRoot "docs\chatgpt_status\distance_property_types\inputs"
New-Item -ItemType Directory -Force -Path $dataDir,$reportDir,$inputDir | Out-Null

$csvOutput = Join-Path $dataDir "distance_property_types_verified.csv"
$geojsonOutput = Join-Path $dataDir "distance_property_types_verified.geojson"
$manifestOutput = Join-Path $dataDir "distance_property_types_evidence_manifest.json"
$manualReviewOutput = Join-Path $reportDir "distance_property_types_manual_review_latest.csv"
$progressOutput = Join-Path $reportDir "distance_property_types_progress_latest.md"

$columns = @(
  "parcel_id", "selected_property_type", "selected_color_category",
  "nearest_industrial_unit_distance_m", "nearest_detached_home_distance_m", "nearest_retail_property_distance_m",
  "nearest_apartment_building_distance_m", "nearest_office_building_distance_m", "nearest_mixed_building_distance_m",
  "selected_match_distance_m", "official_source_evidence", "web_source_evidence", "map_source_evidence",
  "photo_ai_evidence", "photo_ai_image_path", "photo_ai_model_or_tool", "photo_ai_observation",
  "source_date", "matching_method", "conflict_status", "needs_manual_review", "accuracy_score_4",
  "accuracy_label_4", "explanation", "last_updated", "changed_in_latest_run", "change_reason"
)
$reviewColumns = @(
  "parcel_id", "candidate_property_type", "ai_property_type", "official_source_property_type", "web_source_property_type",
  "conflict_status", "accuracy_score_4", "missing_evidence", "manual_question", "source_links_or_files",
  "photo_ai_image_path", "suggested_next_action"
)
$allowedTypes = @("Industrial Unit", "Detached Home", "Retail Property", "Apartment Building", "Office Building", "Mixed Building", "Unknown")
$colorContract = [ordered]@{
  "Industrial Unit" = "#7c2d12"
  "Detached Home" = "#16a34a"
  "Retail Property" = "#f97316"
  "Apartment Building" = "#2563eb"
  "Office Building" = "#7c3aed"
  "Mixed Building" = "#db2777"
  "Unknown" = "#6b7280"
  "Manual Review" = "#6b7280"
}

function Write-Utf8NoBom([string]$Path, [string]$Content) {
  $encoding = New-Object System.Text.UTF8Encoding($false)
  [System.IO.File]::WriteAllText($Path, $Content, $encoding)
}

function Ensure-HeaderCsv([string]$Path, [string[]]$Header) {
  if (-not (Test-Path $Path)) {
    Write-Utf8NoBom -Path $Path -Content (($Header -join ",") + "`n")
  }
}

Ensure-HeaderCsv -Path $csvOutput -Header $columns
Ensure-HeaderCsv -Path $manualReviewOutput -Header $reviewColumns

if (-not (Test-Path $geojsonOutput)) {
  $emptyGeoJson = [ordered]@{
    type = "FeatureCollection"
    name = "distance_property_types_verified"
    features = @()
    metadata = [ordered]@{
      page_key = $pageKey
      layer_name = $layerName
      fake_data = $false
      note = "Empty bootstrap output. Populate only with real evidence-backed parcel rows."
    }
  } | ConvertTo-Json -Depth 10
  Write-Utf8NoBom -Path $geojsonOutput -Content ($emptyGeoJson + "`n")
}

$inputCandidates = @()
if ($env:DISTANCE_PROPERTY_TYPES_INPUT) { $inputCandidates += $env:DISTANCE_PROPERTY_TYPES_INPUT }
$inputCandidates += (Join-Path $inputDir "distance_property_types_source_candidates.csv")
$inputCandidates += (Join-Path $dataDir "distance_property_types_source_candidates.csv")
$sourceInput = $inputCandidates | Where-Object { $_ -and (Test-Path $_) } | Select-Object -First 1

$blockers = New-Object System.Collections.Generic.List[string]
$warnings = New-Object System.Collections.Generic.List[string]
$processedRows = 0
$verifiedRows = 0
$manualReviewRows = 0
$accuracyGe3Rows = 0
$accuracyLt3Rows = 0
$inputRows = 0

if (-not $sourceInput) {
  $blockers.Add("missing_real_evidence_rows")
  $blockers.Add("missing_verified_parcel_input_batch")
  $blockers.Add("no_official_web_map_photo_evidence_available_to_runner")
} else {
  $rows = Import-Csv -Path $sourceInput
  $inputRows = @($rows).Count
  if ($inputRows -eq 0) {
    $blockers.Add("missing_real_evidence_rows")
    $blockers.Add("source_candidate_csv_is_header_only")
  }

  $accepted = New-Object System.Collections.Generic.List[object]
  $manual = New-Object System.Collections.Generic.List[object]

  foreach ($row in $rows) {
    $processedRows++
    $parcelId = [string]$row.parcel_id
    $ptype = if ($row.PSObject.Properties.Name -contains "selected_property_type") { [string]$row.selected_property_type } else { [string]$row.candidate_property_type }
    $scoreText = [string]$row.accuracy_score_4
    $official = [string]$row.official_source_evidence
    $web = [string]$row.web_source_evidence
    $map = [string]$row.map_source_evidence
    $photo = [string]$row.photo_ai_evidence
    $conflict = [string]$row.conflict_status

    $score = 0.0
    [void][double]::TryParse($scoreText, [Globalization.NumberStyles]::Float, [Globalization.CultureInfo]::InvariantCulture, [ref]$score)
    $hasEvidence = -not [string]::IsNullOrWhiteSpace($official) -or -not [string]::IsNullOrWhiteSpace($web) -or -not [string]::IsNullOrWhiteSpace($map) -or (-not [string]::IsNullOrWhiteSpace($photo) -and $photo -ne "not_available")
    $validType = $allowedTypes -contains $ptype
    $needsReview = $false
    $missing = @()

    if ([string]::IsNullOrWhiteSpace($parcelId)) { $needsReview = $true; $missing += "parcel_id" }
    if (-not $validType -or $ptype -eq "Unknown") { $needsReview = $true; $missing += "valid_property_type" }
    if ($score -lt 3.0) { $needsReview = $true; $missing += "accuracy_score_4_ge_3" }
    if (-not $hasEvidence) { $needsReview = $true; $missing += "evidence" }
    if ($conflict -and $conflict -ne "none" -and $conflict -ne "no_conflict") { $needsReview = $true; $missing += "conflict_resolution" }

    if ($score -ge 3.0) { $accuracyGe3Rows++ } else { $accuracyLt3Rows++ }

    if ($needsReview) {
      $manualReviewRows++
      $manual.Add([pscustomobject]@{
        parcel_id = $parcelId
        candidate_property_type = $ptype
        ai_property_type = [string]$row.ai_property_type
        official_source_property_type = [string]$row.official_source_property_type
        web_source_property_type = [string]$row.web_source_property_type
        conflict_status = if ($conflict) { $conflict } else { "insufficient_evidence" }
        accuracy_score_4 = $score.ToString("0.##", [Globalization.CultureInfo]::InvariantCulture)
        missing_evidence = ($missing -join ";")
        manual_question = "Can this parcel/property type be supported by official, web, map, or photo evidence?"
        source_links_or_files = ((@($official,$web,$map) | Where-Object { $_ }) -join " | ")
        photo_ai_image_path = [string]$row.photo_ai_image_path
        suggested_next_action = "Collect/verify official or web/map/photo evidence before acceptance."
      })
    } else {
      $verifiedRows++
      $accepted.Add($row)
    }
  }

  if ($accepted.Count -gt 0) {
    $accepted | Export-Csv -NoTypeInformation -Encoding UTF8 -Path $csvOutput
  }
  if ($manual.Count -gt 0) {
    $manual | Export-Csv -NoTypeInformation -Encoding UTF8 -Path $manualReviewOutput
  }

  if ($verifiedRows -gt 0) {
    $blockers.Add("geojson_geometry_generation_requires_source_geometry_or_existing_feature_collection")
    $blockers.Add("site_integration_not_verified_with_real_features")
  }
}

$manifest = [ordered]@{
  page_key = $pageKey
  layer_name = $layerName
  status = if ($blockers.Count -eq 0) { "ready_for_site_verification" } else { "blocked" }
  fake_data = $false
  db_write = $false
  ddl = $false
  migration_apply = $false
  prod_deploy = $false
  source_input = if ($sourceInput) { $sourceInput } else { $null }
  allowed_property_types = $allowedTypes
  color_contract = $colorContract
  required_columns = $columns
  accuracy_target = ">=3.0/4"
  changed_in_latest_run_filter = "changed_in_latest_run=true"
  remaining_blockers = @($blockers)
  warnings = @($warnings)
  run_started_at = $runStartedAt
  run_finished_at = (Get-Date).ToUniversalTime().ToString("o")
}
Write-Utf8NoBom -Path $manifestOutput -Content (($manifest | ConvertTo-Json -Depth 12) + "`n")

$runFinishedAt = (Get-Date).ToUniversalTime().ToString("o")
$status = if ($blockers.Count -eq 0) { "READY_FOR_SITE_VERIFICATION" } else { "BLOCKED_INPUT_REQUIRED" }
$completionPercent = if ($verifiedRows -gt 0) { 45 } elseif ($inputRows -gt 0) { 38 } else { 35 }
$blockerText = if ($blockers.Count -gt 0) { ($blockers | ForEach-Object { "- $_" }) -join "`n" } else { "- none" }

$report = @"
# Distance Property Types - Progress Latest

page_key=$pageKey
task_id=$taskId
run_started_at=$runStartedAt
run_finished_at=$runFinishedAt
layer_name=$layerName
status=$status
completion_percent=$completionPercent
final_ready=false
product_final_ready=false

## Counters

input_rows=$inputRows
processed_rows=$processedRows
verified_rows=$verifiedRows
manual_review_rows=$manualReviewRows
accuracy_ge_3_rows=$accuracyGe3Rows
accuracy_lt_3_rows=$accuracyLt3Rows

## Outputs

geojson_output=$geojsonOutput
csv_output=$csvOutput
manifest_output=$manifestOutput
manual_review_output=$manualReviewOutput

## Safety flags

fake_data=false
db_write=false
ddl=false
migration_apply=false
prod_deploy=false

## Remaining blockers

$blockerText

## Next batch

next_batch=Provide or generate a real source batch with parcel_id, geometry/centroid, candidate property type, distance fields, and official/web/map/photo evidence. Rows below 3.0/4 or with conflict must remain in manual review.

## Next single action

next_single_action=Run evidence-backed source batch through this script, then verify GeoJSON rendering and the Guncel degisiklikler filter in the local site.
"@
Write-Utf8NoBom -Path $progressOutput -Content $report

$result = [ordered]@{
  page_key = $pageKey
  task_id = $taskId
  status = $status
  final_ready = $false
  product_final_ready = $false
  fake_data = $false
  db_write = $false
  ddl = $false
  migration_apply = $false
  prod_deploy = $false
  input_rows = $inputRows
  processed_rows = $processedRows
  verified_rows = $verifiedRows
  manual_review_rows = $manualReviewRows
  remaining_blockers = @($blockers)
  progress_report = $progressOutput
}
$result | ConvertTo-Json -Depth 8
