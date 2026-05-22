$ErrorActionPreference='Continue'
$Bridge='C:\AAYS_GITHUB_BRIDGE_CLEAN2'
$Folder='E:\AAYS_DATA\elevation\copernicus_dem_glo30'
$Out=Join-Path $Bridge 'ai-results'
$Hb=Join-Path $Bridge 'ai-heartbeat\t118.md'
New-Item -ItemType Directory -Force -Path $Out,(Split-Path $Hb -Parent) | Out-Null
$files=@()
if(Test-Path $Folder){$files=Get-ChildItem -LiteralPath $Folder -Filter *.tif -File -ErrorAction SilentlyContinue | Where-Object {$_.Length -gt 1000000}}
$status=if($files.Count -gt 0){'finished_dem_ready'}else{'failed_no_dem'}
@('# t118 topography dem verify','status='+$status,'dem_count='+$files.Count,'folder='+$Folder,'db_write=false','production_deploy=false','fake_data=false') | Set-Content -Encoding UTF8 $Hb
@{task_id='t118';status=$status;dem_count=$files.Count;files=@($files|ForEach-Object{$_.FullName});db_write=$false;production_deploy=$false;fake_data=$false;next=if($files.Count -gt 0){'topography DEM blocker resolved; run elevation sampling if available'}else{'download DEM first'}} | ConvertTo-Json -Depth 5 | Set-Content -Encoding UTF8 (Join-Path $Out 't118.result.json')
if($files.Count -gt 0){exit 0}else{exit 2}
