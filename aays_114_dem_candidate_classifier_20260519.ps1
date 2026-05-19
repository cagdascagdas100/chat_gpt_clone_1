param([string]$Root='C:\AAYS_GITHUB_BRIDGE_CLEAN2',[int]$Minutes=35)
$ErrorActionPreference='Continue'
$start=Get-Date
$end=$start.AddMinutes($Minutes)
$res=Join-Path $Root 'ai-results'
New-Item -ItemType Directory -Force -Path $res | Out-Null
$inCsv=Join-Path $res 'aays-113-dem-broad-inventory-20260519.csv'
$outCsv=Join-Path $res 'aays-114-dem-candidate-classifier-20260519.csv'
$outJson=Join-Path $res 'aays-114-dem-candidate-classifier-20260519.result.json'
$outMd=Join-Path $res 'aays-114-dem-candidate-classifier-20260519.report.md'
$beat=Join-Path $res 'aays-114-dem-candidate-classifier-20260519.heartbeat.txt'
function ScorePath($p){
  $s=0; $x=([string]$p).ToLowerInvariant()
  foreach($k in @('dem','dtm','dsm','lidar','terrain','elevation','slope','contour','height','topograph')){if($x.Contains($k)){$s+=20}}
  foreach($k in @('postgis','proj','geoid','ntv2','osgbtoetrs','pgsql','bundle-pg')){if($x.Contains($k)){$s-=30}}
  if($x.EndsWith('.tif') -or $x.EndsWith('.tiff')){$s+=5}
  return $s
}
$rows=@()
if(Test-Path $inCsv){try{$rows=Import-Csv $inCsv}catch{}}
if($rows.Count -eq 0 -and (Test-Path $Root)){
  $files=Get-ChildItem $Root -Recurse -File -ErrorAction SilentlyContinue | Where-Object {$_.Name -match 'dem|dtm|dsm|elevation|terrain|slope|contour|height|topograph|tif|tiff|asc|vrt|img'} | Select-Object -First 1500 FullName,Name,Length,LastWriteTime
  foreach($f in $files){$rows += [pscustomobject]@{path=$f.FullName;name=$f.Name;size_mb=[math]::Round($f.Length/1MB,2);modified_utc=$f.LastWriteTime.ToUniversalTime().ToString('s')}}
}
$class=@(); $i=0
foreach($r in $rows){
  $p=if($r.path){$r.path}elseif($r.FullName){$r.FullName}else{[string]$r}
  $score=ScorePath $p
  $kind=if($score -ge 25){'likely_dem_or_dtm'}elseif($score -ge 5){'possible_dem'}elseif($score -lt 0){'likely_projection_grid_not_dem'}else{'unknown_raster'}
  $i++; $class += [pscustomobject]@{rank=$i;path=$p;score=$score;classification=$kind}
}
$class=$class | Sort-Object score -Descending
$class | Export-Csv -Path $outCsv -NoTypeInformation -Encoding UTF8
$phase=0
while((Get-Date) -lt $end){$phase++; Set-Content -Path $beat -Encoding UTF8 -Value "phase=$phase time=$((Get-Date).ToString('s')) candidates=$($class.Count)"; Start-Sleep -Seconds 90}
$top=$class | Select-Object -First 25
$status=if(($class | Where-Object {$_.classification -eq 'likely_dem_or_dtm'}).Count -gt 0){'completed_likely_dem_candidates_found'}else{'completed_no_strong_dem_candidate'}
[ordered]@{status=$status;rows=$class.Count;likely_dem_count=($class|Where-Object{$_.classification -eq 'likely_dem_or_dtm'}).Count;possible_dem_count=($class|Where-Object{$_.classification -eq 'possible_dem'}).Count;projection_grid_count=($class|Where-Object{$_.classification -eq 'likely_projection_grid_not_dem'}).Count;top_candidates=$top;output_csv=$outCsv;started_at=$start.ToString('s');finished_at=(Get-Date).ToString('s');next_step='use likely_dem_or_dtm only for parcel elevation sampling'} | ConvertTo-Json -Depth 8 | Set-Content -Path $outJson -Encoding UTF8
$md=@('# AAYS 114 DEM Candidate Classifier','',"status=$status","rows=$($class.Count)","likely_dem_count=$(($class|Where-Object{$_.classification -eq 'likely_dem_or_dtm'}).Count)","possible_dem_count=$(($class|Where-Object{$_.classification -eq 'possible_dem'}).Count)","projection_grid_count=$(($class|Where-Object{$_.classification -eq 'likely_projection_grid_not_dem'}).Count)",'','## Top candidates')
foreach($t in $top){$md += "- score=$($t.score) class=$($t.classification) path=$($t.path)"}
Set-Content -Path $outMd -Encoding UTF8 -Value ($md -join "`n")
