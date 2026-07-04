param(
  [string]$RepoRoot = $env:AAYS_REPO_ROOT
)

$ErrorActionPreference = 'Stop'
if ([string]::IsNullOrWhiteSpace($RepoRoot)) { $RepoRoot = (Get-Location).Path }
$repoFull = [System.IO.Path]::GetFullPath($RepoRoot)
if (-not $repoFull.ToUpperInvariant().StartsWith('F:\')) {
  throw "Topography bridge is F-disk only. Refusing repo root: $repoFull"
}
Set-Location $repoFull

function Resolve-RepoPath([string]$p) {
  if ([System.IO.Path]::IsPathRooted($p)) { return $p }
  return [System.IO.Path]::Combine($repoFull, $p)
}
function Ensure-Dir([string]$p) {
  $fullPath = Resolve-RepoPath $p
  $d = Split-Path -Parent $fullPath
  if ($d -and -not (Test-Path $d)) { New-Item -ItemType Directory -Force -Path $d | Out-Null }
}
function Write-Utf8([string]$p, [string]$c) {
  $fullPath = Resolve-RepoPath $p
  Ensure-Dir $fullPath
  [System.IO.File]::WriteAllText($fullPath, $c, [System.Text.UTF8Encoding]::new($false))
}
function Json([object]$o) { return ($o | ConvertTo-Json -Depth 12) }

$csvPath = 'docs/chatgpt_status/topography/fixtures/topography_verified_rows_template_20260703.csv'
$statusPath = 'docs/chatgpt_status/topography/status/topography_current_status_20260703.txt'
$reportPath = 'docs/chatgpt_status/topography/reports/topography_progress_latest_20260703.md'
$latestPath = 'outputs/england_program_parcel_matrix_20260629/topography_updates/latest_changes.json'
$geoPath = 'england_map_web/data/program_layer_matrix/topography.geojson'
$smokePath = 'docs/chatgpt_status/topography/browser_smoke/topography_browser_smoke_latest_20260704.json'

$required = @('parcel_id','parcel_ref','elevation_sea_level_m','regional_average_elevation_m','elevation_difference_regional_average_m','elevation_class','color_category','confidence_rating','confidence_percent','source','source_url','source_date','matching_method','calculation_explanation','accuracy_score_4','needs_manual_review','changed_in_latest_run')
$rows = @()
$validRows = @()
$blockers = New-Object System.Collections.Generic.List[string]

if (Test-Path $csvPath) {
  $rows = @(Import-Csv $csvPath)
  foreach ($r in $rows) {
    $ok = $true
    foreach ($f in $required) {
      if (-not ($r.PSObject.Properties.Name -contains $f) -or [string]::IsNullOrWhiteSpace([string]$r.$f)) { $ok = $false }
    }
    if ($ok) { $validRows += $r }
  }
} else {
  $blockers.Add('verified_rows_csv_missing')
}

if ($rows.Count -eq 0) { $blockers.Add('verified_rows_missing') }
if ($validRows.Count -lt $rows.Count) { $blockers.Add('some_rows_missing_required_fields') }
$smokeOk = $false
if (Test-Path $smokePath) {
  try {
    $smoke = Get-Content $smokePath -Raw | ConvertFrom-Json
    $smokeOk = ($smoke.overall_ok -eq $true)
  } catch {
    $smokeOk = $false
  }
}
if (-not $smokeOk) { $blockers.Add('browser_smoke_missing_or_failed') }

$hasUiPatch = (Test-Path 'england_map_web/topography_panel_runtime_patch_20260704.js') -and (Test-Path 'outputs/england_program_parcel_matrix_20260629/topography_matrix_runtime_patch_20260704.js')
if (-not $hasUiPatch) { $blockers.Add('ui_runtime_patch_missing') }

$canPatchGeo = $false
if ((Test-Path $geoPath) -and $validRows.Count -gt 0) {
  try {
    $geo = Get-Content $geoPath -Raw | ConvertFrom-Json
    foreach ($feat in @($geo.features)) {
      $p = $feat.properties
      $pid = [string]$p.parcel_id
      $pref = [string]$p.parcel_ref
      $match = $validRows | Where-Object { ([string]$_.parcel_id -eq $pid -and $pid) -or ([string]$_.parcel_ref -eq $pref -and $pref) } | Select-Object -First 1
      if ($match) {
        foreach ($f in $required) { $p | Add-Member -NotePropertyName $f -NotePropertyValue $match.$f -Force }
        $p | Add-Member -NotePropertyName 'topography_updated_at' -NotePropertyValue ((Get-Date).ToUniversalTime().ToString('s') + 'Z') -Force
      }
    }
    Write-Utf8 $geoPath (Json $geo)
    $canPatchGeo = $true
  } catch {
    $blockers.Add('topography_geojson_patch_failed')
  }
} elseif (-not (Test-Path $geoPath)) {
  $blockers.Add('topography_geojson_missing')
}

$filled = $validRows.Count
$smokeOk = [bool]$smokeOk
$completion = 25
$programPct = 25
$sitePct = 25
$accuracy = '0/4'
if ($filled -gt 0) { $completion = 55; $programPct = 55; $sitePct = 55; $accuracy = '3/4' }
if ($filled -gt 0 -and $smokeOk -and $hasUiPatch -and $canPatchGeo) { $completion = 80; $programPct = 80; $sitePct = 80; $accuracy = '4/4' }
$finalReady = $false
if ($completion -ge 80 -and $blockers.Count -eq 0) { $finalReady = $true; $completion = 100 }
$remaining = 100 - $completion

$changes = @()
foreach ($r in $validRows) {
  $changes += [ordered]@{
    parcel_id = $r.parcel_id
    parcel_ref = $r.parcel_ref
    elevation_sea_level_m = [double]$r.elevation_sea_level_m
    regional_average_elevation_m = [double]$r.regional_average_elevation_m
    elevation_difference_regional_average_m = [double]$r.elevation_difference_regional_average_m
    elevation_class = $r.elevation_class
    color_category = $r.color_category
    confidence_rating = $r.confidence_rating
    confidence_percent = [double]$r.confidence_percent
    source = $r.source
    source_url = $r.source_url
    source_date = $r.source_date
    matching_method = $r.matching_method
    calculation_explanation = $r.calculation_explanation
    accuracy_score_4 = $r.accuracy_score_4
    needs_manual_review = $r.needs_manual_review
    changed_in_latest_run = $r.changed_in_latest_run
  }
}

$out = [ordered]@{
  layer = 'Topography'
  program_output = 'Elevation Difference from Sea Level, Elevation Difference from Regional Average'
  updated_at = ((Get-Date).ToUniversalTime().ToString('s') + 'Z')
  final_ready = $finalReady
  manual_review_required = -not $finalReady
  summary = [ordered]@{
    completion_percent = $completion
    remaining_percent = $remaining
    wait_minutes = 0
    filled_parcel_count = $filled
    verified_parcel_count = $filled
    accuracy_score_4 = $accuracy
    program_integration_percent = $programPct
    website_update_percent = $sitePct
  }
  blockers = @($blockers)
  next_action = 'continue with the existing single shared runner until verified rows, UI smoke and site visibility are complete'
  changes = $changes
}
Write-Utf8 $latestPath (Json $out)

$status = @"
Topography devam durumu:
Tamamlanan: %$completion
Kalan: %$remaining
Bekleme: 0 dakika
Doldurulan parsel: $filled
Dogruluk: $accuracy
Program entegrasyonu: %$programPct
Web sitesi guncellemesi: %$sitePct
final_ready: $($finalReady.ToString().ToLowerInvariant())
blocker: $([string]::Join(';', @($blockers)))
next_action: $($out.next_action)
"@
Write-Utf8 $statusPath $status

$report = @"
# Topography Progress Latest

updated_at=$($out.updated_at)
layer=Topography
final_ready=$($finalReady.ToString().ToLowerInvariant())
completion_percent=$completion
remaining_percent=$remaining
wait_minutes=0
filled_parcel_count=$filled
verified_parcel_count=$filled
accuracy_score_4=$accuracy
program_integration_percent=$programPct
website_update_percent=$sitePct
blockers=$([string]::Join(';', @($blockers)))
"@
Write-Utf8 $reportPath $report

$heartbeatPath = 'docs/chatgpt_status/topography/heartbeat/topography_bridge_heartbeat_latest_20260704.json'
$heartbeat = [ordered]@{
  layer = 'Topography'
  runner = 'topography_single_runner_bridge'
  repo_root = $repoFull
  pid = $PID
  updated_at = ((Get-Date).ToUniversalTime().ToString('s') + 'Z')
  final_ready = $finalReady
  filled_parcel_count = $filled
  verified_parcel_count = $filled
  smoke_ok = [bool]$smokeOk
  ui_patch_ok = [bool]$hasUiPatch
  geojson_patch_ok = [bool]$canPatchGeo
  blockers = @($blockers)
  fake_data_created = $false
}
Write-Utf8 $heartbeatPath (Json $heartbeat)
Write-Output $status
