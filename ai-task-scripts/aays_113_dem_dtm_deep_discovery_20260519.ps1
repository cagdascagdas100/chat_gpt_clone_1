$ErrorActionPreference = 'Continue'
$TaskId = 'aays-113-dem-dtm-deep-discovery-20260519'
$BridgeRoot = 'C:\AAYS_GITHUB_BRIDGE_CLEAN2'
$ResultDir = Join-Path $BridgeRoot 'ai-results'
$ProgressDir = Join-Path $BridgeRoot 'ai-progress'
New-Item -ItemType Directory -Force -Path $ResultDir,$ProgressDir | Out-Null
$Report = Join-Path $ResultDir ($TaskId + '.report.md')
$Json = Join-Path $ResultDir ($TaskId + '.result.json')
$Progress = Join-Path $ProgressDir ($TaskId + '.progress.md')
function W($p,$m){ Add-Content -LiteralPath $p -Encoding UTF8 -Value $m }
Set-Content -LiteralPath $Report -Encoding UTF8 -Value '# AAYS 113 DEM/DTM Deep Discovery'
Set-Content -LiteralPath $Progress -Encoding UTF8 -Value '# AAYS 113 Progress'
W $Report "start_utc=$((Get-Date).ToUniversalTime().ToString('o'))"
W $Report 'scope=read_only_dem_dtm_discovery_after_aays112_blocker'
W $Report 'db_write=false'
W $Report 'fake_elevation_values=false'
$roots = @(
 'E:\AAYS_DATA',
 'E:\AAYS_DATA\topography',
 'E:\AAYS_DATA\elevation',
 'E:\AAYS_DATA\dem',
 'E:\AAYS_DATA\dtm',
 'C:\Users\cagda\Documents\GitHub\AAYS',
 'C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence'
) | Select-Object -Unique
$patterns = @('*.tif','*.tiff','*.vrt','*.asc','*.img','*.dem','*.dtm','*.bil','*.flt','*.hdr','*.gpkg','*dem*','*dtm*','*elevation*','*terrain*','*topo*','*lidar*')
$found = New-Object System.Collections.Generic.List[object]
$warnings = New-Object System.Collections.Generic.List[string]
for($cycle=1; $cycle -le 8; $cycle++){
  $utc = (Get-Date).ToUniversalTime().ToString('o')
  W $Progress "cycle=$cycle | utc=$utc | status=running"
  W $Report ""
  W $Report "## cycle_$cycle"
  foreach($root in $roots){
    if(-not (Test-Path -LiteralPath $root -PathType Container)){
      W $Report "root=$root | verdict=missing"
      continue
    }
    W $Report "root=$root | verdict=present"
    foreach($pat in $patterns){
      try{
        $items = Get-ChildItem -LiteralPath $root -Recurse -File -Filter $pat -ErrorAction SilentlyContinue | Select-Object -First 40
        foreach($i in $items){
          $ext = $i.Extension.ToLowerInvariant()
          $isLikelyRaster = @('.tif','.tiff','.vrt','.asc','.img','.dem','.dtm','.bil','.flt') -contains $ext
          $sha = ''
          if($i.Length -lt 2147483648){ try { $sha = (Get-FileHash -LiteralPath $i.FullName -Algorithm SHA256).Hash.ToLower() } catch { $sha = 'hash_error' } } else { $sha = 'skipped_large_file' }
          $row = [ordered]@{ path=$i.FullName; name=$i.Name; ext=$ext; size_bytes=$i.Length; timestamp_utc=$i.LastWriteTimeUtc.ToString('o'); pattern=$pat; likely_raster=$isLikelyRaster; sha256=$sha }
          $found.Add([pscustomobject]$row) | Out-Null
          W $Report "candidate=$($i.FullName) | ext=$ext | size_bytes=$($i.Length) | timestamp_utc=$($i.LastWriteTimeUtc.ToString('o')) | likely_raster=$isLikelyRaster | sha256=$sha"
        }
      } catch {
        $warnings.Add("scan_error root=$root pattern=$pat message=$($_.Exception.Message)") | Out-Null
        W $Report "scan_error root=$root | pattern=$pat | message=$($_.Exception.Message)"
      }
    }
  }
  W $Progress "cycle=$cycle | utc=$((Get-Date).ToUniversalTime().ToString('o')) | candidates_seen=$($found.Count)"
  if($cycle -lt 8){ Start-Sleep -Seconds 240 }
}
$unique = $found | Sort-Object path -Unique
$likely = @($unique | Where-Object { $_.likely_raster -eq $true })
$status = if($likely.Count -gt 0){ 'completed_candidates_found' } else { 'completed_with_blockers' }
$result = [ordered]@{
 task_id=$TaskId
 status=$status
 generated_at_utc=(Get-Date).ToUniversalTime().ToString('o')
 roots_checked=$roots
 patterns=$patterns
 candidate_count=@($unique).Count
 likely_raster_count=$likely.Count
 candidates=@($unique | Select-Object -First 200)
 warnings=@($warnings)
 blockers= if($likely.Count -eq 0){ @('No likely DEM/DTM raster found in scanned roots') } else { @() }
 next_task= if($likely.Count -gt 0){ 'Run AAYS-112 again using selected DEM/DTM candidate' } else { 'Provide or download official DEM/DTM raster source before elevation sampling' }
}
$result | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $Json -Encoding UTF8
W $Report ""
W $Report "STATUS=$status"
W $Report "candidate_count=$(@($unique).Count)"
W $Report "likely_raster_count=$($likely.Count)"
W $Report "json=$Json"
W $Report "end_utc=$((Get-Date).ToUniversalTime().ToString('o'))"
W $Progress "done_utc=$((Get-Date).ToUniversalTime().ToString('o')) | status=$status | candidate_count=$(@($unique).Count) | likely_raster_count=$($likely.Count)"
Write-Host "AAYS_113_DONE status=$status candidate_count=$(@($unique).Count) likely_raster_count=$($likely.Count)"
exit 0
