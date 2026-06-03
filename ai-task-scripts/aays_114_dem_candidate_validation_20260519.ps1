$ErrorActionPreference='Continue'
$TaskId='aays-114-dem-candidate-validation-20260519'
$Start=Get-Date
$BridgeRoot='C:/AAYS_GITHUB_BRIDGE_CLEAN2'
$ResultDir=Join-Path $BridgeRoot 'ai-results'
New-Item -ItemType Directory -Force -Path $ResultDir | Out-Null
$InJson=Join-Path $ResultDir 'aays-113-dem-broad-inventory-20260519.result.json'
$OutJson=Join-Path $ResultDir 'aays-114-dem-candidate-validation-20260519.result.json'
$Report=Join-Path $ResultDir 'aays-114-dem-candidate-validation-20260519.report.md'
function W($m){ Add-Content -LiteralPath $Report -Encoding UTF8 -Value $m }
Set-Content -LiteralPath $Report -Encoding UTF8 -Value '# AAYS 114 DEM Candidate Validation'
W "start_utc=$((Get-Date).ToUniversalTime().ToString('o'))"
W 'mode=read_only_long_validation_no_db_write_no_download'
$rejectTokens=@('proj','postgis','geoid','ntv2','etrs','epsg','vel','swiss','linz','lmi','gku','inegi','rednap','osgbtoetrs','ostn','osgm')
$goodTokens=@('dem','dtm','dsm','lidar','terrain','elevation','surface','composite')
$candidates=@()
if(Test-Path -LiteralPath $InJson){
  try{
    $j=Get-Content -LiteralPath $InJson -Raw | ConvertFrom-Json
    foreach($c in $j.top_candidates){ $candidates += $c }
  } catch { W "read_inventory_json_error=$($_.Exception.Message)" }
} else { W "missing_input_json=$InJson" }
$validated=@()
for($pass=1;$pass -le 10;$pass++){
  W ""
  W "## pass_$pass $((Get-Date).ToUniversalTime().ToString('o'))"
  $i=0
  foreach($c in $candidates){
    $i++
    $name=([string]$c.name).ToLower()
    $path=[string]$c.path
    $rejectScore=0; $goodScore=0
    foreach($t in $rejectTokens){ if($name.Contains($t) -or $path.ToLower().Contains($t)){ $rejectScore++ } }
    foreach($t in $goodTokens){ if($name.Contains($t) -or $path.ToLower().Contains($t)){ $goodScore++ } }
    $classification='unknown_raster'
    if($rejectScore -gt 0 -and $goodScore -eq 0){ $classification='not_dem_projection_or_geoid_grid' }
    elseif($goodScore -gt 0 -and $rejectScore -eq 0){ $classification='possible_dem_dtm' }
    elseif($goodScore -gt 0 -and $rejectScore -gt 0){ $classification='mixed_needs_manual_review' }
    $exists=Test-Path -LiteralPath $path
    if($pass -eq 1){
      $validated += [ordered]@{path=$path; name=$c.name; size_mb=$c.size_mb; exists=$exists; good_score=$goodScore; reject_score=$rejectScore; classification=$classification}
    }
    if($i -le 40){ W "candidate=$name class=$classification good=$goodScore reject=$rejectScore exists=$exists" }
  }
  W "pass_$pass_checked=$($candidates.Count)"
  if($pass -lt 10){ Start-Sleep -Seconds 180 }
}
$possible=@($validated | Where-Object { $_.classification -eq 'possible_dem_dtm' -or $_.classification -eq 'mixed_needs_manual_review' })
$rejected=@($validated | Where-Object { $_.classification -eq 'not_dem_projection_or_geoid_grid' })
$status='completed_no_valid_dem'
if($possible.Count -gt 0){ $status='completed_possible_dem_found' }
$obj=[ordered]@{
  task_id=$TaskId
  status=$status
  generated_at_utc=(Get-Date).ToUniversalTime().ToString('o')
  input_candidate_count=$candidates.Count
  possible_dem_count=$possible.Count
  rejected_projection_grid_count=$rejected.Count
  possible_dem_candidates=$possible
  rejected_examples=($rejected | Select-Object -First 30)
  next_step='If no possible DEM remains, place official Environment Agency/OS DEM-DTM raster under E:/AAYS_DATA/elevation/ and rerun AAYS-112. If possible DEM exists, run raster readability and CRS validation first.'
}
$obj | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $OutJson -Encoding UTF8
W ""
W "## final"
W "status=$status"
W "possible_dem_count=$($possible.Count)"
W "rejected_projection_grid_count=$($rejected.Count)"
W "result_json=$OutJson"
W "end_utc=$((Get-Date).ToUniversalTime().ToString('o'))"
Write-Host "AAYS_114_OUTPUT=$ResultDir"