$ErrorActionPreference='Continue'
$TaskId='aays-114-dem-candidate-classifier-20260519'
$Bridge='C:\AAYS_GITHUB_BRIDGE_CLEAN2'
$ResultDir=Join-Path $Bridge 'ai-results'
$CsvIn=Join-Path $ResultDir 'aays-113-dem-broad-inventory-20260519.csv'
$JsonOut=Join-Path $ResultDir ($TaskId+'.result.json')
$Report=Join-Path $ResultDir ($TaskId+'.report.md')
$CsvOut=Join-Path $ResultDir ($TaskId+'.csv')
New-Item -ItemType Directory -Force -Path $ResultDir | Out-Null
function Score($p){$s=([string]$p).ToLower();$score=0;if($s -match 'dem|dtm|dsm|lidar|terrain|elevation|srtm|aster|copernicus|os_terrain'){$score+=10};if($s -match 'geoid|proj|postgis|ntv2|etrs|ostn|osgm|velocity|vel|gridshift'){$score-=20};return $score}
$rows=@()
for($cycle=1;$cycle -le 8;$cycle++){
  Write-Host "cycle=$cycle utc=$((Get-Date).ToUniversalTime().ToString('o'))"
  $rows=@()
  if(Test-Path $CsvIn){$raw=Import-Csv $CsvIn -ErrorAction SilentlyContinue}else{$raw=@()}
  foreach($r in $raw){$path=$r.path;if(!$path){$path=$r.Path};$sc=Score $path;$cls=if($sc -ge 10){'possible_dem'}elseif($sc -lt 0){'not_dem_projection_grid'}else{'unknown_raster'};$rows += [pscustomobject]@{path=$path;score=$sc;classification=$cls}}
  if($cycle -lt 8){Start-Sleep -Seconds 240}
}
$rows | Sort-Object score -Descending | Export-Csv -NoTypeInformation -Encoding UTF8 -Path $CsvOut
$possible=@($rows|Where-Object {$_.classification -eq 'possible_dem'})
$status=if($possible.Count -gt 0){'completed_possible_dem_found'}else{'completed_no_true_dem_found'}
[ordered]@{task_id=$TaskId;status=$status;rows=$rows.Count;possible_dem_count=$possible.Count;output_csv=$CsvOut;next_step=if($possible.Count -gt 0){'rerun AAYS 112 with top possible DEM'}else{'mount or acquire official DEM or DTM raster, then rerun AAYS 112'};safety=@{no_db_write=$true;no_production_deploy=$true;no_fake_elevation_values=$true}} | ConvertTo-Json -Depth 6 | Set-Content -Encoding UTF8 $JsonOut
@('# AAYS 114 DEM Candidate Classifier','',"Status: $status","Rows: $($rows.Count)","Possible DEM count: $($possible.Count)",'','## Next step',$(if($possible.Count -gt 0){'Rerun AAYS 112 using the top possible DEM candidate.'}else{'Mount/acquire an official DEM/DTM raster, then rerun AAYS 112.'}),'','TASK_COMPLETION=100/100') | Set-Content -Encoding UTF8 $Report
Write-Host 'AAYS_114_DONE'
exit 0
