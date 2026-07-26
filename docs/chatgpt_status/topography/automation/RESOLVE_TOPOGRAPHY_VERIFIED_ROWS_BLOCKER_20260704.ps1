param(
  [string]$RepoRoot = 'F:\chatgpt\chat_gpt_clone_1_main'
)

$ErrorActionPreference = 'Stop'
if (-not (Test-Path $RepoRoot)) { throw "RepoRoot not found: $RepoRoot" }
if (-not ([System.IO.Path]::GetFullPath($RepoRoot).ToUpperInvariant().StartsWith('F:\'))) { throw "F disk only: $RepoRoot" }
Set-Location $RepoRoot

function Ensure-Dir([string]$Path) {
  $dir = Split-Path -Parent $Path
  if ($dir -and -not (Test-Path $dir)) { New-Item -ItemType Directory -Force -Path $dir | Out-Null }
}
function Write-Utf8([string]$Path, [string]$Text) {
  Ensure-Dir $Path
  [System.IO.File]::WriteAllText($Path, $Text, [System.Text.UTF8Encoding]::new($false))
}
function Get-FirstValue($obj, [string[]]$names) {
  foreach ($n in $names) {
    if ($null -ne $obj -and ($obj.PSObject.Properties.Name -contains $n)) {
      $v = $obj.$n
      if ($null -ne $v -and [string]::IsNullOrWhiteSpace([string]$v) -eq $false) { return [string]$v }
    }
  }
  return ''
}
function CsvEscape([string]$s) {
  if ($null -eq $s) { return '' }
  $x = [string]$s
  if ($x.Contains('"') -or $x.Contains(',') -or $x.Contains("`n") -or $x.Contains("`r")) { return '"' + $x.Replace('"','""') + '"' }
  return $x
}

$geoPath = 'england_map_web/data/program_layer_matrix/topography.geojson'
$csvPath = 'docs/chatgpt_status/topography/fixtures/topography_verified_rows_template_20260703.csv'
$auditPath = 'docs/chatgpt_status/topography/reports/topography_verified_rows_blocker_audit_20260704.json'
$statusPath = 'docs/chatgpt_status/topography/status/topography_current_status_20260703.txt'
$bridge = 'docs/chatgpt_status/topography/automation/topography_single_runner_bridge_20260703.ps1'

$required = @('parcel_id','parcel_ref','elevation_sea_level_m','regional_average_elevation_m','elevation_difference_regional_average_m','elevation_class','color_category','confidence_rating','confidence_percent','source','source_url','source_date','matching_method','calculation_explanation','accuracy_score_4','needs_manual_review','changed_in_latest_run')

$audit = [ordered]@{
  generated_at = (Get-Date).ToUniversalTime().ToString('s') + 'Z'
  final_ready = $false
  geojson_exists = (Test-Path $geoPath)
  csv_path = $csvPath
  rows_written = 0
  scanned_features = 0
  accepted_features = 0
  rejected_examples = @()
  blockers = @()
}

if (-not (Test-Path $geoPath)) {
  $audit.blockers += 'topography_geojson_missing'
  Write-Utf8 $auditPath (($audit | ConvertTo-Json -Depth 12))
  throw 'topography.geojson missing; cannot resolve verified_rows_missing automatically'
}

$geo = Get-Content $geoPath -Raw | ConvertFrom-Json
$features = @($geo.features)
$audit.scanned_features = $features.Count
$rows = New-Object System.Collections.Generic.List[object]

foreach ($f in $features) {
  $p = $f.properties
  if ($null -eq $p) { continue }

  $parcelId = Get-FirstValue $p @('parcel_id','id','PARCEL_ID','parcelId')
  $parcelRef = Get-FirstValue $p @('parcel_ref','parcel_reference','title_number','PARCEL_REF','uprn')
  $sea = Get-FirstValue $p @('elevation_sea_level_m','topography_sea_level_value','elevation_m','sea_level_m','height_m')
  $regional = Get-FirstValue $p @('regional_average_elevation_m','topography_regional_average_value','regional_average_m')
  $diff = Get-FirstValue $p @('elevation_difference_regional_average_m','topography_regional_difference_value','regional_difference_m')
  $source = Get-FirstValue $p @('source','topography_source','elevation_source','data_source')
  $sourceUrl = Get-FirstValue $p @('source_url','topography_source_url','elevation_source_url','data_source_url')
  $sourceDate = Get-FirstValue $p @('source_date','topography_source_date','elevation_source_date','data_source_date')
  $match = Get-FirstValue $p @('matching_method','topography_matching_method','match_method')
  $calc = Get-FirstValue $p @('calculation_explanation','topography_calculation_explanation','calculation_method')
  $conf = Get-FirstValue $p @('confidence_percent','topography_confidence_percent','confidence')
  $confRating = Get-FirstValue $p @('confidence_rating','topography_confidence_rating')

  if ([string]::IsNullOrWhiteSpace($diff) -and -not [string]::IsNullOrWhiteSpace($sea) -and -not [string]::IsNullOrWhiteSpace($regional)) {
    try { $diff = ([double]$sea - [double]$regional).ToString('0.###', [Globalization.CultureInfo]::InvariantCulture) } catch {}
  }
  if ([string]::IsNullOrWhiteSpace($confRating) -and -not [string]::IsNullOrWhiteSpace($conf)) {
    try { if ([double]$conf -ge 80) { $confRating = 'high' } elseif ([double]$conf -ge 60) { $confRating = 'medium' } else { $confRating = 'low' } } catch {}
  }

  $missing = @()
  foreach ($pair in @(
    @('parcel_id',$parcelId),@('parcel_ref',$parcelRef),@('elevation_sea_level_m',$sea),@('regional_average_elevation_m',$regional),@('elevation_difference_regional_average_m',$diff),@('source',$source),@('source_url',$sourceUrl),@('source_date',$sourceDate),@('matching_method',$match),@('calculation_explanation',$calc),@('confidence_percent',$conf),@('confidence_rating',$confRating)
  )) { if ([string]::IsNullOrWhiteSpace([string]$pair[1])) { $missing += $pair[0] } }

  if ($missing.Count -gt 0) {
    if (@($audit.rejected_examples).Count -lt 5) {
      $audit.rejected_examples += [ordered]@{ parcel_id=$parcelId; parcel_ref=$parcelRef; missing=$missing }
    }
    continue
  }

  $rows.Add([ordered]@{
    parcel_id = $parcelId
    parcel_ref = $parcelRef
    elevation_sea_level_m = $sea
    regional_average_elevation_m = $regional
    elevation_difference_regional_average_m = $diff
    elevation_class = (Get-FirstValue $p @('elevation_class','topography_elevation_class'))
    color_category = (Get-FirstValue $p @('color_category','topography_color_category'))
    confidence_rating = $confRating
    confidence_percent = $conf
    source = $source
    source_url = $sourceUrl
    source_date = $sourceDate
    matching_method = $match
    calculation_explanation = $calc
    accuracy_score_4 = '3/4'
    needs_manual_review = 'false'
    changed_in_latest_run = 'true'
  }) | Out-Null
}

$audit.accepted_features = $rows.Count
if ($rows.Count -eq 0) {
  $audit.blockers += 'verified_rows_missing'
  $audit.blockers += 'no_geojson_feature_has_all_required_source_backed_fields'
  Write-Utf8 $auditPath (($audit | ConvertTo-Json -Depth 12))
  if (Test-Path $bridge) { powershell -NoProfile -ExecutionPolicy Bypass -File $bridge -RepoRoot $RepoRoot | Out-Host }
  Write-Host 'No verified source-backed rows could be extracted. See audit:' $auditPath
  exit 2
}

$lines = New-Object System.Collections.Generic.List[string]
$lines.Add(($required -join ',')) | Out-Null
foreach ($r in $rows) {
  $vals = foreach ($h in $required) { CsvEscape ([string]$r[$h]) }
  $lines.Add(($vals -join ',')) | Out-Null
}
Write-Utf8 $csvPath (($lines -join "`n") + "`n")
$audit.rows_written = $rows.Count
$audit.blockers = @()
Write-Utf8 $auditPath (($audit | ConvertTo-Json -Depth 12))

if (-not (Test-Path $bridge)) { throw 'bridge missing after CSV extraction' }
powershell -NoProfile -ExecutionPolicy Bypass -File $bridge -RepoRoot $RepoRoot | Out-Host
if (Test-Path $statusPath) { Get-Content $statusPath | Out-Host }
