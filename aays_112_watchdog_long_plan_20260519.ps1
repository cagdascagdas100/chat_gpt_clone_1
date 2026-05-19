param([string]$Root='C:\AAYS_GITHUB_BRIDGE_CLEAN2',[int]$BudgetMinutes=38)
$ErrorActionPreference='Continue'
$started=Get-Date
$deadline=$started.AddMinutes($BudgetMinutes)
$results=Join-Path $Root 'ai-results'
New-Item -ItemType Directory -Path $results -Force | Out-Null
$base=Join-Path $results 'aays-112-watchdog-long-plan-20260519'
$log=$base+'.log.txt'
$json=$base+'.result.json'
$report=$base+'.report.md'
function Log($m){$line=(Get-Date).ToString('s')+' '+$m; Add-Content -Path $log -Encoding UTF8 -Value $line}
Log 'begin long watchdog plan'
$checks=@()
$paths=@($Root,(Join-Path $Root 'ai-results'),(Join-Path $Root 'ai-tasks'),(Join-Path $Root 'scripts'))
foreach($p in $paths){$checks += [pscustomobject]@{path=$p;exists=(Test-Path $p)}}
$files=@()
if(Test-Path $Root){$files=Get-ChildItem $Root -Recurse -File -ErrorAction SilentlyContinue | Where-Object {$_.FullName -notmatch '\\.git\\|\\node_modules\\'} | Select-Object -First 5000 FullName,Name,Extension,Length,LastWriteTime}
$parcel=$files | Where-Object {$_.Name -match 'parcel|parsel|cadastre|kadastro|boundary|geometry|land|plot|lot' -or $_.Extension -match '\.(shp|geojson|gpkg|kml)$'} | Select-Object -First 300
$dem=$files | Where-Object {$_.Name -match 'dem|dtm|dsm|elevation|terrain|topograph|slope|contour|height' -or $_.Extension -match '\.(tif|tiff|asc|vrt|las|laz)$'} | Select-Object -First 300
$phase=0
while((Get-Date) -lt $deadline -and $phase -lt 12){
  $phase++
  Log "phase=$phase files=$($files.Count) parcel=$($parcel.Count) dem=$($dem.Count)"
  Start-Sleep -Seconds 120
}
$blockers=@()
if(-not (Test-Path $Root)){$blockers+='root_not_found'}
if($parcel.Count -eq 0){$blockers+='no_candidate_parcel_file_found'}
if($dem.Count -eq 0){$blockers+='no_candidate_dem_file_found'}
$status=if($blockers.Count -eq 0){'ready_for_evidence_export'}else{'blocked_needs_input_files_or_runner_path'}
[ordered]@{status=$status;blockers=$blockers;checks=$checks;inventory_files=$files.Count;parcel_candidates=$parcel.Count;dem_candidates=$dem.Count;started_at=$started.ToString('s');finished_at=(Get-Date).ToString('s');log=$log} | ConvertTo-Json -Depth 6 | Set-Content -Path $json -Encoding UTF8
Set-Content -Path $report -Encoding UTF8 -Value "# AAYS 112 Watchdog Long Plan`nstatus=$status`nfiles=$($files.Count)`nparcel_candidates=$($parcel.Count)`ndem_candidates=$($dem.Count)`nblockers=$($blockers -join ',')`nlog=$log`n"
Log "finish status=$status"
