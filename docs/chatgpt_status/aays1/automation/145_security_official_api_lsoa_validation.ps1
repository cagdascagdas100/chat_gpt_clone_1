$ErrorActionPreference = 'Continue'

$repoRoot = $env:AAYS_REPO_ROOT
if ([string]::IsNullOrWhiteSpace($repoRoot)) { $repoRoot = (Get-Location).Path }
$now = Get-Date
$generatedAt = $now.ToString('o')

$geoRel = 'england_map_web/data/security_public_safety/parcel_security_scores_verified.geojson'
$csvRel = 'england_map_web/data/security_public_safety/parcel_security_scores_verified.csv'
$visibleRowsRel = 'england_map_web/data/program_layer_matrix/security_public_safety_visible_rows.json'
$visibleStatusRel = 'england_map_web/data/program_layer_matrix/security_public_safety_visible_status.json'
$manifestRel = 'england_map_web/data/security_public_safety/security_evidence_manifest.json'
$latestRel = 'outputs/england_program_parcel_matrix_20260629/security_public_safety_updates/latest_changes.json'
$outRel = 'docs/chatgpt_status/aays1/runner_outputs/145_security_official_api_lsoa_validation.json'
$reportRel = 'docs/chatgpt_status/aays1/reports/145_security_official_api_lsoa_validation_latest.md'

$geoPath = Join-Path $repoRoot $geoRel
$csvPath = Join-Path $repoRoot $csvRel
$visibleRowsPath = Join-Path $repoRoot $visibleRowsRel
$visibleStatusPath = Join-Path $repoRoot $visibleStatusRel
$manifestPath = Join-Path $repoRoot $manifestRel
$latestPath = Join-Path $repoRoot $latestRel
$outPath = Join-Path $repoRoot $outRel
$reportPath = Join-Path $repoRoot $reportRel
New-Item -ItemType Directory -Force -Path (Split-Path $outPath),(Split-Path $reportPath) | Out-Null

function Get-Sha256Text([string]$text) {
  $sha = [System.Security.Cryptography.SHA256]::Create()
  try {
    $bytes = [Text.Encoding]::UTF8.GetBytes($text)
    return ([BitConverter]::ToString($sha.ComputeHash($bytes))).Replace('-', '').ToLowerInvariant()
  } finally { $sha.Dispose() }
}

function Set-Prop($obj, [string]$name, $value) {
  $obj | Add-Member -NotePropertyName $name -NotePropertyValue $value -Force
}

function Get-LsoaCode($props) {
  $text = [string]$props.official_source_evidence
  $m = [regex]::Match($text, 'E010[0-9]{5}')
  if ($m.Success) { return $m.Value }
  return $null
}

$result = [ordered]@{
  task_id = 'aays1-145-security-official-api-lsoa-validation-20260711'
  page_key = 'aays1'
  status = 'started'
  checked_at = $generatedAt
  source = 'data.police.uk official API'
  last_updated_url = 'https://data.police.uk/api/crime-last-updated'
  street_crime_method = 'official street-level crimes within one mile of one representative parcel point per strict LSOA; supporting freshness evidence only'
  official_latest_date = $null
  official_latest_month = $null
  official_latest_response_sha256 = $null
  verified_feature_count_before = 0
  unique_lsoa_count = 0
  lsoa_http_200_count = 0
  lsoa_failed_count = 0
  rows_enriched = 0
  total_official_api_crime_records = 0
  validations = @()
  blockers = @()
  single_runner_only = $true
  parallel_runner = $false
  final_ready = $false
  product_final_ready = $false
  fake_data = $false
  db_write = $false
  migration = $false
  production_deploy = $false
  person_level_data = $false
}

