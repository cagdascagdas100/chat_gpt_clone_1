$ErrorActionPreference = 'Continue'
$ProgressPreference = 'SilentlyContinue'

$TaskId = 'security-asayis-london-pilot-001-fdrive-20260609'
$StartedAt = (Get-Date).ToString('o')

# Repo stays on C if that is how the runner is configured. Heavy/new work goes to F only.
$RepoRoot = (Get-Location).Path
$RepoDataDir = Join-Path $RepoRoot 'england_map_web\data'
$RepoStatusDir = Join-Path $RepoRoot 'docs\chatgpt_status'
$RepoOutDir = Join-Path $RepoRoot 'ai-results'

$FWorkRoot = 'F:\chatgpt\AAYS_WORK\security_asayis_london_pilot_20260609'
$FDataDir = Join-Path $FWorkRoot 'data'
$FQaDir = Join-Path $FWorkRoot 'qa'
$FOutDir = Join-Path $FWorkRoot 'ai-results'
$FLogDir = Join-Path $FWorkRoot 'logs'

New-Item -ItemType Directory -Force -Path $RepoStatusDir, $RepoOutDir, $FWorkRoot, $FDataDir, $FQaDir, $FOutDir, $FLogDir | Out-Null

$InputPointGeojson = Join-Path $RepoDataDir 'parcel_security_scores_rechecked_0_120m_spatial.geojson'
$InputPolygonGeojson = Join-Path $RepoDataDir 'parcel_security_scores_polygons.geojson'

# Heavy/full outputs: F drive only.
$LondonPointOut = Join-Path $FDataDir 'parcel_security_scores_london_pilot_points.geojson'
$LondonPolygonOut = Join-Path $FDataDir 'parcel_security_scores_london_pilot_polygons.geojson'
$LondonSummaryOut = Join-Path $FDataDir 'parcel_security_london_pilot_summary.json'
$LondonMethodOut = Join-Path $FDataDir 'security_london_pilot_method_manifest.json'
$ColorMatrix = Join-Path $FQaDir 'london_security_color_level_matrix.csv'
$AcceptanceMd = Join-Path $FQaDir 'london_security_acceptance.md'

# GitHub-readable lightweight outputs: repo ai-results/status only.
$LatestMd = Join-Path $RepoOutDir 'security_london_pilot_latest_status.md'
$LatestJson = Join-Path $RepoOutDir 'security_london_pilot_latest_status.json'
$StatusMd = Join-Path $RepoStatusDir 'security_london_pilot_status_20260609.md'
$FLatestMd = Join-Path $FOutDir 'security_london_pilot_latest_status.md'
$FLatestJson = Join-Path $FOutDir 'security_london_pilot_latest_status.json'

# London pilot boundary: conservative Greater London bbox in WGS84.
$LondonBBox = [ordered]@{
  min_lon = -0.510375
  min_lat = 51.286760
  max_lon = 0.334015
  max_lat = 51.691874
}

function Test-InLondonBBoxFromCoordinates {
  param([object]$Coordinates)
  try {
    if ($null -eq $Coordinates) { return $false }
    if ($Coordinates.Count -ge 2 -and ($Coordinates[0] -is [double] -or $Coordinates[0] -is [int] -or $Coordinates[0] -is [decimal])) {
      $lon = [double]$Coordinates[0]
      $lat = [double]$Coordinates[1]
      return ($lon -ge $LondonBBox.min_lon -and $lon -le $LondonBBox.max_lon -and $lat -ge $LondonBBox.min_lat -and $lat -le $LondonBBox.max_lat)
    }
    foreach ($item in $Coordinates) {
      if (Test-InLondonBBoxFromCoordinates -Coordinates $item) { return $true }
    }
    return $false
  } catch {
    return $false
  }
}

function Test-LondonByProperties {
  param([object]$Props)
  if ($null -eq $Props) { return $false }
  $textParts = @()
  foreach ($name in $Props.PSObject.Properties.Name) {
    $value = $Props.$name
    if ($null -ne $value) { $textParts += [string]$value }
  }
  $text = ($textParts -join ' ').ToLowerInvariant()
  if ($text -match 'greater london|london|city of london|westminster|camden|greenwich|hackney|hammersmith|fulham|islington|kensington|chelsea|lambeth|lewisham|southwark|tower hamlets|wandsworth|barnet|bexley|brent|bromley|croydon|ealing|enfield|haringey|harrow|havering|hillingdon|hounslow|kingston upon thames|merton|newham|redbridge|richmond upon thames|sutton|waltham forest') { return $true }
  return $false
}

function Normalize-SafetyLevelId {
  param([object]$Props)
  $raw = ''
  if ($Props.PSObject.Properties.Name -contains 'safety_level_id') { $raw = [string]$Props.safety_level_id }
  elseif ($Props.PSObject.Properties.Name -contains 'safety_level') { $raw = [string]$Props.safety_level }
  elseif ($Props.PSObject.Properties.Name -contains 'security_level') { $raw = [string]$Props.security_level }
  $map = @{
    'very_low'='very_low'; 'low'='low'; 'medium'='medium'; 'good'='good'; 'very_good'='very_good';
    'Cok Dusuk'='very_low'; 'Çok Düşük'='very_low'; 'Dusuk'='low'; 'Düşük'='low'; 'Orta'='medium'; 'Iyi'='good'; 'İyi'='good'; 'Cok Iyi'='very_good'; 'Çok İyi'='very_good'
  }
  if ($map.ContainsKey($raw)) { return $map[$raw] }
  return 'no_data'
}

