$ErrorActionPreference = 'Continue'
$TaskId = 'security-asayis-001-readonly-inventory-20260609'
$StartedAt = Get-Date -Format s
$BridgeRoot = if ($env:AAYS_BRIDGE_ROOT) { $env:AAYS_BRIDGE_ROOT } else { 'C:\AAYS_GITHUB_BRIDGE_CLEAN2' }
$ResultDir = Join-Path $BridgeRoot 'ai-results'
New-Item -ItemType Directory -Force -Path $ResultDir | Out-Null

function Add-Line { param([string[]]$Lines,[string]$Text) return @($Lines + $Text) }
function Count-Regex { param([string]$Text,[string]$Pattern) try { return ([regex]::Matches($Text,$Pattern)).Count } catch { return -1 } }
function Count-FieldValues {
  param([string]$Text,[string]$Field)
  $dict = [ordered]@{}
  try {
    $pattern = '"' + [regex]::Escape($Field) + '"\s*:\s*"([^"]*)"'
    foreach ($m in [regex]::Matches($Text,$pattern)) {
      $v = [string]$m.Groups[1].Value
      if (-not $dict.Contains($v)) { $dict[$v] = 0 }
      $dict[$v]++
    }
  } catch {}
  return $dict
}
function Dict-ToText {
  param($Dict)
  if ($null -eq $Dict -or $Dict.Count -eq 0) { return '{}' }
  return (($Dict.GetEnumerator() | Sort-Object Name | ForEach-Object { $_.Name + '=' + $_.Value }) -join '; ')
}
function Has-Text { param([string]$Text,[string]$Pattern) if ([string]::IsNullOrEmpty($Text)) { return $false } return ($Text -match [regex]::Escape($Pattern)) }

$ProjectCandidates = @()
if ($env:AAYS_PROJECT_ROOT) { $ProjectCandidates += $env:AAYS_PROJECT_ROOT }
$ProjectCandidates += 'C:\Users\cagda\Documents\GitHub\AAYS'
$ProjectCandidates += 'C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence'
$ProjectCandidates += (Get-Location).Path
$ProjectCandidates = $ProjectCandidates | Where-Object { $_ -and (Test-Path $_) } | Select-Object -Unique

$WebCandidates = @()
foreach ($root in $ProjectCandidates) {
  $WebCandidates += (Join-Path $root 'england_map_web')
  $WebCandidates += (Join-Path $root 'terrayield_land_intelligence\england_map_web')
}
$WebRoot = $null
foreach ($w in ($WebCandidates | Select-Object -Unique)) {
  if ((Test-Path (Join-Path $w 'app.js')) -or (Test-Path (Join-Path $w 'security_overlay.js'))) { $WebRoot = $w; break }
}

$appPath = if ($WebRoot) { Join-Path $WebRoot 'app.js' } else { '' }
$overlayPath = if ($WebRoot) { Join-Path $WebRoot 'security_overlay.js' } else { '' }
$indexPath = if ($WebRoot) { Join-Path $WebRoot 'index.html' } else { '' }
$geoPath = if ($WebRoot) { Join-Path $WebRoot 'data\parcel_security_scores_rechecked_0_120m_spatial.geojson' } else { '' }
$polyPath = if ($WebRoot) { Join-Path $WebRoot 'data\parcel_security_scores_polygons.geojson' } else { '' }
$summaryPath = if ($WebRoot) { Join-Path $WebRoot 'data\parcel_security_match_summary.json' } else { '' }
$iconPath = if ($WebRoot) { Join-Path $WebRoot 'assets\icons\terrayield_icons\security.png' } else { '' }

$appText = if ($appPath -and (Test-Path $appPath)) { Get-Content -Raw -Encoding UTF8 $appPath } else { '' }
$overlayText = if ($overlayPath -and (Test-Path $overlayPath)) { Get-Content -Raw -Encoding UTF8 $overlayPath } else { '' }
$indexText = if ($indexPath -and (Test-Path $indexPath)) { Get-Content -Raw -Encoding UTF8 $indexPath } else { '' }

$geoText = ''
if ($geoPath -and (Test-Path $geoPath)) {
  try { $geoText = Get-Content -Raw -Encoding UTF8 $geoPath } catch { $geoText = '' }
}

