$ErrorActionPreference = "Continue"
$Project = "C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence"
$Start = Get-Date
$Run = Get-Date -Format "yyyyMMdd_HHmmss"
$ReportDir = Join-Path $Project ".aays_next_fix\recovery_016_api_exit127_$Run"
$BackupDir = Join-Path $ReportDir "backup"
$SummaryFile = Join-Path $ReportDir "summary.md"
$DetailFile = Join-Path $ReportDir "detail.txt"
New-Item -ItemType Directory -Force -Path $ReportDir,$BackupDir | Out-Null
Set-Location $Project
function Log([string]$Text) { $e=[int]((Get-Date)-$Start).TotalSeconds; $line="[$e s] $Text"; Write-Output $line; Add-Content -Encoding UTF8 -Path $DetailFile -Value $line }
function Backup([string]$Path) { if(Test-Path $Path){ Copy-Item -Force $Path (Join-Path $BackupDir ($Path -replace '[\\/:*?"<>|]','_')); Log "BACKUP $Path" } }
function RunCmd([string]$Label,[scriptblock]$Block){ Log "--- $Label ---"; try{ & $Block 2>&1 | Out-String | ForEach-Object { Add-Content -Encoding UTF8 -Path $DetailFile -Value $_; Write-Output $_ }; Log "$Label EXIT=$LASTEXITCODE" } catch { Log "$Label ERROR=$($_.Exception.Message)" } }
function Endpoint([string]$ep){ try{ $sw=[System.Diagnostics.Stopwatch]::StartNew(); $r=Invoke-WebRequest -Uri ("http://localhost:8010"+$ep) -UseBasicParsing -TimeoutSec 75; $sw.Stop(); $cache=$r.Headers["X-AAYS-Cache"]; $line="OK $ep status=$($r.StatusCode) ms=$($sw.ElapsedMilliseconds) bytes=$($r.Content.Length) cache=$cache"; Log $line; return $line } catch { $line="FAIL $ep error=$($_.Exception.Message)"; Log $line; return $line } }
Log "TASK: TerraYield recovery 016 API exit 127"
Log "PROGRESS: 98%"
Log "PROJECT=$Project"
Log "REPORT_DIR=$ReportDir"
RunCmd "compose config before" { docker compose -f docker-compose.yml -f docker-compose.aays-fast-start.yml config }
Log "--- patch compose shell command if needed ---"
$patches=@()
foreach($file in @('docker-compose.yml','docker-compose.aays-fast-start.yml','docker-compose.override.yml')){
  if(Test-Path $file){
    Backup $file
    $txt=Get-Content -Raw -Encoding UTF8 $file
    $orig=$txt
    $txt=$txt.Replace('bash -lc','sh -lc')
    $txt=$txt.Replace('bash -c','sh -c')
    if($txt -ne $orig){ Set-Content -Encoding UTF8 -Path $file -Value $txt; $patches += "patched $file bash-to-sh"; Log "PATCHED $file bash-to-sh" } else { Log "NO_PATCH_NEEDED $file" }
    Log "--- CONTENT $file ---"
    Get-Content -Path $file -Raw | ForEach-Object { Add-Content -Encoding UTF8 -Path $DetailFile -Value $_ }
  } else { Log "MISSING_COMPOSE_FILE $file" }
}
Log "--- compile focused ---"
$compileOk=$true
foreach($f in @('app\core\ttl_cache.py','app\middleware\map_listings_cache.py','app\main.py','app\api\routes\aays_sales_layers.py','app\api\routes\aays_sales_history_layers.py')){ if(Test-Path $f){ python -m py_compile $f 2>&1 | Out-String | ForEach-Object { Add-Content -Encoding UTF8 -Path $DetailFile -Value $_ }; Log "COMPILE $f EXIT=$LASTEXITCODE"; if($LASTEXITCODE -ne 0){$compileOk=$false} } else { Log "MISSING $f" } }
RunCmd "compose down old api" { docker compose -f docker-compose.yml -f docker-compose.aays-fast-start.yml rm -sf api }
RunCmd "compose up stack after exit127 patch" { docker compose -f docker-compose.yml -f docker-compose.aays-fast-start.yml up -d --remove-orphans }
RunCmd "compose ps after up" { docker compose -f docker-compose.yml -f docker-compose.aays-fast-start.yml ps -a }
$apiReady=$false; $readySeconds=-1; $apiStart=Get-Date
for($i=1;$i -le 120;$i++){ Start-Sleep -Seconds 5; try{ Invoke-WebRequest -Uri 'http://localhost:8010/health' -UseBasicParsing -TimeoutSec 5 | Out-Null; $apiReady=$true; $readySeconds=[int]((Get-Date)-$apiStart).TotalSeconds; Log "API_READY_SECONDS=$readySeconds"; break } catch { if(($i%6)-eq 0){ Log "WAIT_API $i/120"; docker compose -f docker-compose.yml -f docker-compose.aays-fast-start.yml ps -a 2>&1 | Out-String | ForEach-Object { Add-Content -Encoding UTF8 -Path $DetailFile -Value $_ } } } }
$endpointLines=@()
foreach($ep in @('/health','/openapi.json','/map/listings','/map/sales-history/status','/map/sales-history/external-evidence','/map/sales-history/parcels','/map/sales-history/combined','/map/listings')){ $endpointLines += Endpoint $ep }
RunCmd "compose ps final" { docker compose -f docker-compose.yml -f docker-compose.aays-fast-start.yml ps -a }
Log "--- api logs tail ---"
docker logs --tail 300 terrayield_land_api 2>&1 | Select-Object -Last 220 | ForEach-Object { Log ("API_LOG " + $_) }
$elapsed=[int]((Get-Date)-$Start).TotalSeconds
$result=if($compileOk -and $apiReady){'healthy'}elseif(-not $compileOk){'compile_failed'}else{'api_not_ready'}
$summary=@('# TerraYield Recovery 016 API Exit 127 Summary','','## Result',$result,'','## Compile OK',"$compileOk",'','## API Ready',"$apiReady",'','## API Ready Seconds',"$readySeconds",'','## Patches',($patches | Out-String),'','## Endpoint Summary',($endpointLines | Out-String),'','## Progress Estimate','- Application stabilization/speed: ' + ($(if($compileOk -and $apiReady){'97%'}elseif($compileOk){'95%'}else{'94%'})),'- Cross-computer fast-start/runability: ' + ($(if($apiReady){'94%'}else{'91%'})),'- Continue-only automation bridge: 92%','- Overall combined project: ' + ($(if($compileOk -and $apiReady){'95%'}else{'92%'})),'','## Files',"Detail: $DetailFile","Backup: $BackupDir","Elapsed seconds: $elapsed")
Set-Content -Encoding UTF8 -Path $SummaryFile -Value $summary
Write-Output "SUMMARY_FILE=$SummaryFile"
Write-Output "DETAIL_FILE=$DetailFile"
Write-Output "BACKUP_DIR=$BackupDir"
Write-Output "RESULT=$result"
Write-Output "COMPILE_OK=$compileOk"
Write-Output "API_READY=$apiReady"
Write-Output "ELAPSED_SECONDS=$elapsed"
Write-Output "RECOVERY_016_API_EXIT127_DONE"
exit 0
