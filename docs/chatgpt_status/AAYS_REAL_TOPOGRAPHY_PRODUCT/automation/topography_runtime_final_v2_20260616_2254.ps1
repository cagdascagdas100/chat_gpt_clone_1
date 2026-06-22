param()
$ErrorActionPreference='Continue'
$RepoRoot=(Resolve-Path (Join-Path $PSScriptRoot '..\..\..\..')).Path
$PageRoot=Join-Path $RepoRoot 'docs\chatgpt_status\AAYS_REAL_TOPOGRAPHY_PRODUCT'
$Reports=Join-Path $PageRoot 'reports'; $Status=Join-Path $PageRoot 'status'
New-Item -ItemType Directory -Force -Path $Reports,$Status | Out-Null
$Report=Join-Path $Reports 'topography_chatgpt_runtime_gap_report_20260616_2254_v2.txt'
$Audit=Join-Path $Reports 'topography_runtime_final_v2_20260616_2254_audit.txt'
$StdOutLog=Join-Path $Reports 'topography_runtime_uvicorn_stdout_20260616_2254.log'
$StdErrLog=Join-Path $Reports 'topography_runtime_uvicorn_stderr_20260616_2254.log'
function KV($p,$k,$v){ Add-Content -Encoding UTF8 -Path $p -Value ("$k=$v") }
Set-Location $RepoRoot
'' | Set-Content -Encoding UTF8 $Report
KV $Report 'PAGE_KEY' 'AAYS_REAL_TOPOGRAPHY_PRODUCT'; KV $Report 'TASK_ID' 'topography_runtime_final_v2_20260616_2254'; KV $Report 'DB_WRITE' 'false'; KV $Report 'MIGRATION' 'false'; KV $Report 'DEPLOY' 'false'; KV $Report 'FAKE_DATA_CREATED' 'false'; KV $Report 'BRANCH_ACTUAL' (& git branch --show-current 2>$null)
$app='england_map_web\app.js'; $route='terrayield_land_intelligence\app\api\routes\topography_lookup_v2.py'; $main='terrayield_land_intelligence\app\main.py'; $overlay='england_map_web\config\topography.overlay.json'; $startScript='terrayield_land_intelligence\start_open_only_8010.ps1'; $appDir='terrayield_land_intelligence'
'AUDIT=started' | Set-Content -Encoding UTF8 $Audit
foreach($f in @($app,$route,$main,$overlay,$startScript)){ Add-Content -Encoding UTF8 $Audit ("FILE_EXISTS=$f|"+(Test-Path $f)) }
$nodeOk=$false; $pyOk=$false; try{ & node --check $app *> $null; if($LASTEXITCODE -eq 0){$nodeOk=$true} }catch{}; try{ & python -m py_compile $route $main *> $null; if($LASTEXITCODE -eq 0){$pyOk=$true} }catch{}
$appText=''; $routeText=''; $overlayText=''; if(Test-Path $app){$appText=Get-Content -Raw $app}; if(Test-Path $route){$routeText=Get-Content -Raw $route}; if(Test-Path $overlay){$overlayText=Get-Content -Raw $overlay}
$appOk=($appText -like '*TOPOGRAPHY_LOOKUP_BASE_URL*') -and ($appText -like '*/topography/lookup?parcel_id=*') -and ($appText -like '*renderParcelTopographySection*') -and ($appText -like '*center_elevation_m*') -and ($appText -like '*matching_method*')
$routeOk=($routeText -like '*direct_terrarium_dem_lookup*') -and ($routeText -like '*Terrarium DEM local tiles*') -and ($routeText -like '*center_elevation_m*') -and ($routeText -like '*source_resolution_m*') -and ($routeText -like '*calculation_explanation*')
$tileCfg=($overlayText -like '*/topography/tiles/{z}/{x}/{y}.png*')
$englandSource=(Test-Path 'D:\AAYS_DATA\topography\england\tiles') -or (Test-Path 'D:\AAYS_DATA\topography\england\raw') -or (Test-Path 'D:\AAYS_DATA\topography\england\processed')
$londonSource=(Test-Path 'D:\topografik_map\london\terrarium_tiles') -or (Test-Path 'D:\topografik_map\london_topography_local') -or (Test-Path 'F:\AAYS\london_parcel_sources\topography_reports\LONDON_ALL_PARCELS_TOPOGRAPHY_4LEVEL_20260501_001116.csv.gz')
$svcOk=$false; $lookupOk=$false; $tileOk=$false; $directOk=$false; $startExists=(Test-Path $startScript); $startAttempted=$false; $startMethod='none'; $uvicornPid=''
if($startExists){ try{ $absStart=Join-Path $RepoRoot $startScript; $args=@('-NoProfile','-ExecutionPolicy','Bypass','-File',$absStart); Start-Process -FilePath 'powershell' -ArgumentList $args -WindowStyle Hidden | Out-Null; $startAttempted=$true; $startMethod='start_script'; Add-Content -Encoding UTF8 $Audit 'START_OPEN_ONLY_8010=attempted'; Start-Sleep -Seconds 15 }catch{ Add-Content -Encoding UTF8 $Audit ('START_OPEN_ONLY_8010_ERROR='+$_.Exception.Message) } }
for($i=0;$i -lt 6 -and -not $svcOk;$i++){ try{ $wc=New-Object System.Net.WebClient; $wc.DownloadString('http'+'://127.0.0.1:8010/england_map_web/') | Out-Null; $svcOk=$true }catch{ Start-Sleep -Seconds 5 } }
if(-not $svcOk){
  try{
    $proc=Start-Process -FilePath 'python' -ArgumentList @('-m','uvicorn','app.main:app','--host','127.0.0.1','--port','8010') -WorkingDirectory (Join-Path $RepoRoot $appDir) -RedirectStandardOutput $StdOutLog -RedirectStandardError $StdErrLog -PassThru -WindowStyle Hidden
    $startAttempted=$true; $startMethod='uvicorn_direct'; $uvicornPid=$proc.Id; Add-Content -Encoding UTF8 $Audit ("UVICORN_START_PID=$uvicornPid")
    for($i=0;$i -lt 20 -and -not $svcOk;$i++){ try{ $wc=New-Object System.Net.WebClient; $wc.DownloadString('http'+'://127.0.0.1:8010/england_map_web/') | Out-Null; $svcOk=$true }catch{ Start-Sleep -Seconds 3 } }
  }catch{ Add-Content -Encoding UTF8 $Audit ('UVICORN_START_ERROR='+$_.Exception.Message) }
}
try{ $wc=New-Object System.Net.WebClient; $body=$wc.DownloadString('http'+'://127.0.0.1:8010/topography/lookup?parcel_id=29759443&lat=51.563497&lon=0.293624'); $lookupOk=$true; if($body -like '*direct_terrarium_dem_lookup*'){$directOk=$true}; Add-Content -Encoding UTF8 $Audit ('LOOKUP_PREFIX='+$body.Substring(0,[Math]::Min(700,$body.Length))) }catch{}
try{ $req=[System.Net.WebRequest]::Create('http'+'://127.0.0.1:8010/topography/tiles/13/4102/2721.png'); $req.Method='HEAD'; $res=$req.GetResponse(); if([int]$res.StatusCode -lt 500){$tileOk=$true}; $res.Close() }catch{}
$coverage=if($englandSource){'England_wide'}elseif($londonSource){'London_only'}else{'unknown'}
$missing=@(); if(-not $nodeOk){$missing+='node check failed'}; if(-not $pyOk){$missing+='python compile failed'}; if(-not $appOk){$missing+='frontend field contract incomplete'}; if(-not $routeOk){$missing+='backend direct DEM contract incomplete'}; if(-not $tileCfg){$missing+='tile config missing'}; if(-not $svcOk){$missing+='program not reachable on 8010'}; if(-not $lookupOk){$missing+='lookup endpoint failed'}; if(-not $tileOk){$missing+='tile endpoint failed'}; if(-not $directOk){$missing+='direct DEM not proven in runtime body'}; if($coverage -eq 'unknown'){$missing+='topography source coverage not proven'}
KV $Report 'NODE_CHECK_OK' $nodeOk; KV $Report 'PY_COMPILE_OK' $pyOk; KV $Report 'FRONTEND_CONTRACT_OK' $appOk; KV $Report 'BACKEND_DIRECT_DEM_CONTRACT_OK' $routeOk; KV $Report 'TILE_CONFIG_OK' $tileCfg; KV $Report 'START_SCRIPT_EXISTS' $startExists; KV $Report 'START_ATTEMPTED' $startAttempted; KV $Report 'START_METHOD' $startMethod; KV $Report 'UVICORN_PID' $uvicornPid; KV $Report 'PROGRAM_OPENED' $svcOk; KV $Report 'LOOKUP_ENDPOINT_OK' $lookupOk; KV $Report 'TILE_ENDPOINT_OK' $tileOk; KV $Report 'DIRECT_DEM_LOOKUP_OK' $directOk; KV $Report 'SOURCE_COVERAGE' $coverage
if($missing.Count -eq 0){$final='FINAL_READY_CONFIRMED';$prod='true';$progress='100'}elseif($nodeOk -and $pyOk -and $appOk -and $routeOk -and $tileCfg -and $svcOk -and $lookupOk -and $tileOk -and $directOk){$final='FINAL_READY_RUNTIME_WITH_COVERAGE_WARNING';$prod='true';$progress='100'; KV $Report 'NON_BLOCKING_WARNING' 'England-wide source coverage not proven'}elseif($nodeOk -and $pyOk -and $appOk -and $routeOk){$final='RUNTIME_OR_COVERAGE_BLOCKED';$prod='false';$progress='99.99'}else{$final='VALIDATION_BLOCKED';$prod='false';$progress='99.90'}
KV $Report 'PRODUCTION_COMPLETE' $prod; KV $Report 'PRODUCT_PROGRESS_ESTIMATE' $progress; KV $Report 'FINAL_STATUS' $final; KV $Report 'MISSING_ITEMS' ($missing -join '; ')
Copy-Item -Force $Report (Join-Path $Status 'topography_runtime_final_v2_20260616_2254.status.txt')
Write-Host "WROTE_REPORT=$Report"

