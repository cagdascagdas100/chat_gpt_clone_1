$ErrorActionPreference='Continue'
$TaskId='aays-113-dem-broad-inventory-20260519'
$BridgeRoot=Split-Path -Parent $PSScriptRoot
$ResultDir=Join-Path $BridgeRoot 'ai-results'
$HeartbeatDir=Join-Path $BridgeRoot 'ai-heartbeat'
New-Item -ItemType Directory -Force -Path $ResultDir,$HeartbeatDir | Out-Null
$OutJson=Join-Path $ResultDir ($TaskId+'.result.json')
$OutMd=Join-Path $ResultDir ($TaskId+'.report.md')
$OutCsv=Join-Path $ResultDir ($TaskId+'.csv')
$Heartbeat=Join-Path $HeartbeatDir 'portable-runner.md'
$roots=@('E:\AAYS_DATA','E:\','C:\Users\cagda\Documents\GitHub\AAYS')
$patterns=@('*.tif','*.tiff','*.asc','*.vrt','*.img')
@('# AAYS Portable Task Runner Fixed','',('Time: '+(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')),'Status: running',('TaskId: '+$TaskId),('BridgeRoot: '+$BridgeRoot),'Message: DEM broad inventory running','Mode: no-spawn-foreground-loop','SafeScriptOnly: enabled') | Set-Content -Encoding UTF8 $Heartbeat
$rows=@()
foreach($root in $roots){
  if(Test-Path $root){
    foreach($pat in $patterns){
      Get-ChildItem -Path $root -Filter $pat -Recurse -File -ErrorAction SilentlyContinue | Select-Object -First 500 | ForEach-Object {
        $name=$_.FullName.ToLowerInvariant()
        $score=0
        foreach($k in @('dem','dtm','dsm','lidar','terrain','elevation','height','os_terrain','srtm')){ if($name.Contains($k)){ $score++ } }
        $rows += [pscustomobject]@{ path=$_.FullName; name=$_.Name; size_mb=[math]::Round($_.Length/1MB,2); modified_utc=$_.LastWriteTimeUtc.ToString('s')+'Z'; score=$score }
      }
    }
  }
}
$rows=$rows | Sort-Object score,size_mb -Descending
$rows | Export-Csv -NoTypeInformation -Encoding UTF8 $OutCsv
$result=[ordered]@{ task_id=$TaskId; status=($(if($rows.Count -gt 0){'completed_candidates_found'}else{'completed_no_dem_found'})); generated_at_utc=(Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ'); rows=[int]$rows.Count; top_candidates=@($rows | Select-Object -First 50); output_csv=$OutCsv; next_step='If candidates are valid DEM/DTM raster, rerun AAYS 112 elevation exporter.' }
$result | ConvertTo-Json -Depth 6 | Set-Content -Encoding UTF8 $OutJson
@('# AAYS 113 DEM Broad Inventory','',('Status: '+$result.status),('Rows: '+$rows.Count),'','## Top candidates',(($rows | Select-Object -First 30 | ForEach-Object { '- '+$_.path+' size_mb='+$_.size_mb+' score='+$_.score }) -join "`n"),'','PLAN_PROGRESS_PERCENT=100','TASK_COMPLETION=100/100') | Set-Content -Encoding UTF8 $OutMd
@('# AAYS Portable Task Runner Fixed','',('Time: '+(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')),'Status: finished',('TaskId: '+$TaskId),('BridgeRoot: '+$BridgeRoot),'Message: exit=0 dem broad inventory done','Mode: no-spawn-foreground-loop','SafeScriptOnly: enabled') | Set-Content -Encoding UTF8 $Heartbeat
Write-Output ($result | ConvertTo-Json -Depth 6)
exit 0
