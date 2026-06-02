$ErrorActionPreference = "Continue"
$Project = "C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence"
$Start = Get-Date
$Run = Get-Date -Format "yyyyMMdd_HHmmss"
$ReportDir = Join-Path $Project ".aays_next_fix\recovery_012_docker_compile_$Run"
$SummaryFile = Join-Path $ReportDir "summary.md"
$DetailFile = Join-Path $ReportDir "detail.txt"
New-Item -ItemType Directory -Force -Path $ReportDir | Out-Null
Set-Location $Project
function Log([string]$Text) { $elapsed=[int]((Get-Date)-$Start).TotalSeconds; $line="[$elapsed s] $Text"; Write-Output $line; Add-Content -Encoding UTF8 -Path $DetailFile -Value $line }
function T([string]$Path) { try { $sw=[System.Diagnostics.Stopwatch]::StartNew(); $r=Invoke-WebRequest -Uri ("http://localhost:8010"+$Path) -UseBasicParsing -TimeoutSec 75; $sw.Stop(); $cache=$r.Headers["X-AAYS-Cache"]; $line="OK $Path status=$($r.StatusCode) ms=$($sw.ElapsedMilliseconds) bytes=$($r.Content.Length) cache=$cache"; Log $line; return $line } catch { $line="FAIL $Path error=$($_.Exception.Message)"; Log $line; return $line } }
function DockerReady { try { docker version 2>&1 | Out-String | ForEach-Object { Log $_ }; return ($LASTEXITCODE -eq 0) } catch { Log "DOCKER_ERROR=$($_.Exception.Message)"; return $false } }
Log "TASK: TerraYield recovery 012 Docker compile API"
Log "PROGRESS: 97%"
Log "PROJECT=$Project"
Log "REPORT_DIR=$ReportDir"
Log "--- repo root ---"
git rev-parse --show-toplevel 2>&1 | Out-String | ForEach-Object { Log $_ }
Log "--- latest mega 009 detail tail ---"
$d = Get-ChildItem -Path ".aays_next_fix" -Recurse -File -ErrorAction SilentlyContinue -Filter detail.txt | Where-Object { $_.FullName -like "*mega_009*" } | Sort-Object LastWriteTime -Descending | Select-Object -First 1
if ($d) { Log "LATEST_DETAIL=$($d.FullName)"; Get-Content $d.FullName -Tail 200 -ErrorAction SilentlyContinue | ForEach-Object { Log ("MEGA009 " + $_) } } else { Log "NO_MEGA009_DETAIL" }
Log "--- compile focused check ---"
$compileOk=$true
foreach ($f in @("app\core\ttl_cache.py","app\middleware\map_listings_cache.py","app\main.py","app\api\routes\aays_sales_layers.py","app\api\routes\aays_sales_history_layers.py")) { if (Test-Path $f) { python -m py_compile $f 2>&1 | Out-String | ForEach-Object { Log ("COMPILE $f EXIT=$LASTEXITCODE " + $_) }; if ($LASTEXITCODE -ne 0) { $compileOk=$false } } else { Log "MISSING $f" } }
Log "--- docker readiness ---"
$dockerReady = DockerReady
if (-not $dockerReady) { Log "TRY_START_DOCKER_DESKTOP"; foreach ($p in @("C:\Program Files\Docker\Docker\Docker Desktop.exe", "$env:LOCALAPPDATA\Docker\Docker Desktop.exe")) { if (Test-Path $p) { try { Start-Process -FilePath $p; Log "DOCKER_START_ATTEMPT=$p"; break } catch { Log "DOCKER_START_FAIL=$p $($_.Exception.Message)" } } }; for ($i=1; $i -le 24; $i++) { Start-Sleep -Seconds 10; Log "WAIT_DOCKER $i/24"; if (DockerReady) { $dockerReady=$true; break } } }
$apiReady=$false; $readySeconds=-1; $endpointLines=@()
if ($dockerReady) { Log "--- compose api up ---"; docker compose -f docker-compose.yml -f docker-compose.aays-fast-start.yml up -d --no-deps --force-recreate api 2>&1 | Out-String | ForEach-Object { Log $_ }; $rs=Get-Date; for ($i=1; $i -le 90; $i++) { Start-Sleep -Seconds 5; try { Invoke-WebRequest -Uri "http://localhost:8010/health" -UseBasicParsing -TimeoutSec 5 | Out-Null; $apiReady=$true; $readySeconds=[int]((Get-Date)-$rs).TotalSeconds; Log "API_READY_SECONDS=$readySeconds"; break } catch { Log "WAIT_API $i/90" } }; foreach ($ep in @('/health','/openapi.json','/map/listings','/map/sales-history/status','/map/sales-history/external-evidence','/map/sales-history/parcels','/map/sales-history/combined','/map/listings')) { $endpointLines += T $ep }; docker compose -f docker-compose.yml -f docker-compose.aays-fast-start.yml ps 2>&1 | Out-String | ForEach-Object { Log $_ }; docker logs --tail 180 terrayield_land_api 2>&1 | Select-String -Pattern "Only lon/lat|Traceback|Exception|ERROR|timeout|geography|status|SyntaxError|ImportError" -CaseSensitive:$false | Select-Object -Last 100 | ForEach-Object { Log ("API_LOG " + $_.Line) } } else { Log "DOCKER_STILL_NOT_READY" }
$elapsed=[int]((Get-Date)-$Start).TotalSeconds
$result = if ($dockerReady -and $apiReady -and $compileOk) { "healthy" } elseif (-not $dockerReady) { "docker_not_running" } elseif (-not $compileOk) { "compile_failed" } else { "api_not_ready" }
$summary=@("# TerraYield Recovery 012 Summary","","## Result",$result,"","## Compile OK","$compileOk","","## Docker Ready","$dockerReady","","## API Ready","$apiReady","","## API Ready Seconds","$readySeconds","","## Endpoint Summary",($endpointLines | Out-String),"","## Progress Estimate","- Application stabilization/speed: " + ($(if ($apiReady -and $compileOk) { "96%" } else { "94%" })),"- Cross-computer fast-start/runability: " + ($(if ($dockerReady -and $apiReady) { "93%" } else { "90%" })),"- Continue-only automation bridge: 91%","- Overall combined project: " + ($(if ($apiReady -and $compileOk) { "94%" } else { "91-92%" })),"","## Files","Detail: $DetailFile","Elapsed seconds: $elapsed")
Set-Content -Encoding UTF8 -Path $SummaryFile -Value $summary
Write-Output "SUMMARY_FILE=$SummaryFile"
Write-Output "DETAIL_FILE=$DetailFile"
Write-Output "RESULT=$result"
Write-Output "COMPILE_OK=$compileOk"
Write-Output "DOCKER_READY=$dockerReady"
Write-Output "API_READY=$apiReady"
Write-Output "ELAPSED_SECONDS=$elapsed"
Write-Output "RECOVERY_012_DOCKER_COMPILE_DONE"
exit 0