function Get-FileMeta {
  param([string]$Path)
  $meta = [ordered]@{ path=$Path; exists=(Test-Path $Path); size_bytes=0; sha256=$null }
  if (Test-Path $Path) {
    try { $meta.size_bytes = (Get-Item $Path).Length } catch {}
    try { $meta.sha256 = (Get-FileHash $Path -Algorithm SHA256).Hash } catch {}
  }
  return $meta
}

function Filter-GeoJsonLondon {
  param(
    [string]$InputPath,
    [string]$OutputPath,
    [string]$Label
  )
  $result = [ordered]@{
    label = $Label
    input_path = $InputPath
    output_path = $OutputPath
    input_exists = (Test-Path $InputPath)
    output_written = $false
    total_features = 0
    london_features = 0
    geometry_counts = [ordered]@{}
    safety_level_counts = [ordered]@{}
    confidence_label_counts = [ordered]@{}
    output_meta = $null
    error = $null
  }
  if (-not (Test-Path $InputPath)) { return $result }
  try {
    $raw = Get-Content $InputPath -Raw -Encoding UTF8
    $geo = $raw | ConvertFrom-Json
    $features = @($geo.features)
    $result.total_features = $features.Count
    $selected = New-Object System.Collections.Generic.List[object]
    foreach ($feature in $features) {
      $geomType = [string]$feature.geometry.type
      if (-not $result.geometry_counts.Contains($geomType)) { $result.geometry_counts[$geomType] = 0 }
      $result.geometry_counts[$geomType]++

      $isLondon = (Test-LondonByProperties -Props $feature.properties) -or (Test-InLondonBBoxFromCoordinates -Coordinates $feature.geometry.coordinates)
      if ($isLondon) {
        $levelId = Normalize-SafetyLevelId -Props $feature.properties
        $feature.properties | Add-Member -NotePropertyName 'safety_level_id' -NotePropertyValue $levelId -Force
        $feature.properties | Add-Member -NotePropertyName 'pilot_scope' -NotePropertyValue 'london_only' -Force
        $feature.properties | Add-Member -NotePropertyName 'f_work_root' -NotePropertyValue $FWorkRoot -Force
        $feature.properties | Add-Member -NotePropertyName 'police_data_precision_note' -NotePropertyValue 'Police.uk locations are anonymised/approximate; this is an area/LSOA-based safety estimate, not exact parcel crime evidence.' -Force
        $selected.Add($feature) | Out-Null

        if (-not $result.safety_level_counts.Contains($levelId)) { $result.safety_level_counts[$levelId] = 0 }
        $result.safety_level_counts[$levelId]++
        $confidence = 'unknown'
        if ($feature.properties.PSObject.Properties.Name -contains 'confidence_label') { $confidence = [string]$feature.properties.confidence_label }
        elseif ($feature.properties.PSObject.Properties.Name -contains 'confidence') { $confidence = [string]$feature.properties.confidence }
        if (-not $result.confidence_label_counts.Contains($confidence)) { $result.confidence_label_counts[$confidence] = 0 }
        $result.confidence_label_counts[$confidence]++
      }
    }
    $outGeo = [ordered]@{
      type = 'FeatureCollection'
      name = "security_asayis_london_pilot_$Label"
      pilot_scope = 'london_only'
      storage_policy = 'heavy_outputs_on_f_drive_only; repo receives lightweight status manifests'
      f_work_root = $FWorkRoot
      bbox_filter = $LondonBBox
      precision_note = 'Police.uk locations are anonymised/approximate; output is area/LSOA-based, not exact parcel crime evidence.'
      features = @($selected)
    }
    $outJson = $outGeo | ConvertTo-Json -Depth 100
    Set-Content -Path $OutputPath -Value $outJson -Encoding UTF8
    $result.london_features = $selected.Count
    $result.output_written = $true
    $result.output_meta = Get-FileMeta -Path $OutputPath
  } catch {
    $result.error = $_.Exception.Message
  }
  return $result
}

$pointResult = Filter-GeoJsonLondon -InputPath $InputPointGeojson -OutputPath $LondonPointOut -Label 'points'
$polygonResult = Filter-GeoJsonLondon -InputPath $InputPolygonGeojson -OutputPath $LondonPolygonOut -Label 'polygons'

$method = [ordered]@{
  method_id = 'security_london_pilot_fdrive_v1'
  task_id = $TaskId
  scope = 'London only / Greater London bbox plus London property-name fallback'
  started_at = $StartedAt
  completed_at = (Get-Date).ToString('o')
  repo_root = $RepoRoot
  f_work_root = $FWorkRoot
  storage_policy = 'new/heavy processing outputs on F drive; GitHub repo receives small status and manifest outputs only'
  db_write = $false
  ddl = $false
  migration = $false
  production_deploy = $false
  fake_data = $false
  police_precision_note = 'Police.uk street-level crime locations are anonymised/approximate and must not be displayed as exact parcel crime evidence.'
  expected_next_step = 'Review London pilot outputs from F-drive metadata, then prepare London-only frontend overlay wiring if counts are valid.'
  london_bbox = $LondonBBox
}

