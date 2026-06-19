$ErrorActionPreference = "Stop"

$pageKey = "internet_access_parcel_layer_low_credit_20260612"
$taskId = "internet-access-108-real-parcel-final-gate"
$fixId = "ia108-real-geometry-join-v2-schema-probe"

$pageDir = "docs/chatgpt_status/$pageKey"
$statusDir = "$pageDir/status"
$heartbeatDir = "$pageDir/heartbeat"
$runnerOutDir = "$pageDir/runner_outputs"
$reportsDir = "docs/chatgpt_status/reports"
$pageReportsDir = "$pageDir/reports"

$sourceRoot = "F:\chatgpt\AAYS_WORK\internet_access_score10_real_build_20260610"
if (!(Test-Path $sourceRoot)) { $sourceRoot = "D:\chatgpt\AAYS_WORK\internet_access_score10_real_build_20260610" }

$heavyRoot = "F:\AAYS_WORK\internet_access_final_20260616"
if (!(Test-Path "F:\")) { $heavyRoot = "D:\AAYS_WORK\internet_access_final_20260616" }

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

$repoReport = "$pageReportsDir/ia108_real_geometry_join_v2_schema_probe_report.json"
$repoStatus = "$statusDir/ia108_real_geometry_join_v2_schema_probe.txt"
$repoLog = "$statusDir/ia108_real_geometry_join_v2_schema_probe.log"

"V2_SCHEMA_PROBE_STARTED=$(Get-Date -Format o)" | Set-Content -Encoding UTF8 "$heartbeatDir/latest.txt"

function Write-Log($s) {
  $s | Tee-Object -FilePath $repoLog -Append
}

function Get-PropValue($obj, [string[]]$keys) {
  if ($null -eq $obj) { return $null }
  foreach ($k in $keys) {
    if ($obj.PSObject.Properties.Name -contains $k) {
      $v = [string]$obj.$k
      if ($v -and $v.Trim().Length -gt 0) { return @{ key=$k; value=$v.Trim() } }
    }
  }
  return $null
}

function Get-Geometry($obj) {
  if ($null -eq $obj) { return $null }
  if ($obj.PSObject.Properties.Name -contains "geometry" -and $obj.geometry -and ($obj.geometry.type -eq "Polygon" -or $obj.geometry.type -eq "MultiPolygon")) { return $obj.geometry }
  if ($obj.PSObject.Properties.Name -contains "geom" -and $obj.geom -and ($obj.geom.type -eq "Polygon" -or $obj.geom.type -eq "MultiPolygon")) { return $obj.geom }
  if ($obj.PSObject.Properties.Name -contains "the_geom" -and $obj.the_geom -and ($obj.the_geom.type -eq "Polygon" -or $obj.the_geom.type -eq "MultiPolygon")) { return $obj.the_geom }
  return $null
}

function Try-RegisterGeometry($idx, $key, $geom) {
  if ($key -and $geom -and -not $idx.ContainsKey($key)) { $idx[$key] = $geom }
}

if (!(Test-Path $srcGeoJson)) { throw "Source score GeoJSON missing: $srcGeoJson" }
if (!(Test-Path $srcCsv)) { throw "Source score CSV missing: $srcCsv" }

Write-Log "Reading score GeoJSON..."
$scoreObj = Get-Content $srcGeoJson -Raw | ConvertFrom-Json
$scoreFeatures = @($scoreObj.features)
$preferredKeys = @("parcel_id","parcelid","parcel","id","uprn","UPRN","title_number","title_no","title","property_id","propertyid","oa11cd","lsoa11cd","msoa11cd","postcode","pcd","pcds")

$scoreIndex = @{}
$scoreKeyName = $null
foreach ($f in $scoreFeatures) {
  $kv = Get-PropValue $f.properties $preferredKeys
  if ($kv) {
    if (-not $scoreKeyName) { $scoreKeyName = $kv.key }
    if (-not $scoreIndex.ContainsKey($kv.value)) { $scoreIndex[$kv.value] = $f }
  }
}

$searchRoots = @("F:\AAYS_WORK","F:\chatgpt\AAYS_WORK","D:\AAYS_WORK","D:\chatgpt\AAYS_WORK","C:\Users\cagda\Documents\GitHub\AAYS") | Where-Object { Test-Path $_ }
$candidateFiles = foreach ($root in $searchRoots) {
  Get-ChildItem -Path $root -Recurse -File -ErrorAction SilentlyContinue |
    Where-Object {
      $_.Extension -in @(".geojson",".json") -and
      $_.Length -gt 1024 -and
      $_.FullName -match "(parcel|polygon|boundary|boundaries|cadastre|cadastral|title|uprn|footprint|lookup|security)" -and
      $_.FullName -notmatch "parcel_internet_access_scores.geojson"
    } |
    Sort-Object Length -Descending
}

$best = $null
$bestIndex = $null
$bestMatches = 0
$bestKey = $null
$bestMode = $null
$summaries = @()

foreach ($file in @($candidateFiles | Select-Object -First 140)) {
  Write-Log "Inspecting $($file.FullName)"
  $idx = @{}
  $mode = "unknown"
  $featureCount = 0
  $polygonCount = 0
  $propKeys = @()
  $sampleMatches = 0
  $joinKey = $null

  try {
    $raw = Get-Content $file.FullName -Raw -ErrorAction Stop
    $obj = $raw | ConvertFrom-Json

    if ($obj.PSObject.Properties.Name -contains "features") {
      $mode = "feature_collection"
      $features = @($obj.features)
      $featureCount = $features.Count
      foreach ($pf in $features) {
        $geom = Get-Geometry $pf
        if ($geom) {
          $polygonCount++
          if ($pf.properties) {
            $propKeys += @($pf.properties.PSObject.Properties.Name)
            foreach ($k in ($preferredKeys | Select-Object -Unique)) {
              if ($pf.properties.PSObject.Properties.Name -contains $k) {
                $v = [string]$pf.properties.$k
                if ($v -and $scoreIndex.ContainsKey($v.Trim())) {
                  Try-RegisterGeometry $idx $v.Trim() $geom
                  $joinKey = $k
                }
              }
            }
          }
        }
      }
    }
    elseif ($obj -is [System.Collections.IEnumerable]) {
      $mode = "array"
      $items = @($obj)
      $featureCount = $items.Count
      foreach ($it in $items) {
        $geom = Get-Geometry $it
        if ($geom) {
          $polygonCount++
          $propKeys += @($it.PSObject.Properties.Name)
          foreach ($k in ($preferredKeys | Select-Object -Unique)) {
            if ($it.PSObject.Properties.Name -contains $k) {
              $v = [string]$it.$k
              if ($v -and $scoreIndex.ContainsKey($v.Trim())) {
                Try-RegisterGeometry $idx $v.Trim() $geom
                $joinKey = $k
              }
            }
          }
        }
      }
    }
    else {
      $mode = "object_or_lookup"
      foreach ($p in $obj.PSObject.Properties) {
        $candidateKey = [string]$p.Name
        $val = $p.Value
        $geom = Get-Geometry $val
        if ($geom) {
          $polygonCount++
          if ($scoreIndex.ContainsKey($candidateKey)) {
            Try-RegisterGeometry $idx $candidateKey $geom
            $joinKey = "top_level_key"
          }
        }
        elseif ($val -and ($val.PSObject.Properties.Name -contains "properties") -and ($val.PSObject.Properties.Name -contains "geometry")) {
          $geom2 = Get-Geometry $val
          if ($geom2) {
            $polygonCount++
            $kv = Get-PropValue $val.properties $preferredKeys
            if ($kv -and $scoreIndex.ContainsKey($kv.value)) {
              Try-RegisterGeometry $idx $kv.value $geom2
              $joinKey = $kv.key
            }
          }
        }
      }
      $featureCount = $obj.PSObject.Properties.Count
    }

    $sampleMatches = $idx.Count
    $summaries += [ordered]@{
      file = $file.FullName
      size = $file.Length
      mode = $mode
      feature_count = $featureCount
      polygon_count = $polygonCount
      sample_matches = $sampleMatches
      join_key = $joinKey
      sample_property_keys = @($propKeys | Select-Object -Unique | Select-Object -First 40)
    }

    if ($sampleMatches -gt $bestMatches) {
      $bestMatches = $sampleMatches
      $best = $file.FullName
      $bestIndex = $idx
      $bestKey = $joinKey
      $bestMode = $mode
    }
  }
  catch {
    $summaries += [ordered]@{ file=$file.FullName; size=$file.Length; error=$_.Exception.Message }
  }
}

if (-not $best -or $bestMatches -le 0) {
  [ordered]@{
    task_id = $taskId
    fix_id = $fixId
    status = "REAL_PARCEL_GEOMETRY_JOIN_BLOCKED_NO_MATCHING_KEY"
    completion_percent = 72
    final_ready = $false
    production_complete = $false
    score_feature_count = $scoreFeatures.Count
    score_join_key_detected = $scoreKeyName
    searched_roots = $searchRoots
    candidate_count = @($candidateFiles).Count
    inspected_candidate_count = @($summaries).Count
    candidates = $summaries
    required_next_action = "Provide or identify a real Polygon/MultiPolygon parcel source with parcel_id/uprn/title_number compatible with the score dataset. Fake geometry refused."
    generated_at = (Get-Date -Format o)
  } | ConvertTo-Json -Depth 20 | Set-Content -Encoding UTF8 $repoReport

  @"
status=REAL_PARCEL_GEOMETRY_JOIN_BLOCKED_NO_MATCHING_KEY
completion_percent=72
final_ready=false
production_complete=false
score_join_key_detected=$scoreKeyName
candidate_count=$(@($candidateFiles).Count)
inspected_candidate_count=$(@($summaries).Count)
"@ | Set-Content -Encoding UTF8 $repoStatus

  throw "No matching real geometry key found. See $repoReport"
}

$joined = 0
$nullAfter = 0
foreach ($sf in $scoreFeatures) {
  $kv = Get-PropValue $sf.properties @($scoreKeyName,"parcel_id","id","uprn","UPRN","title_number","title_no","title")
  if ($kv -and $bestIndex.ContainsKey($kv.value)) {
    $sf.geometry = $bestIndex[$kv.value]
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
  source_polygon_source = $best
  join_key = $bestKey
  join_mode = $bestMode
  joined_geometry_count = $joined
  null_geometry_after_join = $nullAfter
  generated_at = (Get-Date -Format o)
} | ConvertTo-Json -Depth 10 | Set-Content -Encoding UTF8 $detailJson

$status = if ($nullAfter -eq 0 -and $joined -eq $scoreFeatures.Count) { "REAL_PARCEL_GEOMETRY_JOIN_READY" } else { "REAL_PARCEL_GEOMETRY_JOIN_PARTIAL" }
$percent = if ($status -eq "REAL_PARCEL_GEOMETRY_JOIN_READY") { 99 } else { 74 }
[ordered]@{
  task_id = $taskId
  fix_id = $fixId
  status = $status
  completion_percent = $percent
  final_ready = $false
  production_complete = $false
  selected_source = $best
  selected_mode = $bestMode
  selected_join_key = $bestKey
  score_feature_count = $scoreFeatures.Count
  joined_geometry_count = $joined
  null_geometry_after_join = $nullAfter
  ready_geojson = $readyGeoJson
  ready_csv = $readyCsv
  ready_breakdown = $readyBreakdown
  detail_json = $detailJson
  candidates = $summaries
  generated_at = (Get-Date -Format o)
} | ConvertTo-Json -Depth 20 | Set-Content -Encoding UTF8 $repoReport

@"
status=$status
completion_percent=$percent
selected_source=$best
selected_mode=$bestMode
selected_join_key=$bestKey
score_feature_count=$($scoreFeatures.Count)
joined_geometry_count=$joined
null_geometry_after_join=$nullAfter
ready_geojson=$readyGeoJson
"@ | Set-Content -Encoding UTF8 $repoStatus

"V2_SCHEMA_PROBE_FINISHED=$(Get-Date -Format o)" | Add-Content -Encoding UTF8 "$heartbeatDir/latest.txt"
