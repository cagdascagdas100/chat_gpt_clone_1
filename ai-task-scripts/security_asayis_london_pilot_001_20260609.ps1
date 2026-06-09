$ErrorActionPreference = 'Continue'
$ProgressPreference = 'SilentlyContinue'

$TaskId = 'security-asayis-london-pilot-001-20260609'
$StartedAt = (Get-Date).ToString('o')

$RepoRoot = (Get-Location).Path
$DataDir = Join-Path $RepoRoot 'england_map_web\data'
$StatusDir = Join-Path $RepoRoot 'docs\chatgpt_status'
$QaDir = Join-Path $RepoRoot 'qa\security_london_pilot'
$OutDir = Join-Path $RepoRoot 'ai-results'

New-Item -ItemType Directory -Force -Path $StatusDir, $QaDir, $OutDir | Out-Null

$InputPointGeojson = Join-Path $DataDir 'parcel_security_scores_rechecked_0_120m_spatial.geojson'
$InputPolygonGeojson = Join-Path $DataDir 'parcel_security_scores_polygons.geojson'
$LondonPointOut = Join-Path $DataDir 'parcel_security_scores_london_pilot_points.geojson'
$LondonPolygonOut = Join-Path $DataDir 'parcel_security_scores_london_pilot_polygons.geojson'
$LondonSummaryOut = Join-Path $DataDir 'parcel_security_london_pilot_summary.json'
$LondonMethodOut = Join-Path $DataDir 'security_london_pilot_method_manifest.json'
$LatestMd = Join-Path $OutDir 'security_london_pilot_latest_status.md'
$LatestJson = Join-Path $OutDir 'security_london_pilot_latest_status.json'
$StatusMd = Join-Path $StatusDir 'security_london_pilot_status_20260609.md'
$ColorMatrix = Join-Path $QaDir 'london_security_color_level_matrix.csv'
$AcceptanceMd = Join-Path $QaDir 'london_security_acceptance.md'

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
    # Point coordinates: [lon, lat]
    if ($Coordinates.Count -ge 2 -and ($Coordinates[0] -is [double] -or $Coordinates[0] -is [int] -or $Coordinates[0] -is [decimal])) {
      $lon = [double]$Coordinates[0]
      $lat = [double]$Coordinates[1]
      return ($lon -ge $LondonBBox.min_lon -and $lon -le $LondonBBox.max_lon -and $lat -ge $LondonBBox.min_lat -and $lat -le $LondonBBox.max_lat)
    }
    # Nested coordinates: recurse until a coordinate pair is found inside bbox.
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
        if (-not ($feature.properties.PSObject.Properties.Name -contains 'safety_level_id')) {
          $feature.properties | Add-Member -NotePropertyName 'safety_level_id' -NotePropertyValue $levelId -Force
        }
        if (-not ($feature.properties.PSObject.Properties.Name -contains 'pilot_scope')) {
          $feature.properties | Add-Member -NotePropertyName 'pilot_scope' -NotePropertyValue 'london_only' -Force
        }
        if (-not ($feature.properties.PSObject.Properties.Name -contains 'police_data_precision_note')) {
          $feature.properties | Add-Member -NotePropertyName 'police_data_precision_note' -NotePropertyValue 'Police.uk locations are anonymised/approximate; this is an area/LSOA-based safety estimate, not exact parcel crime evidence.' -Force
        }
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
      bbox_filter = $LondonBBox
      precision_note = 'Police.uk locations are anonymised/approximate; output is area/LSOA-based, not exact parcel crime evidence.'
      features = @($selected)
    }
    $outJson = $outGeo | ConvertTo-Json -Depth 100
    Set-Content -Path $OutputPath -Value $outJson -Encoding UTF8
    $result.london_features = $selected.Count
    $result.output_written = $true
  } catch {
    $result.error = $_.Exception.Message
  }
  return $result
}

$pointResult = Filter-GeoJsonLondon -InputPath $InputPointGeojson -OutputPath $LondonPointOut -Label 'points'
$polygonResult = Filter-GeoJsonLondon -InputPath $InputPolygonGeojson -OutputPath $LondonPolygonOut -Label 'polygons'

$method = [ordered]@{
  method_id = 'security_london_pilot_v1'
  task_id = $TaskId
  scope = 'London only / Greater London bbox plus London property-name fallback'
  started_at = $StartedAt
  completed_at = (Get-Date).ToString('o')
  db_write = $false
  ddl = $false
  migration = $false
  production_deploy = $false
  fake_data = $false
  police_precision_note = 'Police.uk street-level crime locations are anonymised/approximate and must not be displayed as exact parcel crime evidence.'
  expected_next_step = 'Review London pilot outputs, then prepare London-only frontend overlay wiring and popup evidence text if counts are valid.'
  london_bbox = $LondonBBox
}

$summary = [ordered]@{
  task_id = $TaskId
  scope = 'london_only'
  started_at = $StartedAt
  completed_at = (Get-Date).ToString('o')
  point_result = $pointResult
  polygon_result = $polygonResult
  method = $method
  outputs = [ordered]@{
    london_points_geojson = $LondonPointOut
    london_polygons_geojson = $LondonPolygonOut
    summary_json = $LondonSummaryOut
    method_manifest = $LondonMethodOut
    color_matrix = $ColorMatrix
    acceptance_md = $AcceptanceMd
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
$md += '# Security / Asayiş London-only Pilot Status'
$md += ''
$md += "Task: $TaskId"
$md += "Started: $StartedAt"
$md += "Completed: $((Get-Date).ToString('o'))"
$md += ''
$md += '## Guardrails'
$md += '- DB write: false'
$md += '- DDL: false'
$md += '- Migration: false'
$md += '- Production deploy: false'
$md += '- Fake data: false'
$md += ''
$md += '## Scope'
$md += '- London only / Greater London bounding box plus London borough/property-name fallback.'
$md += '- This pilot must not overwrite all-England outputs.'
$md += '- Police.uk locations are anonymised/approximate; UI must label results as area/LSOA-based safety estimates, not exact parcel crime evidence.'
$md += ''
$md += '## Results'
$md += "- Point input exists: $($pointResult.input_exists)"
$md += "- Point total features: $($pointResult.total_features)"
$md += "- Point London features: $($pointResult.london_features)"
$md += "- Polygon input exists: $($polygonResult.input_exists)"
$md += "- Polygon total features: $($polygonResult.total_features)"
$md += "- Polygon London features: $($polygonResult.london_features)"
$md += ''
$md += '## Outputs'
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
Set-Content -Path $LatestMd -Value $mdText -Encoding UTF8
Set-Content -Path $StatusMd -Value $mdText -Encoding UTF8
Set-Content -Path $AcceptanceMd -Value $mdText -Encoding UTF8
$summary | ConvertTo-Json -Depth 100 | Set-Content -Path $LatestJson -Encoding UTF8

Write-Host $mdText
exit 0