$featureCount = if ($geoText) { Count-Regex $geoText '"type"\s*:\s*"Feature"' } else { 0 }
$pointCount = if ($geoText) { Count-Regex $geoText '"type"\s*:\s*"Point"' } else { 0 }
$polygonCount = if ($geoText) { Count-Regex $geoText '"type"\s*:\s*"Polygon"' } else { 0 }
$multiPolygonCount = if ($geoText) { Count-Regex $geoText '"type"\s*:\s*"MultiPolygon"' } else { 0 }
$safetyLevels = if ($geoText) { Count-FieldValues $geoText 'safety_level' } else { [ordered]@{} }
$confidenceLabels = if ($geoText) { Count-FieldValues $geoText 'confidence_label' } else { [ordered]@{} }
$matchStatuses = if ($geoText) { Count-FieldValues $geoText 'security_match_status' } else { [ordered]@{} }
if ($matchStatuses.Count -eq 0 -and $geoText) { $matchStatuses = Count-FieldValues $geoText 'match_status' }

$summaryText = if ($summaryPath -and (Test-Path $summaryPath)) { Get-Content -Raw -Encoding UTF8 $summaryPath } else { '' }
$nodeCheckApp = 'NOT_RUN'
if ($appPath -and (Test-Path $appPath)) {
  try {
    $nodeOut = (& node --check $appPath 2>&1 | Out-String)
    if ($LASTEXITCODE -eq 0) { $nodeCheckApp = 'PASS' } else { $nodeCheckApp = 'FAIL: ' + $nodeOut.Trim() }
  } catch { $nodeCheckApp = 'ERROR: ' + $_.Exception.Message }
}

$iconHash = ''
if ($iconPath -and (Test-Path $iconPath)) {
  try { $iconHash = (Get-FileHash $iconPath -Algorithm SHA256).Hash } catch { $iconHash = 'HASH_ERROR' }
}

$polygonReady = ($polyPath -and (Test-Path $polyPath))
$webRootFound = [bool]$WebRoot
$worthUsesSecurityPng = (Has-Text $appText 'terrayield_icons/security.png') -and (-not (Has-Text $appText 'worth-security.svg'))
$worthStillSvg = Has-Text $appText 'worth-security.svg'
$overlayAscii = (Has-Text $overlayText 'Cok Dusuk') -or (Has-Text $overlayText 'Cok Iyi')
$overlayUnicode = (Has-Text $overlayText 'Çok Düşük') -or (Has-Text $overlayText 'Çok İyi') -or (Has-Text $overlayText 'Düşük')

$blockers = @()
if (-not $webRootFound) { $blockers += 'WEB_ROOT_NOT_FOUND' }
if ($featureCount -le 0) { $blockers += 'GEOJSON_EMPTY_OR_MISSING' }
if ($featureCount -gt 0 -and (($polygonCount + $multiPolygonCount) -eq 0)) { $blockers += 'NO_PARCEL_POLYGON_GEOMETRY' }
if ($worthStillSvg) { $blockers += 'WORTH_MENU_STILL_USES_SVG' }
if (-not $overlayAscii) { $blockers += 'OVERLAY_ASCII_LEVEL_IDS_NOT_CONFIRMED' }
if (-not $summaryText) { $blockers += 'SUMMARY_MISSING' }

$progress = 12
if ($webRootFound) { $progress += 8 }
if ($featureCount -gt 0) { $progress += 10 }
if ($nodeCheckApp -eq 'PASS') { $progress += 5 }
if ($iconHash) { $progress += 5 }
if ($polygonReady) { $progress += 20 }
if ($blockers.Count -eq 0) { $progress = 55 }

