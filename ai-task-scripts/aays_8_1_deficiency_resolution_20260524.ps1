$ErrorActionPreference='Continue'
$TaskId='aays-8-1-deficiency-resolution-20260524'
$Bridge='C:\AAYS_GITHUB_BRIDGE_CLEAN2'
$OutDir=Join-Path $Bridge 'ai-results'
$HbDir=Join-Path $Bridge 'ai-heartbeat'
$DocDir=Join-Path $Bridge 'docs\integration'
$DemDir='E:\AAYS_DATA\elevation\copernicus_dem_glo30'
New-Item -ItemType Directory -Force -Path $OutDir,$HbDir,$DocDir,$DemDir | Out-Null
$Result=Join-Path $OutDir 'aays_8_1_deficiency_resolution_20260524.result.json'
$Report=Join-Path $OutDir 'aays_8_1_deficiency_resolution_20260524.report.md'
$Status=Join-Path $DocDir 'AAYS_8_1_DEFICIENCY_RESOLUTION_STATUS_20260524.md'
$Hb=Join-Path $HbDir 'portable-runner.md'
function Write-Hb($status,$msg){ @('# AAYS Portable Task Runner Fixed','','Time: '+(Get-Date -Format s),'Status: '+$status,'TaskId: '+$TaskId,'Message: '+$msg,'Mode: deficiency-resolution-safe','SafeScriptOnly: enabled','DB_WRITE=false','PRODUCTION_DEPLOY=false','FAKE_DATA=false') | Set-Content -Encoding UTF8 $Hb }
function Add-Report($m){ Add-Content -Encoding UTF8 -Path $Report -Value $m }
Set-Content -Encoding UTF8 -Path $Report -Value '# AAYS 8.1 Deficiency Resolution Report'
Add-Report ('started_at='+(Get-Date -Format s))
Add-Report 'db_write=false'
Add-Report 'production_deploy=false'
Add-Report 'fake_data=false'
Write-Hb 'running' 'check dem files'
$expected=@(
 'Copernicus_DSM_COG_10_N51_00_W001_00_DEM.tif',
 'Copernicus_DSM_COG_10_N52_00_W001_00_DEM.tif'
)
$downloaded=@()
$missing=@()
foreach($f in $expected){
 $p=Join-Path $DemDir $f
 if(Test-Path -LiteralPath $p){ $downloaded += $p; Add-Report ('exists='+$p); continue }
 $missing += $p
}
$attempted=@()
foreach($p in $missing){
 $file=Split-Path $p -Leaf
 $base=[IO.Path]::GetFileNameWithoutExtension($file)
 $url='https://copernicus-dem-30m.s3.amazonaws.com/'+$base+'/'+$file
 $attempted += $url
 Write-Hb 'running' ('download '+$file)
 try{
   Invoke-WebRequest -Uri $url -OutFile $p -TimeoutSec 900 -UseBasicParsing
   if((Test-Path -LiteralPath $p) -and ((Get-Item -LiteralPath $p).Length -gt 1000000)){
     $downloaded += $p
     Add-Report ('downloaded='+$p)
   } else {
     Remove-Item -LiteralPath $p -Force -ErrorAction SilentlyContinue
     Add-Report ('download_failed_small_or_missing='+$p)
   }
 } catch {
   Add-Report ('download_failed='+$file+' error='+$_.Exception.Message)
 }
}
$gitConflictNote='local git pull may fail if ai-tasks/current-task.json has uncommitted local changes; do not use destructive reset automatically; use queue pending instead.'
Add-Report ('git_conflict_note='+$gitConflictNote)
$completed = ($downloaded.Count -ge 2)
$statusValue = if($completed){'finished_dem_available'}else{'finished_with_dem_warning'}
$overall = if($completed){100}else{99}
$obj=[ordered]@{
 task_id=$TaskId
 status=$statusValue
 overall_progress=$overall
 expected_dem_count=$expected.Count
 available_dem_count=$downloaded.Count
 available_dem_files=$downloaded
 missing_dem_files=@($expected | ForEach-Object { Join-Path $DemDir $_ } | Where-Object { -not (Test-Path -LiteralPath $_) })
 attempted_urls=$attempted
 db_write=$false
 production_deploy=$false
 fake_data=$false
 git_conflict_note=$gitConflictNote
 completed_at=(Get-Date -Format s)
}
$obj|ConvertTo-Json -Depth 6|Set-Content -Encoding UTF8 $Result
@('# AAYS 8.1 Deficiency Resolution Status','status='+$statusValue,'overall_progress='+$overall,'available_dem_count='+$downloaded.Count,'db_write=false','production_deploy=false','fake_data=false','updated_at='+(Get-Date -Format s)) | Set-Content -Encoding UTF8 $Status
Write-Hb 'finished' ('status='+$statusValue+' dem='+$downloaded.Count)
exit 0
