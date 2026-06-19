$ErrorActionPreference = "Stop"

$pageKey = "internet_access_parcel_layer_low_credit_20260612"
$taskId = "internet-access-108-real-parcel-final-gate"

$pageDir = "docs/chatgpt_status/$pageKey"
$statusDir = "$pageDir/status"
$heartbeatDir = "$pageDir/heartbeat"
$runnerOutDir = "$pageDir/runner_outputs"
$reportsDir = "docs/chatgpt_status/reports"
$pageReportsDir = "$pageDir/reports"

$sourceRoot = "F:\chatgpt\AAYS_WORK\internet_access_score10_real_build_20260610"
if (!(Test-Path $sourceRoot)) {
  $sourceRoot = "D:\chatgpt\AAYS_WORK\internet_access_score10_real_build_20260610"
}

$heavyRoot = "F:\AAYS_WORK\internet_access_final_20260616"
if (!(Test-Path "F:\")) {
  $heavyRoot = "D:\AAYS_WORK\internet_access_final_20260616"
}

$processedDir = Join-Path $heavyRoot "processed"
$diagDir = Join-Path $heavyRoot "diagnostics"

New-Item -ItemType Directory -Force $processedDir,$diagDir,$statusDir,$heartbeatDir,$runnerOutDir,$reportsDir,$pageReportsDir | Out-Null

$srcGeoJson = Join-Path $sourceRoot "processed\parcel_internet_access_scores.geojson"
$srcCsv = Join-Path $sourceRoot "processed\parcel_internet_access_scores.csv"
$srcBreakdown = Join-Path $sourceRoot "processed\parcel_internet_access_factor_breakdown.csv"

$readyGeoJson = Join-Path $processedDir "parcel_internet_access_scores_ready.geojson"
$readyCsv = Join-Path $processedDir "parcel_internet_access_scores_ready.csv"
$readyBreakdown = Join-Path $processedDir "parcel_internet_access_factor_breakdown_ready.csv"
$detailJson = Join-Path $processedDir "parcel_internet_access_detail_ready.json"

$repoFixReport = "$pageReportsDir/ia108_real_geometry_join_report.json"
$repoFixStatus = "$statusDir/ia108_real_geometry_join_status.txt"

"GEOMETRY_JOIN_STARTED=$(Get-Date -Format o)" | Set-Content -Encoding UTF8 "$heartbeatDir/latest.txt"

function Read-CsvHeaders($path) {
  if (!(Test-Path $path)) { return @() }
  $first = Get-Content $path -TotalCount 1
  if (!$first) { return @() }
  return $first.Split(",") | ForEach-Object { $_.Trim('"').Trim() }
}

function Get-FeatureKey($props, $preferredKeys) {
  foreach ($k in $preferredKeys) {
    if ($props.PSObject.Properties.Name -contains $k) {
      $v = [string]$props.$k
      if ($v -and $v.Trim().Length -gt 0) { return @{ key=$k; value=$v.Trim() } }
    }
  }
  return $null
}

$scoreHeaders = Read-CsvHeaders $srcCsv
$preferred = @(
  "parcel_id","parcelid","parcel","id","uprn","UPRN","title_number","title_no","title","property_id","propertyid",
  "oa11cd","lsoa11cd","msoa11cd","postcode","pcd","pcds"
)
$preferred += $scoreHeaders

if (!(Test-Path $srcGeoJson)) {
  throw "Source score GeoJSON missing: $srcGeoJson"
}
if (!(Test-Path $srcCsv)) {
  throw "Source score CSV missing: $srcCsv"
}

$scoreObj = Get-Content $srcGeoJson -Raw | ConvertFrom-Json
$scoreFeatures = @($scoreObj.features)

$scoreKeyName = $null
$scoreIndex = @{}

foreach ($f in $scoreFeatures) {
  if ($null -eq $f.properties) { continue }
  $kv = Get-FeatureKey $f.properties $preferred
  if ($kv) {
    if (-not $scoreKeyName) { $scoreKeyName = $kv.key }
    if (-not $scoreIndex.ContainsKey($kv.value)) {
      $scoreIndex[$kv.value] = $f
    }
  }
}

$searchRoots = @(
  "F:\AAYS_WORK",
  "F:\chatgpt\AAYS_WORK",
  "D:\AAYS_WORK",
  "D:\chatgpt\AAYS_WORK",
  "C:\Users\cagda\Documents\GitHub\AAYS"
) | Where-Object { Test-Path $_ }

$candidateFiles = foreach ($root in $searchRoots) {
  Get-ChildItem -Path $root -Recurse -File -ErrorAction SilentlyContinue |
    Where-Object {
      $_.Extension -in @(".geojson",".json") -and
      $_.FullName -match "(parcel|polygon|boundary|boundaries|cadastre|cadastral|title|uprn|footprint)" -and
      $_.Length -gt 1024 -and
      $_.FullName -notmatch "parcel_internet_access_scores.geojson"
    } |
    Sort-Object Length -Descending
}

$best = $null
$bestMatches = 0
$bestKey = $null
$bestPolygonCount = 0
$candidateSummaries = @()

foreach ($file in @($candidateFiles | Select-Object -First 80)) {
  try {
    $obj = Get-Content $file.FullName -Raw -ErrorAction Stop | ConvertFrom-Json
    $features = @($obj.features)
    if ($features.Count -eq 0) { continue }

    $polygonFeatures = @($features | Where-Object {
      $_.geometry -and ($_.geometry.type -eq "Polygon" -or $_.geometry.type -eq "MultiPolygon")
    })

    if ($polygonFeatures.Count -eq 0) { continue }

    $localBestMatches = 0
    $localBestKey = $null

    foreach ($key in $preferred | Select-Object -Unique) {
      $m = 0
      foreach ($pf in ($polygonFeatures | Select-Object -First 5000)) {
        if ($pf.properties -and ($pf.properties.PSObject.Properties.Name -contains $key)) {
          $v = [string]$pf.properties.$key
          if ($v -and $scoreIndex.ContainsKey($v.Trim())) {
            $m++
          }
        }
      }
      if ($m -gt $localBestMatches) {
        $localBestMatches = $m
        $localBestKey = $key
      }
    }

    $candidateSummaries += [ordered]@{
      file = $file.FullName
      size = $file.Length
      feature_count = $features.Count
      polygon_count = $polygonFeatures.Count
      best_join_key = $localBestKey
      sample_matches = $localBestMatches
    }

    if ($localBestMatches -gt $bestMatches) {
      $best = $file.FullName
      $bestMatches = $localBestMatches
      $bestKey = $localBestKey
      $bestPolygonCount = $polygonFeatures.Count
    }
  }
  catch {
    $candidateSummaries += [ordered]@{
      file = $file.FullName
      size = $file.Length
      error = $_.Exception.Message
    }
  }
}

if (-not $best -or $bestMatches -le 0) {
  $report = [ordered]@{
    task_id = $taskId
    page_key = $pageKey
    status = "REAL_PARCEL_GEOMETRY_JOIN_BLOCKED"
    completion_percent = 68
    final_ready = $false
    production_complete = $false
    reason = "No real Polygon/MultiPolygon parcel GeoJSON with a matching join key was found. Fake geometry refused."
    score_feature_count = $scoreFeatures.Count
    score_join_key_detected = $scoreKeyName
    searched_roots = $searchRoots
    candidates = $candidateSummaries
    required_next_action = "Provide a real parcel polygon source with a join key matching the score dataset."
    generated_at = (Get-Date -Format o)
  }
  $report | ConvertTo-Json -Depth 10 | Set-Content -Encoding UTF8 $repoFixReport

  @"
status=REAL_PARCEL_GEOMETRY_JOIN_BLOCKED
completion_percent=68
final_ready=false
production_complete=false
reason=no_matching_real_polygon_source
score_join_key_detected=$scoreKeyName
candidate_count=$($candidateSummaries.Count)
"@ | Set-Content -Encoding UTF8 $repoFixStatus

  throw "No matching real parcel polygon source found. See $repoFixReport"
}

$polyObj = Get-Content $best -Raw | ConvertFrom-Json
$polyFeatures = @($polyObj.features | Where-Object {
  $_.geometry -and ($_.geometry.type -eq "Polygon" -or $_.geometry.type -eq "MultiPolygon")
})

$polyIndex = @{}
foreach ($pf in $polyFeatures) {
  if ($pf.properties -and ($pf.properties.PSObject.Properties.Name -contains $bestKey)) {
    $v = [string]$pf.properties.$bestKey
    if ($v -and -not $polyIndex.ContainsKey($v.Trim())) {
      $polyIndex[$v.Trim()] = $pf.geometry
    }
  }
}

$joined = 0
$nullAfter = 0

foreach ($sf in $scoreFeatures) {
  $kv = Get-FeatureKey $sf.properties @($scoreKeyName,$bestKey) 
  if ($kv -and $polyIndex.ContainsKey($kv.value)) {
    $sf.geometry = $polyIndex[$kv.value]
    $joined++
  }
  if ($null -eq $sf.geometry) { $nullAfter++ }
}

$scoreObj | ConvertTo-Json -Depth 100 | Set-Content -Encoding UTF8 $readyGeoJson
Copy-Item $srcCsv $readyCsv -Force
if (Test-Path $srcBreakdown) { Copy-Item $srcBreakdown $readyBreakdown -Force }
@{
  task_id = $taskId
  page_key = $pageKey
  source_score_geojson = $srcGeoJson
  source_polygon_geojson = $best
  score_join_key = $scoreKeyName
  polygon_join_key = $bestKey
  joined_geometry_count = $joined
  null_geometry_after_join = $nullAfter
  generated_at = (Get-Date -Format o)
} | ConvertTo-Json -Depth 10 | Set-Content -Encoding UTF8 $detailJson

$report2 = [ordered]@{
  task_id = $taskId
  page_key = $pageKey
  status = if ($nullAfter -eq 0 -and $joined -eq $scoreFeatures.Count) { "REAL_PARCEL_GEOMETRY_JOIN_READY" } else { "REAL_PARCEL_GEOMETRY_JOIN_PARTIAL" }
  completion_percent = if ($nullAfter -eq 0 -and $joined -eq $scoreFeatures.Count) { 99 } else { 72 }
  final_ready = $false
  production_complete = $false
  source_polygon_geojson = $best
  polygon_feature_count = $bestPolygonCount
  score_join_key = $scoreKeyName
  polygon_join_key = $bestKey
  joined_geometry_count = $joined
  score_feature_count = $scoreFeatures.Count
  null_geometry_after_join = $nullAfter
  ready_geojson = $readyGeoJson
  ready_csv = $readyCsv
  ready_breakdown = $readyBreakdown
  detail_json = $detailJson
  candidates = $candidateSummaries
  generated_at = (Get-Date -Format o)
}
$report2 | ConvertTo-Json -Depth 10 | Set-Content -Encoding UTF8 $repoFixReport

@"
status=$($report2.status)
completion_percent=$($report2.completion_percent)
source_polygon_geojson=$best
score_join_key=$scoreKeyName
polygon_join_key=$bestKey
joined_geometry_count=$joined
score_feature_count=$($scoreFeatures.Count)
null_geometry_after_join=$nullAfter
ready_geojson=$readyGeoJson
"@ | Set-Content -Encoding UTF8 $repoFixStatus

"GEOMETRY_JOIN_FINISHED=$(Get-Date -Format o)" | Add-Content -Encoding UTF8 "$heartbeatDir/latest.txt"