$CompletedAt = Get-Date -Format s
$md = @()
$md += '# SECURITY_ASAYIS_001_READONLY_INVENTORY'
$md += ''
$md += 'TASK_ID=' + $TaskId
$md += 'STATUS=FINISHED_READ_ONLY'
$md += 'STARTED_AT=' + $StartedAt
$md += 'COMPLETED_AT=' + $CompletedAt
$md += 'DB_WRITE=false'
$md += 'DDL=false'
$md += 'MIGRATION=false'
$md += 'PRODUCTION_DEPLOY=false'
$md += 'FAKE_DATA=false'
$md += ''
$md += '## Paths'
$md += 'BRIDGE_ROOT=' + $BridgeRoot
$md += 'WEB_ROOT_FOUND=' + $webRootFound
$md += 'WEB_ROOT=' + [string]$WebRoot
$md += 'APP_PATH=' + $appPath
$md += 'OVERLAY_PATH=' + $overlayPath
$md += 'GEOJSON_PATH=' + $geoPath
$md += 'POLYGON_GEOJSON_PATH=' + $polyPath
$md += 'SUMMARY_PATH=' + $summaryPath
$md += ''
$md += '## Frontend Checks'
$md += 'NODE_CHECK_APP_JS=' + $nodeCheckApp
$md += 'APP_HAS_SECURITY_CONTROL_MODE=' + (Has-Text $appText 'SECURITY_CONTROL_MODE')
$md += 'APP_HAS_TOGGLE_SECURITY=' + ((Has-Text $appText 'toggleSecurityOverlay') -or (Has-Text $appText 'AAYS_SECURITY'))
$md += 'APP_PRIMARY_SECURITY_PNG_PRESENT=' + (Has-Text $appText 'terrayield_icons/security.png')
$md += 'APP_WORTH_MENU_STILL_USES_SECURITY_SVG=' + $worthStillSvg
$md += 'APP_WORTH_MENU_FULLY_SECURITY_PNG=' + $worthUsesSecurityPng
$md += 'INDEX_LOADS_SECURITY_OVERLAY_JS=' + (Has-Text $indexText 'security_overlay.js')
$md += 'INDEX_LOADS_SECURITY_OVERLAY_CSS=' + (Has-Text $indexText 'security_overlay.css')
$md += 'OVERLAY_EXPECTS_ASCII_LEVELS=' + $overlayAscii
$md += 'OVERLAY_EXPECTS_UNICODE_LEVELS=' + $overlayUnicode
$md += 'SECURITY_ICON_SHA256=' + $iconHash
$md += ''
$md += '## GeoJSON Checks'
$md += 'GEOJSON_EXISTS=' + ($geoPath -and (Test-Path $geoPath))
$md += 'GEOJSON_FEATURE_COUNT=' + $featureCount
$md += 'GEOJSON_POINT_COUNT=' + $pointCount
$md += 'GEOJSON_POLYGON_COUNT=' + $polygonCount
$md += 'GEOJSON_MULTIPOLYGON_COUNT=' + $multiPolygonCount
$md += 'POLYGON_OUTPUT_EXISTS=' + $polygonReady
$md += 'GEOJSON_SAFETY_LEVELS=' + (Dict-ToText $safetyLevels)
$md += 'GEOJSON_CONFIDENCE_LABELS=' + (Dict-ToText $confidenceLabels)
$md += 'GEOJSON_MATCH_STATUSES=' + (Dict-ToText $matchStatuses)
$md += ''
$md += '## Blockers'
if ($blockers.Count -eq 0) { $md += 'BLOCKERS=none' } else { foreach ($b in $blockers) { $md += ('- ' + $b) } }
$md += ''
$md += '## Next Step Recommendation'
$md += 'NEXT_ACTION=Create SECURITY_ASAYIS_002 patch-plan task only after this inventory is reviewed. Do not patch frontend until ONAY: SECURITY_FRONTEND_PATCH is received.'
$md += 'NEXT_COMMAND=devam et'
$md += 'PROGRESS_PERCENT=' + $progress
$md += 'ETA_MINUTES_NEXT=8-12'

$latestMd = Join-Path $ResultDir 'security_asayis_latest_status.md'
$latestJson = Join-Path $ResultDir 'security_asayis_latest_status.json'
Set-Content -Encoding UTF8 -Path $latestMd -Value $md

$obj = [ordered]@{
  task_id=$TaskId; status='FINISHED_READ_ONLY'; progress_percent=$progress; eta_minutes_next='8-12'; db_write=$false; ddl=$false; migration=$false; production_deploy=$false; fake_data=$false;
  web_root_found=$webRootFound; web_root=[string]$WebRoot; node_check_app_js=$nodeCheckApp; geojson_feature_count=$featureCount; point_count=$pointCount; polygon_count=$polygonCount; multipolygon_count=$multiPolygonCount; polygon_output_exists=$polygonReady; blockers=$blockers; next_command='devam et'; completed_at=$CompletedAt
}
$obj | ConvertTo-Json -Depth 6 | Set-Content -Encoding UTF8 -Path $latestJson

$md -join "`n"
exit 0