try {
  foreach ($required in @($geoPath,$csvPath,$visibleRowsPath,$visibleStatusPath,$manifestPath,$latestPath)) {
    if (-not (Test-Path $required)) { throw "missing_required_file:$required" }
  }

  $geo = Get-Content -Raw -Encoding UTF8 $geoPath | ConvertFrom-Json
  $features = @($geo.features)
  $result.verified_feature_count_before = $features.Count
  if ($features.Count -lt 300) { throw "verified_features_below_300:$($features.Count)" }

  $latestResponse = Invoke-WebRequest -UseBasicParsing -Uri $result.last_updated_url -TimeoutSec 45 -Headers @{ 'User-Agent'='TerraYield-AAYS-security-validation/1.0' }
  if ([int]$latestResponse.StatusCode -ne 200) { throw "crime_last_updated_http_$($latestResponse.StatusCode)" }
  $result.official_latest_response_sha256 = Get-Sha256Text ([string]$latestResponse.Content)
  $latestObject = $latestResponse.Content | ConvertFrom-Json
  $result.official_latest_date = [string]$latestObject.date
  $latestDate = [datetime]::ParseExact($result.official_latest_date, 'yyyy-MM-dd', [Globalization.CultureInfo]::InvariantCulture)
  $result.official_latest_month = $latestDate.ToString('yyyy-MM')

  $representatives = [ordered]@{}
  foreach ($feature in $features) {
    if ($null -eq $feature.properties -or $null -eq $feature.geometry) { throw 'feature_missing_properties_or_geometry' }
    $lsoa = Get-LsoaCode $feature.properties
    if ([string]::IsNullOrWhiteSpace($lsoa)) { throw "feature_missing_valid_lsoa:$($feature.properties.parcel_id)" }
    if ([string]$feature.geometry.type -ne 'Point') { throw "internet_validation_requires_point_geometry:$($feature.properties.parcel_id)" }
    $coordinates = @($feature.geometry.coordinates)
    if ($coordinates.Count -lt 2) { throw "feature_missing_coordinates:$($feature.properties.parcel_id)" }
    if (-not $representatives.Contains($lsoa)) {
      $representatives[$lsoa] = [pscustomobject]@{
        parcel_id = [string]$feature.properties.parcel_id
        longitude = [double]$coordinates[0]
        latitude = [double]$coordinates[1]
      }
    }
  }

  $result.unique_lsoa_count = $representatives.Count
  if ($representatives.Count -lt 1 -or $representatives.Count -gt 75) { throw "unexpected_unique_lsoa_count:$($representatives.Count)" }

  $validationByLsoa = @{}
  foreach ($lsoa in $representatives.Keys) {
    $rep = $representatives[$lsoa]
    $lat = $rep.latitude.ToString('0.000000', [Globalization.CultureInfo]::InvariantCulture)
    $lng = $rep.longitude.ToString('0.000000', [Globalization.CultureInfo]::InvariantCulture)
    $url = "https://data.police.uk/api/crimes-street/all-crime?date=$($result.official_latest_month)&lat=$lat&lng=$lng"
    $entry = [ordered]@{
      lsoa_code = $lsoa
      representative_parcel_id = $rep.parcel_id
      representative_latitude = $lat
      representative_longitude = $lng
      request_url = $url
      http_status = $null
      crime_count = 0
      response_sha256 = $null
      category_counts = @{}
      status = 'failed'
      error = $null
    }
    try {
      $response = Invoke-WebRequest -UseBasicParsing -Uri $url -TimeoutSec 60 -Headers @{ 'User-Agent'='TerraYield-AAYS-security-validation/1.0' }
      $entry.http_status = [int]$response.StatusCode
      if ($entry.http_status -ne 200) { throw "http_$($entry.http_status)" }
      $entry.response_sha256 = Get-Sha256Text ([string]$response.Content)
      $parsed = $response.Content | ConvertFrom-Json
      $crimes = @($parsed)
      $entry.crime_count = $crimes.Count
      $categoryCounts = [ordered]@{}
      foreach ($group in @($crimes | Group-Object -Property category | Sort-Object Name)) {
        $categoryCounts[[string]$group.Name] = [int]$group.Count
      }
      $entry.category_counts = $categoryCounts
      $entry.status = 'http_200_verified'
      $result.lsoa_http_200_count++
      $result.total_official_api_crime_records += $crimes.Count
    } catch {
      $entry.error = $_.Exception.Message
      $result.lsoa_failed_count++
      $result.blockers += "lsoa_api_validation_failed:${lsoa}:$($_.Exception.Message)"
    }
    $validationByLsoa[$lsoa] = [pscustomobject]$entry
    $result.validations += [pscustomobject]$entry
    Start-Sleep -Milliseconds 200
  }

  if ($result.lsoa_failed_count -gt 0 -or $result.lsoa_http_200_count -ne $result.unique_lsoa_count) {
    throw "official_api_validation_incomplete:$($result.lsoa_http_200_count)/$($result.unique_lsoa_count)"
  }

  foreach ($feature in $features) {
    $props = $feature.properties
    $lsoa = Get-LsoaCode $props
    $validation = $validationByLsoa[$lsoa]
    Set-Prop $props 'official_api_latest_month' $result.official_latest_month
    Set-Prop $props 'official_api_validation_status' 'HTTP_200'
    Set-Prop $props 'official_api_sample_crime_count' ([int]$validation.crime_count)
    Set-Prop $props 'official_api_sample_sha256' ([string]$validation.response_sha256)
    Set-Prop $props 'official_api_validation_method' 'one_mile_radius_representative_point_supporting_evidence_not_exact_lsoa_count'
    Set-Prop $props 'official_api_validation_url' ([string]$validation.request_url)
    Set-Prop $props 'last_verified_at' $generatedAt
    $existingEvidence = [string]$props.official_source_evidence
    $apiEvidence = "official_api_month=$($result.official_latest_month); official_api_http=200; official_api_1mi_count=$($validation.crime_count); official_api_sha256=$($validation.response_sha256)"
    Set-Prop $props 'official_source_evidence' "$existingEvidence; $apiEvidence"
    $result.rows_enriched++
  }

  Set-Prop $geo 'official_api_latest_month' $result.official_latest_month
  Set-Prop $geo 'official_api_lsoa_validated_count' $result.unique_lsoa_count
  Set-Prop $geo 'official_api_validation_generated_at' $generatedAt
  $geo | ConvertTo-Json -Depth 45 | Set-Content -Encoding UTF8 $geoPath
  @($features | ForEach-Object { $_.properties }) | Export-Csv -NoTypeInformation -Encoding UTF8 $csvPath

  $visible = Get-Content -Raw -Encoding UTF8 $visibleRowsPath | ConvertFrom-Json
  Set-Prop $visible 'official_api_latest_month' $result.official_latest_month
  Set-Prop $visible 'official_api_lsoa_validated_count' $result.unique_lsoa_count
  Set-Prop $visible 'official_api_validation_generated_at' $generatedAt
  Set-Prop $visible 'rows' @($features | ForEach-Object { $_.properties })
  $visible | ConvertTo-Json -Depth 35 | Set-Content -Encoding UTF8 $visibleRowsPath

  $status = Get-Content -Raw -Encoding UTF8 $visibleStatusPath | ConvertFrom-Json
  Set-Prop $status 'official_api_latest_month' $result.official_latest_month
  Set-Prop $status 'official_api_lsoa_validated_count' $result.unique_lsoa_count
  Set-Prop $status 'official_api_http_200_count' $result.lsoa_http_200_count
  Set-Prop $status 'official_api_total_sample_crime_records' $result.total_official_api_crime_records
  Set-Prop $status 'official_api_validation_generated_at' $generatedAt
  Set-Prop $status 'official_api_validation_output_path' $outRel
  $status | ConvertTo-Json -Depth 20 | Set-Content -Encoding UTF8 $visibleStatusPath

  $manifest = Get-Content -Raw -Encoding UTF8 $manifestPath | ConvertFrom-Json
  Set-Prop $manifest 'official_api_latest_month' $result.official_latest_month
  Set-Prop $manifest 'official_api_lsoa_validated_count' $result.unique_lsoa_count
  Set-Prop $manifest 'official_api_http_200_count' $result.lsoa_http_200_count
  Set-Prop $manifest 'official_api_total_sample_crime_records' $result.total_official_api_crime_records
  Set-Prop $manifest 'official_api_validation_method' $result.street_crime_method
  Set-Prop $manifest 'official_api_validation_output_path' $outRel
  $manifest | ConvertTo-Json -Depth 30 | Set-Content -Encoding UTF8 $manifestPath

  $latest = Get-Content -Raw -Encoding UTF8 $latestPath | ConvertFrom-Json
  Set-Prop $latest 'official_api_latest_month' $result.official_latest_month
  Set-Prop $latest 'official_api_lsoa_validated_count' $result.unique_lsoa_count
  Set-Prop $latest 'official_api_http_200_count' $result.lsoa_http_200_count
  Set-Prop $latest 'official_api_total_sample_crime_records' $result.total_official_api_crime_records
  Set-Prop $latest 'official_api_validation_output_path' $outRel
  $latest | ConvertTo-Json -Depth 35 | Set-Content -Encoding UTF8 $latestPath

  $csvCount = @(Import-Csv -LiteralPath $csvPath).Count
  $geoCount = @((Get-Content -Raw -Encoding UTF8 $geoPath | ConvertFrom-Json).features).Count
  $visibleCount = @((Get-Content -Raw -Encoding UTF8 $visibleRowsPath | ConvertFrom-Json).rows).Count
  if ($csvCount -ne $geoCount -or $csvCount -ne $visibleCount -or $csvCount -ne 300) {
    throw "post_validation_count_mismatch:csv=$csvCount,geo=$geoCount,visible=$visibleCount"
  }

  $result.status = 'completed_all_lsoa_official_api_validated'
} catch {
  if ($result.blockers -notcontains $_.Exception.Message) { $result.blockers += $_.Exception.Message }
  $result.status = 'blocked_official_api_validation_incomplete'
}

@"
# AAYS1 Security official API LSOA validation

- Generated at: $generatedAt
- Official latest date: $($result.official_latest_date)
- Official latest month: $($result.official_latest_month)
- Verified features before validation: $($result.verified_feature_count_before)
- Unique LSOAs: $($result.unique_lsoa_count)
- LSOA HTTP 200: $($result.lsoa_http_200_count)
- LSOA failures: $($result.lsoa_failed_count)
- Rows enriched: $($result.rows_enriched)
- Total official API crime records across representative one-mile queries: $($result.total_official_api_crime_records)
- Validation method: $($result.street_crime_method)
- final_ready: false
- fake_data: false
- db_write: false
- migration: false
- production_deploy: false
"@ | Set-Content -Encoding UTF8 $reportPath

$result | ConvertTo-Json -Depth 35 | Set-Content -Encoding UTF8 $outPath
Write-Host "OUTPUT=$outPath"
if ($result.blockers.Count -gt 0 -or $result.status -ne 'completed_all_lsoa_official_api_validated') { exit 2 }
exit 0
