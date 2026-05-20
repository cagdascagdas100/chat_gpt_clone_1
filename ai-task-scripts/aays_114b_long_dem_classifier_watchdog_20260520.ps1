$ErrorActionPreference='Continue'
$TaskId='aays-114b-long-dem-classifier-watchdog-20260520'
$Bridge='C:/AAYS_GITHUB_BRIDGE_CLEAN2'
$ResultDir=Join-Path $Bridge 'ai-results'
New-Item -ItemType Directory -Force -Path $ResultDir | Out-Null
$InputJson=Join-Path $ResultDir 'aays-113-dem-broad-inventory-20260519.result.json'
$OutJson=Join-Path $ResultDir 'aays-114b-long-dem-classifier-watchdog-20260520.result.json'
$Report=Join-Path $ResultDir 'aays-114b-long-dem-classifier-watchdog-20260520.report.md'
function W($m){ Add-Content -LiteralPath $Report -Encoding UTF8 -Value $m }
Set-Content -LiteralPath $Report -Encoding UTF8 -Value '# AAYS 114B Long DEM Classifier Watchdog'
W "start_utc=$((Get-Date).ToUniversalTime().ToString('o'))"
W 'mode=read_only_long_classifier'
$good=@('dem','dtm','dsm','lidar','terrain','elevation','srtm','aster','copernicus','os_terrain')
$bad=@('geoid','proj','postgis','ntv2','etrs','ostn','osgm','velocity','vel','gridshift','epsg')
$candidates=@()
if(Test-Path -LiteralPath $InputJson){
  try{ $j=Get-Content -LiteralPath $InputJson -Raw | ConvertFrom-Json; foreach($c in $j.top_candidates){ $candidates += $c } } catch { W "input_json_error=$($_.Exception.Message)" }
} else { W "missing_input_json=$InputJson" }
$final=@()
for($cycle=1;$cycle -le 10;$cycle++){
  W ""
  W "## cycle_$cycle $((Get-Date).ToUniversalTime().ToString('o'))"
  $possible=0; $rejected=0; $unknown=0
  foreach($c in $candidates){
    $s=(([string]$c.path)+' '+([string]$c.name)).ToLower()
    $gs=0; $bs=0
    foreach($x in $good){ if($s.Contains($x)){ $gs++ } }
    foreach($x in $bad){ if($s.Contains($x)){ $bs++ } }
    $class='unknown'
    if($gs -gt 0 -and $bs -eq 0){ $class='possible_dem_dtm'; $possible++ }
    elseif($bs -gt 0){ $class='not_terrain_dem_projection_or_geoid_grid'; $rejected++ }
    else { $unknown++ }
    if($cycle -eq 1){ $final += [ordered]@{path=$c.path; name=$c.name; size_mb=$c.size_mb; good_score=$gs; reject_score=$bs; classification=$class} }
  }
  W "candidate_count=$($candidates.Count) possible=$possible rejected=$rejected unknown=$unknown"
  if($cycle -lt 10){ Start-Sleep -Seconds 180 }
}
$possibleRows=@($final | Where-Object { $_.classification -eq 'possible_dem_dtm' })
$rejectedRows=@($final | Where-Object { $_.classification -eq 'not_terrain_dem_projection_or_geoid_grid' })
$status='completed_no_valid_dem'
if($possibleRows.Count -gt 0){ $status='completed_possible_dem_found' }
$obj=[ordered]@{task_id=$TaskId;status=$status;generated_at_utc=(Get-Date).ToUniversalTime().ToString('o');input_candidate_count=$candidates.Count;possible_dem_count=$possibleRows.Count;rejected_count=$rejectedRows.Count;possible_dem_candidates=$possibleRows;rejected_examples=($rejectedRows|Select-Object -First 25);next_step='If possible_dem_count is zero, place official DEM or DTM raster under E:/AAYS_DATA/elevation and rerun AAYS-112.';safety=@{no_db_write=$true;no_production_deploy=$true;no_fake_elevation_values=$true}}
$obj | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $OutJson -Encoding UTF8
W ""
W "## final"
W "status=$status"
W "possible_dem_count=$($possibleRows.Count)"
W "result_json=$OutJson"
W "end_utc=$((Get-Date).ToUniversalTime().ToString('o'))"
Write-Host 'AAYS_114B_LONG_DONE'