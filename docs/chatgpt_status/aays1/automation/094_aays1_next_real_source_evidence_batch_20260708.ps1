$ErrorActionPreference = 'Stop'

$RepoRoot = $env:AAYS_REPO_ROOT
if ([string]::IsNullOrWhiteSpace($RepoRoot)) {
  $RepoRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..\..\..\..')).Path
}

$PageKey = 'aays1'
$TaskId = if ([string]::IsNullOrWhiteSpace($env:AAYS_TASK_ID)) { 'aays1-next-real-source-evidence-batch-20260708' } else { $env:AAYS_TASK_ID }
$Now = (Get-Date).ToUniversalTime().ToString('o')
$Stamp = Get-Date -Format 'yyyyMMdd_HHmmss'

function JP([string]$p) { Join-Path $RepoRoot ($p -replace '/', '\') }

$StatusDir = JP 'docs/chatgpt_status/aays1/status'
$ReportDir = JP 'docs/chatgpt_status/aays1/reports'
$HeartbeatDir = JP 'docs/chatgpt_status/aays1/heartbeat'
$RunnerOutputDir = JP 'docs/chatgpt_status/aays1/runner_outputs'
$SecurityDataDir = JP 'england_map_web/data/security_public_safety'
$AaysDataDir = JP 'england_map_web/data/aays1'
New-Item -ItemType Directory -Force -Path $StatusDir,$ReportDir,$HeartbeatDir,$RunnerOutputDir,$SecurityDataDir,$AaysDataDir | Out-Null

function Write-AaysStatusAndExit([string]$StatusName, [string]$Blocker, [object[]]$ExtraRows, [object[]]$MissingPaths, [int]$ExitCode) {
  $status = [ordered]@{
    page_key = $PageKey
    task_id = $TaskId
    status = $StatusName
    blocker = $Blocker
    candidate_rows = @($ExtraRows).Count
    missing_or_empty_source_paths = $MissingPaths
    source_system = 'data.police.uk'
    source_api_last_updated_url = 'https://data.police.uk/api/crime-last-updated'
    source_api_crimes_url_template = 'https://data.police.uk/api/crimes-street/all-crime?lat={lat}&lng={lng}&date={yyyy-MM}'
    completion_percent = 35
    remaining_percent = 65
    final_ready = $false
    fake_data = $false
    db_write = $false
    migration = $false
    production_deploy = $false
    updated_at = $Now
  }

  $statusPath = Join-Path $StatusDir '094_aays1_next_real_source_evidence_batch_latest.json'
  $status | ConvertTo-Json -Depth 100 | Set-Content -Encoding UTF8 -LiteralPath $statusPath

  $runnerOutputPath = Join-Path $RunnerOutputDir "094_aays1_next_real_source_evidence_batch_$Stamp.json"
  $status | ConvertTo-Json -Depth 100 | Set-Content -Encoding UTF8 -LiteralPath $runnerOutputPath

  if (@($ExtraRows).Count -gt 0) {
    $jsonOut = Join-Path $SecurityDataDir "aays1_next_source_evidence_candidates_$Stamp.json"
    [ordered]@{
      type = 'aays1_security_public_safety_source_candidates'
      generated_at = $Now
      page_key = $PageKey
      task_id = $TaskId
      source = 'Police.uk Data API / data.police.uk'
      rows = $ExtraRows
      final_ready = $false
      fake_data = $false
      db_write = $false
      migration = $false
      production_deploy = $false
      needs_manual_review = $true
    } | ConvertTo-Json -Depth 100 | Set-Content -Encoding UTF8 -LiteralPath $jsonOut
    $status['candidate_output'] = ($jsonOut.Substring($RepoRoot.Length).TrimStart('\') -replace '\\','/')
    $status | ConvertTo-Json -Depth 100 | Set-Content -Encoding UTF8 -LiteralPath $statusPath
  }

  $productStatus = [ordered]@{
    page_key = $PageKey
    task_id = $TaskId
    status = $StatusName
    blocker = $Blocker
    candidate_rows = @($ExtraRows).Count
    verified_rows_added = 0
    completion_percent = 35
    remaining_percent = 65
    final_ready = $false
    fake_data = $false
    db_write = $false
    migration = $false
    production_deploy = $false
    updated_at = $Now
  }
  $productStatus | ConvertTo-Json -Depth 100 | Set-Content -Encoding UTF8 -LiteralPath (Join-Path $AaysDataDir 'aays1_product_status_latest.json')

  $panelPath = JP 'england_map_web/data/runner_panel/page_status_index.json'
  if (Test-Path -LiteralPath $panelPath) {
    try {
      $idx = Get-Content -Raw -LiteralPath $panelPath | ConvertFrom-Json -ErrorAction Stop
      foreach ($pg in @($idx.pages)) {
        if ([string]$pg.page_key -eq $PageKey) {
          $pg.runner_status = $StatusName
          $pg.single_runner_status = $StatusName
          $pg.latest_task_id = $TaskId
          $pg.latest_queue_status = $(if (@($ExtraRows).Count -gt 0) { 'candidate_source_fetched' } else { 'blocked' })
          $pg.latest_report = 'docs/chatgpt_status/aays1/reports/094_aays1_next_real_source_evidence_batch_latest.md'
          $pg.latest_blocker = $Blocker
          $pg.blockers = @($Blocker)
          $pg.completion_percent = 35
          $pg.remaining_percent = 65
          $pg.final_ready = $false
          $pg.heartbeat_at = $Now
          $pg.last_heartbeat_at = $Now
          $pg.verified_new_rows = 0
          $pg.target_new_rows = 150
        }
      }
      $idx.updated_at = $Now
      $idx | ConvertTo-Json -Depth 100 | Set-Content -Encoding UTF8 -LiteralPath $panelPath
    } catch {
      $Blocker = "$Blocker;panel_update_failed=$($_.Exception.Message)"
    }
  }

  @"
# 094 aays1 next real source evidence batch

status: $StatusName
task_id: $TaskId
candidate_rows: $(@($ExtraRows).Count)
verified_rows_added: 0
completion_percent: 35
remaining_percent: 65
blocker: $Blocker
source_system: Police.uk Data API / data.police.uk
final_ready: false
fake_data: false
db_write: false
migration: false
production_deploy: false

Notes:
- This task never fabricates security evidence.
- Candidate rows are not merged into verified outputs until review/acceptance criteria are satisfied.
- If no non-verified candidate source rows exist, the blocker is explicit and metrics remain unchanged.
"@ | Set-Content -Encoding UTF8 -LiteralPath (Join-Path $ReportDir '094_aays1_next_real_source_evidence_batch_latest.md')

  "aays1 094 source evidence batch $StatusName $Now candidates=$(@($ExtraRows).Count) final_ready=false" | Set-Content -Encoding UTF8 -LiteralPath (Join-Path $HeartbeatDir '094_aays1_next_real_source_evidence_batch_latest.txt')
  Write-Output "AAYS1_094_SOURCE_EVIDENCE_BATCH status=$StatusName candidates=$(@($ExtraRows).Count) final_ready=false fake_data=false db_write=false migration=false production_deploy=false blocker=$Blocker"
  exit $ExitCode
}

$sourceRelCandidates = @(
  'england_map_web/data/parcel_security_scores_rechecked_0_120m_spatial.geojson',
  'england_map_web/data/security_public_safety/parcel_security_scores_verified.geojson',
  'england_map_web/data/program_layer_matrix/security_public_safety.geojson',
  'england_map_web/data/program_layer_matrix/security.geojson'
)

$sourceFeatures = @()
$sourceRelUsed = $null
$missingOrEmpty = @()
foreach ($rel in $sourceRelCandidates) {
  $path = JP $rel
  if (-not (Test-Path -LiteralPath $path)) {
    $missingOrEmpty += "${rel}:missing"
    continue
  }
  try {
    $raw = Get-Content -Raw -LiteralPath $path
    if ([string]::IsNullOrWhiteSpace($raw)) {
      $missingOrEmpty += "${rel}:empty"
      continue
    }
    $geo = $raw | ConvertFrom-Json -ErrorAction Stop
    $features = @($geo.features)
    if ($features.Count -gt 0) {
      $sourceFeatures = $features
      $sourceRelUsed = $rel
      break
    }
    $missingOrEmpty += "${rel}:no_features"
  } catch {
    $missingOrEmpty += "${rel}:parse_error=$($_.Exception.Message)"
  }
}

if ($sourceFeatures.Count -eq 0) {
  Write-AaysStatusAndExit 'blocked_missing_nonempty_source_geojson' 'missing_expansion_source_geojson' @() $missingOrEmpty 0
}

$verifiedIds = @{}
$verifiedCsvPath = JP 'england_map_web/data/security_public_safety/parcel_security_scores_verified.csv'
if (Test-Path -LiteralPath $verifiedCsvPath) {
  try {
    foreach ($row in @(Import-Csv -LiteralPath $verifiedCsvPath)) {
      if (-not [string]::IsNullOrWhiteSpace($row.parcel_id)) { $verifiedIds[[string]$row.parcel_id] = $true }
    }
  } catch {
  }
}

function Get-PropValue($props, [string[]]$names) {
  foreach ($name in $names) {
    if ($null -ne $props.$name -and -not [string]::IsNullOrWhiteSpace([string]$props.$name)) {
      return [string]$props.$name
    }
  }
  return $null
}

function Get-PointLonLat($feature) {
  if ($null -eq $feature.geometry) { return $null }
  if ([string]$feature.geometry.type -ne 'Point') { return $null }
  $coords = @($feature.geometry.coordinates)
  if ($coords.Count -lt 2) { return $null }
  return [double[]]@([double]$coords[0], [double]$coords[1])
}

$candidates = @()
foreach ($f in $sourceFeatures) {
  $props = $f.properties
  $parcelId = Get-PropValue $props @('parcel_id','security_parcel_id','parcel_ref','id')
  if ([string]::IsNullOrWhiteSpace($parcelId)) { continue }
  if ($verifiedIds.ContainsKey($parcelId)) { continue }
  $ll = Get-PointLonLat $f
  if ($null -eq $ll) { continue }
  $candidates += [ordered]@{ parcel_id=$parcelId; lon=$ll[0]; lat=$ll[1]; source_input=$sourceRelUsed }
  if ($candidates.Count -ge 10) { break }
}

if ($candidates.Count -eq 0) {
  Write-AaysStatusAndExit 'blocked_no_unverified_candidate_coordinates' 'next_batch_source_fetch_requires_nonverified_parcel_coordinates' @() $missingOrEmpty 0
}

try {
  $lastUpdated = Invoke-RestMethod -Method GET -Uri 'https://data.police.uk/api/crime-last-updated' -TimeoutSec 30
  $sourceMonth = (Get-Date $lastUpdated.date).ToString('yyyy-MM')
} catch {
  Write-AaysStatusAndExit 'blocked_police_api_last_updated_failed' "police_api_last_updated_failed=$($_.Exception.Message)" @() $missingOrEmpty 0
}

$weights = @{
  'anti-social-behaviour' = 0.5
  'bicycle-theft' = 1.0
  'burglary' = 3.0
  'criminal-damage-arson' = 2.0
  'drugs' = 2.0
  'other-crime' = 2.0
  'other-theft' = 1.5
  'possession-of-weapons' = 4.0
  'public-order' = 2.5
  'robbery' = 4.0
  'shoplifting' = 1.0
  'theft-from-the-person' = 2.0
  'vehicle-crime' = 2.5
  'violent-crime' = 4.0
}

$resultRows = @()
foreach ($c in $candidates) {
  $lat = [Math]::Round([double]$c.lat, 6)
  $lon = [Math]::Round([double]$c.lon, 6)
  $url = "https://data.police.uk/api/crimes-street/all-crime?lat=$lat&lng=$lon&date=$sourceMonth"
  try {
    $crimes = @(Invoke-RestMethod -Method GET -Uri $url -TimeoutSec 45)
  } catch {
    $resultRows += [ordered]@{
      parcel_id = $c.parcel_id
      source_url = $url
      source_date = $sourceMonth
      fetch_status = 'blocked_fetch_failed'
      fetch_error = $_.Exception.Message
      needs_manual_review = $true
      final_ready = $false
      fake_data = $false
    }
    continue
  }

  $weighted = 0.0
  $categoryCounts = @{}
  foreach ($crime in $crimes) {
    $cat = [string]$crime.category
    if ([string]::IsNullOrWhiteSpace($cat)) { $cat = 'unknown' }
    if (-not $categoryCounts.ContainsKey($cat)) { $categoryCounts[$cat] = 0 }
    $categoryCounts[$cat] += 1
    $w = if ($weights.ContainsKey($cat)) { [double]$weights[$cat] } else { 1.0 }
    $weighted += $w
  }

  $score = [Math]::Max(0, [Math]::Min(100, 100 - ($weighted * 3.0)))
  $level = if ($score -ge 80) { 'Very Good Security' } elseif ($score -ge 60) { 'Good Security' } elseif ($score -ge 40) { 'Medium Security' } elseif ($score -ge 20) { 'Low Security' } else { 'Very Low Security' }

  $resultRows += [ordered]@{
    parcel_id = $c.parcel_id
    lat = $lat
    lng = $lon
    source_url = $url
    source_date = $sourceMonth
    official_source_evidence = ('Police.uk street crime API; month={0}; crime_count={1}; category_counts={2}' -f $sourceMonth, $crimes.Count, (($categoryCounts.GetEnumerator() | Sort-Object Name | ForEach-Object { '{0}:{1}' -f $_.Key, $_.Value }) -join ';'))
    source_geography_level = 'point_radius_police_uk_street'
    matching_method = 'parcel_point_to_police_uk_lat_lng_query'
    weighted_crime_month = [Math]::Round($weighted, 3)
    security_score_percent_candidate = [Math]::Round($score, 2)
    security_level_candidate = $level
    accuracy_score_4_candidate = 3
    accuracy_label_4_candidate = 'Official API candidate - manual review required'
    confidence_score_candidate = 75
    changed_in_latest_run = $true
    needs_manual_review = $true
    ai_assurance_result = 'SOURCE_FETCHED_NO_FAKE_DATA_REVIEW_REQUIRED'
    final_ready = $false
    fake_data = $false
  }
}

if ($resultRows.Count -eq 0) {
  Write-AaysStatusAndExit 'blocked_no_candidate_rows_after_source_fetch' 'police_api_returned_no_usable_candidate_rows' @() $missingOrEmpty 0
}

Write-AaysStatusAndExit 'source_candidates_fetched_manual_review_required' 'candidate_rows_require_review_before_verified_merge' $resultRows $missingOrEmpty 0
