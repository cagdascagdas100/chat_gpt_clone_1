param(
  [string]$RepoRoot = $env:AAYS_REPO_ROOT,
  [string]$TaskId = $env:AAYS_TASK_ID
)

$ErrorActionPreference = 'Stop'
if ([string]::IsNullOrWhiteSpace($RepoRoot)) { $RepoRoot = (Get-Location).Path }
if ([string]::IsNullOrWhiteSpace($TaskId)) { $TaskId = 'topography_shared_runner_task_20260704' }
$RepoRoot = [System.IO.Path]::GetFullPath($RepoRoot)
Set-Location -LiteralPath $RepoRoot

function Ensure-Dir([string]$Path) { if ($Path -and -not (Test-Path -LiteralPath $Path)) { New-Item -ItemType Directory -Force -Path $Path | Out-Null } }
function Write-Utf8([string]$Rel, [string]$Content) {
  $full = Join-Path $RepoRoot ($Rel -replace '/', '\')
  Ensure-Dir (Split-Path -Parent $full)
  [System.IO.File]::WriteAllText($full, $Content, [System.Text.UTF8Encoding]::new($false))
}
function Json([object]$Obj) { return ($Obj | ConvertTo-Json -Depth 30) }
function As-Bool([object]$Value) {
  if ($Value -is [bool]) { return $Value }
  if ($null -eq $Value) { return $false }
  return ([string]$Value).Trim().ToLowerInvariant() -in @('true','1','yes','y')
}
function To-DoubleSafe([object]$Value) {
  $s = ([string]$Value).Trim().Replace(',', '.')
  $d = 0.0
  if ([double]::TryParse($s, [System.Globalization.NumberStyles]::Float, [System.Globalization.CultureInfo]::InvariantCulture, [ref]$d)) { return $d }
  return $null
}

$required = @('parcel_id','parcel_ref','elevation_sea_level_m','regional_average_elevation_m','elevation_difference_regional_average_m','elevation_class','color_category','confidence_rating','confidence_percent','source','source_url','source_date','matching_method','calculation_explanation','accuracy_score_4','needs_manual_review','changed_in_latest_run')
$header = ($required -join ',')
$csvRel = 'docs/chatgpt_status/topography/fixtures/topography_verified_rows_template_20260703.csv'
$statusRel = 'docs/chatgpt_status/topography/status/topography_current_status_20260703.txt'
$reportRel = 'docs/chatgpt_status/topography/reports/topography_progress_latest_20260703.md'
$latestRel = 'outputs/england_program_parcel_matrix_20260629/topography_updates/latest_changes.json'
$geoRel = 'england_map_web/data/program_layer_matrix/topography.geojson'
$heartbeatRel = 'docs/chatgpt_status/topography/heartbeat/topography_shared_runner_task_20260704_heartbeat.json'
$gateRel = "docs/chatgpt_status/topography/status/${TaskId}_gate.json"

$blockers = New-Object System.Collections.Generic.List[string]
$csvPath = Join-Path $RepoRoot ($csvRel -replace '/', '\')
if (-not (Test-Path -LiteralPath $csvPath)) {
  Write-Utf8 $csvRel $header
  $blockers.Add('verified_rows_csv_created_header_only')
}

$rows = @()
try { $rows = @(Import-Csv -LiteralPath $csvPath) } catch { $blockers.Add('verified_rows_csv_parse_failed') }
if ($rows.Count -eq 0) { $blockers.Add('verified_rows_missing') }

$validRows = @()
foreach ($r in $rows) {
  $ok = $true
  foreach ($f in $required) {
    if (-not ($r.PSObject.Properties.Name -contains $f) -or [string]::IsNullOrWhiteSpace([string]$r.$f)) { $ok = $false }
  }
  $acc = To-DoubleSafe $r.accuracy_score_4
  $manual = As-Bool $r.needs_manual_review
  $officialSource = (([string]$r.source + ' ' + [string]$r.source_url) -match '(?i)(Copernicus|official|Environment Agency|DEFRA|Ordnance Survey|gov\.uk)')
  if ($ok -and $acc -ne $null -and $acc -ge 3 -and -not $manual -and $officialSource) { $validRows += $r }
}
if ($rows.Count -gt 0 -and $validRows.Count -eq 0) { $blockers.Add('no_official_verified_rows_passing_gate') }

$uiPatchOk = (Test-Path -LiteralPath (Join-Path $RepoRoot 'england_map_web/topography_panel_runtime_patch_20260704.js')) -and (Test-Path -LiteralPath (Join-Path $RepoRoot 'outputs/england_program_parcel_matrix_20260629/topography_matrix_runtime_patch_20260704.js'))
if (-not $uiPatchOk) { $blockers.Add('ui_runtime_patch_missing') }

$geoPath = Join-Path $RepoRoot ($geoRel -replace '/', '\')
$geoPatchOk = $false
if (Test-Path -LiteralPath $geoPath) {
  try {
    $geo = Get-Content -LiteralPath $geoPath -Raw | ConvertFrom-Json
    $matched = 0
    if ($validRows.Count -gt 0 -and $geo.features) {
      foreach ($feat in @($geo.features)) {
        $p = $feat.properties
        if ($null -eq $p) { continue }
        $pid = [string]$p.parcel_id
        $pref = [string]$p.parcel_ref
        $match = $validRows | Where-Object { (([string]$_.parcel_id -eq $pid) -and $pid) -or (([string]$_.parcel_ref -eq $pref) -and $pref) } | Select-Object -First 1
        if ($match) {
          foreach ($f in $required) { $p | Add-Member -NotePropertyName $f -NotePropertyValue $match.$f -Force }
          $p | Add-Member -NotePropertyName 'topography_updated_at' -NotePropertyValue ((Get-Date).ToUniversalTime().ToString('s') + 'Z') -Force
          $matched++
        }
      }
      if ($matched -gt 0) {
        Write-Utf8 $geoRel (Json $geo)
        $geoPatchOk = $true
      } else {
        $blockers.Add('no_geojson_feature_matched_verified_rows')
      }
    }
  } catch { $blockers.Add('topography_geojson_patch_failed') }
} else {
  $blockers.Add('topography_geojson_missing')
}

$sourceGate = ($validRows.Count -gt 0)
$uiGate = [bool]$uiPatchOk
$manualReview = -not ($sourceGate -and $uiGate -and $geoPatchOk)
$changes = @()
foreach ($r in $validRows) {
  $changes += [ordered]@{
    parcel_id = $r.parcel_id
    parcel_ref = $r.parcel_ref
    elevation_sea_level_m = To-DoubleSafe $r.elevation_sea_level_m
    regional_average_elevation_m = To-DoubleSafe $r.regional_average_elevation_m
    elevation_difference_regional_average_m = To-DoubleSafe $r.elevation_difference_regional_average_m
    elevation_class = $r.elevation_class
    color_category = $r.color_category
    confidence_rating = $r.confidence_rating
    confidence_percent = To-DoubleSafe $r.confidence_percent
    source = $r.source
    source_url = $r.source_url
    source_date = $r.source_date
    matching_method = $r.matching_method
    calculation_explanation = $r.calculation_explanation
    accuracy_score_4 = $r.accuracy_score_4
    needs_manual_review = As-Bool $r.needs_manual_review
    changed_in_latest_run = As-Bool $r.changed_in_latest_run
  }
}

$completion = 25
$accuracy = '0/4'
if ($sourceGate) { $completion = 55; $accuracy = '3/4' }
if ($sourceGate -and $uiGate -and $geoPatchOk) { $completion = 80; $accuracy = '3.5/4' }
$finalReady = $false

$payload = [ordered]@{
  layer = 'Topography'
  program_output = 'Elevation Difference from Sea Level, Elevation Difference from Regional Average'
  updated_at = ((Get-Date).ToUniversalTime().ToString('s') + 'Z')
  final_ready = $finalReady
  manual_review_required = $true
  summary = [ordered]@{
    completion_percent = $completion
    remaining_percent = 100 - $completion
    filled_parcel_count = $validRows.Count
    verified_parcel_count = $validRows.Count
    accuracy_score_4 = $accuracy
    program_integration_percent = $completion
    website_update_percent = $completion
  }
  blockers = @($blockers)
  next_action = if ($sourceGate) { 'Run browser smoke and parcel popup evidence gate through the single shared runner.' } else { 'Add official source-backed Topography verified rows; do not mark final_ready true.' }
  changes = $changes
}
Write-Utf8 $latestRel (Json $payload)

$statusText = @"
Topography shared-runner task status
final_ready=false
source_row_gate_passed=$sourceGate
ui_token_gate_passed=$uiGate
geojson_patch_ok=$geoPatchOk
verified_parcel_count=$($validRows.Count)
accuracy_score_4=$accuracy
blockers=$([string]::Join(';', @($blockers)))
"@
Write-Utf8 $statusRel $statusText

$reportText = @"
# Topography Shared Runner Progress

updated_at=$($payload.updated_at)
final_ready=false
source_row_gate_passed=$sourceGate
ui_token_gate_passed=$uiGate
geojson_patch_ok=$geoPatchOk
verified_parcel_count=$($validRows.Count)
accuracy_score_4=$accuracy
blockers=$([string]::Join(';', @($blockers)))

No fake final_ready was written. Official verified rows are required before completion.
"@
Write-Utf8 $reportRel $reportText

$gate = [ordered]@{
  task_id = $TaskId
  page_key = 'topography'
  source_row_gate_passed = $sourceGate
  ui_token_gate_passed = $uiGate
  browser_smoke_passed = $false
  post_sync_ok = $false
  manual_review_required = $true
  fake_data = $false
  blockers = @($blockers)
}
Write-Utf8 $gateRel (Json $gate)
Write-Utf8 $heartbeatRel (Json ([ordered]@{ task_id=$TaskId; page_key='topography'; updated_at=((Get-Date).ToUniversalTime().ToString('s') + 'Z'); final_ready=$false; fake_data=$false; blockers=@($blockers) }))
Write-Output "topography_shared_runner_task_completed final_ready=false source_row_gate_passed=$sourceGate ui_token_gate_passed=$uiGate blockers=$($blockers.Count)"
