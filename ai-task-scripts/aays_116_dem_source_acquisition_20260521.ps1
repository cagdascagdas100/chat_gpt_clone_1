$ErrorActionPreference='Continue'
$TaskId='aays-116-dem-source-acquisition-20260521'
$Root=Split-Path -Parent $PSScriptRoot
$Start=Get-Date
$ResultDir=Join-Path $Root 'ai-results'
$ProgressDir=Join-Path $Root 'ai-progress'
$HbDir=Join-Path $Root 'ai-heartbeat'
$DocDir=Join-Path $Root 'docs/topography'
New-Item -ItemType Directory -Force -Path $ResultDir,$ProgressDir,$HbDir,$DocDir | Out-Null
$Progress=Join-Path $ProgressDir ($TaskId+'.progress.md')
$Result=Join-Path $ResultDir ($TaskId+'.result.json')
$Report=Join-Path $ResultDir ($TaskId+'.report.md')
$Manifest=Join-Path $DocDir 'AAYS_116_DEM_SOURCE_MANIFEST_20260521.json'
function SafeWrite($Path,[string[]]$Lines){
  $ok=$false
  for($try=1;$try -le 5 -and -not $ok;$try++){
    try{
      $dir=Split-Path -Parent $Path
      if($dir -and !(Test-Path -LiteralPath $dir)){New-Item -ItemType Directory -Force -Path $dir|Out-Null}
      $text=($Lines -join [Environment]::NewLine)+[Environment]::NewLine
      [System.IO.File]::WriteAllText($Path,$text,[System.Text.UTF8Encoding]::new($false))
      $ok=$true
    }catch{
      Start-Sleep -Milliseconds (250*$try)
      if($try -eq 5){Write-Host ('safe_write_failed='+$Path+' msg='+$_.Exception.Message)}
    }
  }
}
function SafeAppend($Path,[string]$Line){
  $ok=$false
  for($try=1;$try -le 5 -and -not $ok;$try++){
    try{
      $dir=Split-Path -Parent $Path
      if($dir -and !(Test-Path -LiteralPath $dir)){New-Item -ItemType Directory -Force -Path $dir|Out-Null}
      [System.IO.File]::AppendAllText($Path,$Line+[Environment]::NewLine,[System.Text.UTF8Encoding]::new($false))
      $ok=$true
    }catch{
      Start-Sleep -Milliseconds (250*$try)
      if($try -eq 5){Write-Host ('safe_append_failed='+$Path+' msg='+$_.Exception.Message)}
    }
  }
}
function P($pct,$phase){
  SafeWrite $Progress @('# '+$TaskId,'percent: '+$pct,'phase: '+$phase,'elapsed_minutes: '+[math]::Round(((Get-Date)-$Start).TotalMinutes,2),'db_write=false','production_deploy=false','fake_elevation=false')
  SafeWrite (Join-Path $HbDir 'portable-runner.md') @('# AAYS Portable Task Runner Fixed','Time: '+(Get-Date -Format 'yyyy-MM-dd HH:mm:ss'),'Status: running','TaskId: '+$TaskId,'TaskFile: '+(Join-Path $Root 'ai-tasks/current-task.json'),'Message: '+$phase,'Mode: direct-safe-script','SafeScriptOnly: enabled')
}
function W($m){SafeAppend $Report $m}
SafeWrite $Report @('# AAYS 116 DEM Source Acquisition','mode=read_only_source_manifest_no_fake_elevation_no_db_no_deploy')
$searchRoots=@('E:\AAYS_DATA\elevation','E:\AAYS_DATA\terrain','E:\AAYS_DATA\dem','C:\AAYS_GITHUB_BRIDGE_CLEAN2\data','C:\AAYS_GITHUB_BRIDGE_CLEAN2\external')
$sources=@(
 @{name='EA LIDAR Composite DTM 10m';url='https://www.data.gov.uk/dataset/7f31af0f-bc98-4761-b4b4-147bfb986648/lidar-composite-digital-terrain-model-dtm-10m';kind='official_open_dtm'},
 @{name='EA LIDAR Composite DTM 2m';url='https://www.data.gov.uk/dataset/e529ca2f-b4ce-403e-8cef-ab821061c4f3/lidar-composite-digital-terrain-model-dtm-2m';kind='official_open_dtm'},
 @{name='EA LIDAR Composite DTM 1m';url='https://www.data.gov.uk/dataset/01b3ee39-da3f-47b6-83da-dc98e73a461f/lidar-composite-digital-terrain-model-dtm-1m';kind='official_open_dtm'},
 @{name='OS Terrain 50';url='https://docs.os.uk/os-downloads/height-and-imagery/os-terrain-50/os-terrain-50-overview';kind='official_open_dtm'}
)
$existing=@()
P 5 'scan_existing_dem_paths'
foreach($r in $searchRoots){
 W "scan_root=$r"
 if(Test-Path -LiteralPath $r){
  $files=Get-ChildItem -LiteralPath $r -Recurse -File -ErrorAction SilentlyContinue | Where-Object {$_.Extension -match '^(\.tif|\.tiff|\.asc|\.vrt)$'} | Select-Object -First 200
  foreach($f in $files){$existing += [ordered]@{path=$f.FullName;size_mb=[math]::Round($f.Length/1MB,2);extension=$f.Extension}}
 }
}
P 25 'probe_official_sources'
$probe=@()
foreach($s in $sources){
 try{$resp=Invoke-WebRequest -Uri $s.url -Method Head -TimeoutSec 30 -UseBasicParsing; $probe += [ordered]@{name=$s.name;url=$s.url;status_code=[int]$resp.StatusCode;reachable=$true}; W "reachable=$($s.name)"}
 catch{$probe += [ordered]@{name=$s.name;url=$s.url;reachable=$false;error=$_.Exception.Message}; W "unreachable=$($s.name)"}
}
P 45 'write_manifest'
$manifestObj=[ordered]@{task_id=$TaskId;created_at=(Get-Date).ToUniversalTime().ToString('o');status='source_manifest_created';search_roots=$searchRoots;existing_raster_candidates=$existing;official_sources=$sources;source_probe=$probe;safety=[ordered]@{db_write=$false;production_deploy=$false;fake_elevation=$false};next_step=if($existing.Count -gt 0){'rerun_aays_112_with_discovered_raster'}else{'download_official_dem_to_E_AAYS_DATA_elevation_then_rerun_aays_112'}}
SafeWrite $Manifest @($manifestObj|ConvertTo-Json -Depth 8)
for($i=1;$i -le 8;$i++){P (45+$i*5) ('watch_cycle_'+$i); Start-Sleep -Seconds 180}
P 90 'write_result'
$resultObj=[ordered]@{task_id=$TaskId;status=if($existing.Count -gt 0){'completed_existing_raster_found'}else{'completed_sources_identified_no_local_dem_yet'};elapsed_minutes=[math]::Round(((Get-Date)-$Start).TotalMinutes,2);existing_raster_count=$existing.Count;manifest=$Manifest;official_source_count=$sources.Count;reachable_source_count=(@($probe|Where-Object {$_.reachable})).Count;db_write=$false;production_deploy=$false;fake_elevation=$false;next_command='if raster found rerun AAYS112 else place official DEM in E:\AAYS_DATA\elevation'}
SafeWrite $Result @($resultObj|ConvertTo-Json -Depth 8)
W 'result_written'
P 100 'completed'
SafeWrite (Join-Path $HbDir 'portable-runner.md') @('# AAYS Portable Task Runner Fixed','Time: '+(Get-Date -Format 'yyyy-MM-dd HH:mm:ss'),'Status: finished','TaskId: '+$TaskId,'TaskFile: '+(Join-Path $Root 'ai-tasks/current-task.json'),'Message: exit=0','Mode: direct-safe-script','SafeScriptOnly: enabled')
Write-Host 'AAYS_116_DONE'
exit 0