$summary = [ordered]@{
  task_id = $TaskId
  scope = 'london_only'
  started_at = $StartedAt
  completed_at = (Get-Date).ToString('o')
  f_work_root = $FWorkRoot
  repo_root = $RepoRoot
  point_result = $pointResult
  polygon_result = $polygonResult
  method = $method
  outputs = [ordered]@{
    f_london_points_geojson = $LondonPointOut
    f_london_polygons_geojson = $LondonPolygonOut
    f_summary_json = $LondonSummaryOut
    f_method_manifest = $LondonMethodOut
    f_color_matrix = $ColorMatrix
    f_acceptance_md = $AcceptanceMd
    repo_latest_md = $LatestMd
    repo_latest_json = $LatestJson
    repo_status_md = $StatusMd
  }
  acceptance = [ordered]@{
    has_london_point_output = [bool]$pointResult.output_written
    has_london_polygon_output = [bool]$polygonResult.output_written
    has_any_london_features = (($pointResult.london_features + $polygonResult.london_features) -gt 0)
    ready_for_frontend_patch = (($pointResult.london_features + $polygonResult.london_features) -gt 0)
  }
}

$summary | ConvertTo-Json -Depth 100 | Set-Content -Path $LondonSummaryOut -Encoding UTF8
$method | ConvertTo-Json -Depth 20 | Set-Content -Path $LondonMethodOut -Encoding UTF8

@'
safety_level_id,display_label,color,meaning
very_low,Çok Düşük,#8b0000,Lower safety estimate / higher crime-risk percentile
low,Düşük,#d73027,Below average safety estimate
medium,Orta,#fee08b,Middle band
good,İyi,#91cf60,Above average safety estimate
very_good,Çok İyi,#1a9850,Higher safety estimate / lower crime-risk percentile
no_data,Veri Yok,#9ca3af,No reliable London pilot score available
'@ | Set-Content -Path $ColorMatrix -Encoding UTF8

$md = @()
$md += '# Security / Asayiş London-only Pilot Status — F Drive Work Root'
$md += ''
$md += "Task: $TaskId"
$md += "Started: $StartedAt"
$md += "Completed: $((Get-Date).ToString('o'))"
$md += "F work root: $FWorkRoot"
$md += "Repo root: $RepoRoot"
$md += ''
$md += '## Guardrails'
$md += '- DB write: false'
$md += '- DDL: false'
$md += '- Migration: false'
$md += '- Production deploy: false'
$md += '- Fake data: false'
$md += ''
$md += '## Storage Policy'
$md += '- New/heavy processing outputs are written to F drive only.'
$md += '- Existing C-drive repo files are not moved.'
$md += '- GitHub-readable repo outputs are limited to lightweight status/summary files under ai-results and docs/chatgpt_status.'
$md += '- All-England outputs are not overwritten.'
$md += ''
$md += '## Scope'
$md += '- London only / Greater London bounding box plus London borough/property-name fallback.'
$md += '- Police.uk locations are anonymised/approximate; UI must label results as area/LSOA-based safety estimates, not exact parcel crime evidence.'
$md += ''
$md += '## Results'
$md += "- Point input exists: $($pointResult.input_exists)"
$md += "- Point total features: $($pointResult.total_features)"
$md += "- Point London features: $($pointResult.london_features)"
$md += "- Point output on F: $LondonPointOut"
$md += "- Polygon input exists: $($polygonResult.input_exists)"
$md += "- Polygon total features: $($polygonResult.total_features)"
$md += "- Polygon London features: $($polygonResult.london_features)"
$md += "- Polygon output on F: $LondonPolygonOut"
$md += ''
$md += '## F Outputs'
$md += "- $LondonPointOut"
$md += "- $LondonPolygonOut"
$md += "- $LondonSummaryOut"
$md += "- $LondonMethodOut"
$md += "- $ColorMatrix"
$md += "- $AcceptanceMd"
$md += ''
$md += '## Next Step'
$md += 'If London feature counts are valid, create London-only frontend overlay wiring and popup evidence note. Keep all-England files untouched.'
$mdText = $md -join [Environment]::NewLine

Set-Content -Path $FLatestMd -Value $mdText -Encoding UTF8
Set-Content -Path $AcceptanceMd -Value $mdText -Encoding UTF8
Set-Content -Path $FLatestJson -Value ($summary | ConvertTo-Json -Depth 100) -Encoding UTF8

# Lightweight GitHub-readable copies only.
Set-Content -Path $LatestMd -Value $mdText -Encoding UTF8
Set-Content -Path $StatusMd -Value $mdText -Encoding UTF8
Set-Content -Path $LatestJson -Value ($summary | ConvertTo-Json -Depth 100) -Encoding UTF8

Write-Host $mdText
exit 0
