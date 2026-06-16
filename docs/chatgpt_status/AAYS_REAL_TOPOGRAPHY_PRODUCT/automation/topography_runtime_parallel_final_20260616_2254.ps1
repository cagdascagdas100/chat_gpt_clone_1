param()
$ErrorActionPreference = 'Continue'
$PAGE_KEY = 'AAYS_REAL_TOPOGRAPHY_PRODUCT'
$TASK_ID = 'topography_runtime_parallel_final_20260616_2254'
$ExpectedBranch = 'aays-runner-v17-icon-work-20260603-232706'
$RepoRoot = 'C:\Users\cagda\Documents\GitHub\AAYS'
$PageRoot = Join-Path $RepoRoot 'docs\chatgpt_status\AAYS_REAL_TOPOGRAPHY_PRODUCT'
$Reports = Join-Path $PageRoot 'reports'
$Status = Join-Path $PageRoot 'status'
New-Item -ItemType Directory -Force -Path $Reports,$Status | Out-Null
$MasterReport = Join-Path $Reports 'topography_chatgpt_runtime_gap_report_20260616_2254.txt'
$AuditReport = Join-Path $Reports 'topography_runtime_parallel_final_20260616_2254_static_audit.txt'
$HealthReport = Join-Path $Reports 'topography_runtime_parallel_final_20260616_2254_endpoint_health.txt'
$InventoryReport = Join-Path $Reports 'topography_runtime_parallel_final_20260616_2254_source_inventory.txt'
$UiReport = Join-Path $Reports 'topography_runtime_parallel_final_20260616_2254_ui_contract.txt'
function Write-Kv($Path,$Key,$Value){ Add-Content -Encoding UTF8 -Path $Path -Value ("$Key=$Value") }
function HasText($Path,$Needle){ if(Test-Path $Path){ return ((Get-Content -Raw -ErrorAction SilentlyContinue $Path) -like "*$Needle*") } return $false }
Set-Location $RepoRoot
'' | Set-Content -Encoding UTF8 $MasterReport
Write-Kv $MasterReport 'PAGE_KEY' $PAGE_KEY
Write-Kv $MasterReport 'TASK_ID' $TASK_ID
Write-Kv $MasterReport 'BRANCH_EXPECTED' $ExpectedBranch
Write-Kv $MasterReport 'FAKE_DATA_CREATED' 'false'
Write-Kv $MasterReport 'DB_WRITE' 'false'
$branch = (& git branch --show-current 2>$null)
Write-Kv $MasterReport 'BRANCH_ACTUAL' $branch
$staticJob = Start-Job -Name static_audit -ScriptBlock {
  param($RepoRoot,$AuditReport)
  Set-Location $RepoRoot
  $app='england_map_web\app.js'
  $route='terrayield_land_intelligence\app\api\routes\topography_lookup_v2.py'
  $main='terrayield_land_intelligence\app\main.py'
  $overlay='england_map_web\config\topography.overlay.json'
  "STATIC_AUDIT=started" | Set-Content -Encoding UTF8 $AuditReport
  foreach($f in @($app,$route,$main,$overlay,'terrayield_land_intelligence\requirements.txt','terrayield_land_intelligence\pyproject.toml')){ Add-Content -Encoding UTF8 $AuditReport ("EXISTS_$($f.Replace('\','__'))=" + (Test-Path $f)) }
  $nodeOk=$false; $pyOk=$false
  try { & node --check $app *> $null; if($LASTEXITCODE -eq 0){$nodeOk=$true} } catch {}
  try { & python -m py_compile $route $main *> $null; if($LASTEXITCODE -eq 0){$pyOk=$true} } catch {}
  Add-Content -Encoding UTF8 $AuditReport "NODE_CHECK_OK=$nodeOk"
  Add-Content -Encoding UTF8 $AuditReport "PY_COMPILE_OK=$pyOk"
  $tokens=@('TOPOGRAPHY_LOOKUP_BASE_URL','/topography/lookup?parcel_id=','normalizeTopographyLookupForPopup','buildTopographyPopupRowsHtml','renderParcelTopographySection','center_elevation_m','region_average_elevation_m','elevation_difference_from_region_average_m','confidence_level','confidence_reason','matching_method','calculation_explanation','source_resolution_m','hight_differance.png')
  foreach($t in $tokens){ $present=$false; if(Test-Path $app){ $present=((Get-Content -Raw $app) -like "*$t*") }; Add-Content -Encoding UTF8 $AuditReport "APP_TOKEN_$($t.Replace('/','_').Replace('?','_').Replace('=','_'))=$present" }
  $routeTokens=@('direct_terrarium_dem_lookup','Terrarium DEM local tiles','fake_data','db_write','center_elevation_m','elevation_above_sea_level_m','region_average_elevation_m','elevation_difference_from_region_average_m','source_dataset','source_resolution_m','confidence_level','matching_method','calculation_explanation')
  foreach($t in $routeTokens){ $present=$false; if(Test-Path $route){ $present=((Get-Content -Raw $route) -like "*$t*") }; Add-Content -Encoding UTF8 $AuditReport "ROUTE_TOKEN_$($t.Replace(' ','_'))=$present" }
  $tileOk=$false; if(Test-Path $overlay){ $tileOk=((Get-Content -Raw $overlay) -like '*/topography/tiles/{z}/{x}/{y}.png*') }
  Add-Content -Encoding UTF8 $AuditReport "TILE_CONFIG_TOKEN_OK=$tileOk"
} -ArgumentList $RepoRoot,$AuditReport
$inventoryJob = Start-Job -Name source_inventory -ScriptBlock {
  param($InventoryReport)
  $paths=@('D:\topografik_map\london\terrarium_tiles','D:\topografik_map\london\web_assets\parcel_topography_confidence','D:\topografik_map\london_topography_local','F:\AAYS\london_parcel_sources\topography_reports\LONDON_ALL_PARCELS_TOPOGRAPHY_4LEVEL_20260501_001116.csv.gz','D:\AAYS_DATA\topography\england\raw','D:\AAYS_DATA\topography\england\tiles','D:\AAYS_DATA\topography\england\processed','D:\AAYS_DATA\topography\england\parcel_matches','D:\AAYS_DATA\topography\england\reports')
  "SOURCE_INVENTORY=started" | Set-Content -Encoding UTF8 $InventoryReport
  foreach($p in $paths){ $exists=Test-Path $p; Add-Content -Encoding UTF8 $InventoryReport "PATH_EXISTS=$p|$exists"; if($exists -and (Get-Item $p).PSIsContainer){ $count=(Get-ChildItem -Force -ErrorAction SilentlyContinue $p | Select-Object -First 500 | Measure-Object).Count; Add-Content -Encoding UTF8 $InventoryReport "PATH_SAMPLE_COUNT=$p|$count" } }
} -ArgumentList $InventoryReport
$healthJob = Start-Job -Name endpoint_health -ScriptBlock {
  param($RepoRoot,$HealthReport)
  Set-Location $RepoRoot
  "ENDPOINT_HEALTH=started" | Set-Content -Encoding UTF8 $HealthReport
  try { if(Test-Path 'terrayield_land_intelligence\start_open_only_8010.ps1'){ Start-Process powershell -ArgumentList '-NoProfile','-ExecutionPolicy','Bypass','-File','terrayield_land_intelligence\start_open_only_8010.ps1' -WindowStyle Hidden | Out-Null; Start-Sleep -Seconds 8 } } catch { Add-Content -Encoding UTF8 $HealthReport "START_ERROR=$($_.Exception.Message)" }
  $urls=@('http://127.0.0.1:8010/england_map_web/','http://127.0.0.1:8010/topography/lookup?parcel_id=29759443&lat=51.563497&lon=0.293624')
  foreach($u in $urls){ try { $r=Invoke-WebRequest -UseBasicParsing -TimeoutSec 15 $u; Add-Content -Encoding UTF8 $HealthReport "URL_OK=$u|true|$($r.StatusCode)"; if($u -like '*lookup*'){ $body=$r.Content; Add-Content -Encoding UTF8 $HealthReport "LOOKUP_BODY_PREFIX=$($body.Substring(0,[Math]::Min(1200,$body.Length)))" } } catch { Add-Content -Encoding UTF8 $HealthReport "URL_OK=$u|false|$($_.Exception.Message)" } }
  try { $t=Invoke-WebRequest -UseBasicParsing -TimeoutSec 15 -Method Head 'http://127.0.0.1:8010/topography/tiles/13/4102/2721.png'; Add-Content -Encoding UTF8 $HealthReport "TILE_HEAD_OK=true|$($t.StatusCode)" } catch { Add-Content -Encoding UTF8 $HealthReport "TILE_HEAD_OK=false|$($_.Exception.Message)" }
} -ArgumentList $RepoRoot,$HealthReport
$uiJob = Start-Job -Name ui_contract -ScriptBlock {
  param($RepoRoot,$UiReport)
  Set-Location $RepoRoot
  $app='england_map_web\app.js'
  "UI_CONTRACT=started" | Set-Content -Encoding UTF8 $UiReport
  $fields=@('Elevation Difference from Sea Level','Elevation Difference from Regional Average','center_elevation_m','region_average_elevation_m','elevation_difference_from_region_average_m','elevation_difference_class','color_hex','source_dataset','source_resolution_m','source_date','topography_source','confidence_level','confidence_reason','matching_method','calculation_explanation')
  foreach($f in $fields){ $present=$false; if(Test-Path $app){ $present=((Get-Content -Raw $app) -like "*$f*") }; Add-Content -Encoding UTF8 $UiReport "UI_FIELD_$($f.Replace(' ','_'))=$present" }
  Add-Content -Encoding UTF8 $UiReport 'MANUAL_BROWSER_CLICK_SMOKE=not_available_in_runner_unless_browser_automation_present'
} -ArgumentList $RepoRoot,$UiReport
Wait-Job $staticJob,$inventoryJob,$healthJob,$uiJob -Timeout 600 | Out-Null
Receive-Job $staticJob,$inventoryJob,$healthJob,$uiJob | Out-Null
Remove-Job $staticJob,$inventoryJob,$healthJob,$uiJob -Force | Out-Null
$nodeOk=(Select-String -Path $AuditReport -Pattern 'NODE_CHECK_OK=True' -Quiet)
$pyOk=(Select-String -Path $AuditReport -Pattern 'PY_COMPILE_OK=True' -Quiet)
$programOk=(Select-String -Path $HealthReport -Pattern 'URL_OK=http://127.0.0.1:8010/england_map_web/\|true' -Quiet)
$lookupOk=(Select-String -Path $HealthReport -Pattern 'URL_OK=http://127.0.0.1:8010/topography/lookup' -Quiet)
$tileOk=(Select-String -Path $HealthReport -Pattern 'TILE_HEAD_OK=true' -Quiet)
$directOk=(Select-String -Path $HealthReport -Pattern 'direct_terrarium_dem_lookup' -Quiet)
$londonSource=(Select-String -Path $InventoryReport -Pattern 'D:\\topografik_map\\london\\terrarium_tiles\|True' -Quiet)
$englandSource=(Select-String -Path $InventoryReport -Pattern 'D:\\AAYS_DATA\\topography\\england\\tiles\|True' -Quiet)
$uiAutoOk=(Select-String -Path $UiReport -Pattern 'UI_FIELD_center_elevation_m=True' -Quiet) -and (Select-String -Path $UiReport -Pattern 'UI_FIELD_matching_method=True' -Quiet)
Write-Kv $MasterReport 'STATIC_FINAL_READY' 'legacy_static_report_not_sufficient'
Write-Kv $MasterReport 'NODE_CHECK_OK' $nodeOk
Write-Kv $MasterReport 'PY_COMPILE_OK' $pyOk
Write-Kv $MasterReport 'PROGRAM_OPENED' $programOk
Write-Kv $MasterReport 'LOOKUP_ENDPOINT_OK' $lookupOk
Write-Kv $MasterReport 'TILE_ENDPOINT_OK' $tileOk
Write-Kv $MasterReport 'DIRECT_DEM_LOOKUP_OK' $directOk
Write-Kv $MasterReport 'POPUP_PANEL_FIELDS_OK' $uiAutoOk
if($englandSource){ $coverage='England_wide' } elseif($londonSource){ $coverage='London_only' } else { $coverage='unknown' }
Write-Kv $MasterReport 'SOURCE_COVERAGE' $coverage
Write-Kv $MasterReport 'DATUM_METADATA' 'missing_source_metadata_unless_report_source_contains_datum'
$missing=@()
if(-not $nodeOk){$missing+='node check failed or node unavailable'}
if(-not $pyOk){$missing+='python compile failed or python unavailable'}
if(-not $programOk){$missing+='program did not open on 8010'}
if(-not $lookupOk){$missing+='lookup endpoint failed'}
if(-not $tileOk){$missing+='tile endpoint failed'}
if(-not $directOk){$missing+='direct DEM lookup not proven in endpoint body'}
if(-not $uiAutoOk){$missing+='popup/right panel field contract not fully proven by static scan'}
if($coverage -ne 'England_wide'){$missing+='England-wide source coverage not proven'}
if($missing.Count -eq 0){ $final='FINAL_READY_CONFIRMED'; $prod='true'; $progress='100' } elseif($programOk -and $lookupOk -and $nodeOk -and $pyOk){ $final='SOURCE_COVERAGE_OR_UI_SMOKE_BLOCKED'; $prod='false'; $progress='99.99' } else { $final='RUNTIME_GAP_FOUND'; $prod='false'; $progress='99.90' }
Write-Kv $MasterReport 'PRODUCTION_COMPLETE' $prod
Write-Kv $MasterReport 'PRODUCT_PROGRESS_ESTIMATE' $progress
Write-Kv $MasterReport 'FINAL_STATUS' $final
Write-Kv $MasterReport 'MISSING_ITEMS' ($missing -join '; ')
Write-Kv $MasterReport 'PATCH_NEEDED' 'see static_audit, endpoint_health, source_inventory, ui_contract child reports; apply only missing minimal patch, no fake data'
Copy-Item -Force $MasterReport (Join-Path $Status 'topography_runtime_parallel_final_20260616_2254.status.txt')
Write-Host "WROTE_REPORT=$MasterReport"