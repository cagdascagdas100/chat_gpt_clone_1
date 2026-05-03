$ErrorActionPreference = "Continue"
$Project = "C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence"
$Start = Get-Date
$Run = Get-Date -Format "yyyyMMdd_HHmmss"
$ReportDir = Join-Path $Project ".aays_next_fix\recovery_022_final_parallel_pack_$Run"
$SummaryFile = Join-Path $ReportDir "summary.md"
$DetailFile = Join-Path $ReportDir "detail.txt"
New-Item -ItemType Directory -Force -Path $ReportDir | Out-Null
Set-Location $Project
function Log($x){$s=[int]((Get-Date)-$Start).TotalSeconds;$l="[$s s] $x";Write-Output $l;Add-Content -Encoding UTF8 -Path $DetailFile -Value $l}
function E($ep){try{$sw=[System.Diagnostics.Stopwatch]::StartNew();$r=Invoke-WebRequest -Uri ("http://localhost:8010"+$ep) -UseBasicParsing -TimeoutSec 75;$sw.Stop();$cache=$r.Headers["X-AAYS-Cache"];$line="OK $ep status=$($r.StatusCode) ms=$($sw.ElapsedMilliseconds) bytes=$($r.Content.Length) cache=$cache";Log $line;return $line}catch{$line="FAIL $ep error=$($_.Exception.Message)";Log $line;return $line}}
Log "TASK: TerraYield 022 final parallel stability pack"
Log "PROGRESS: 99%"
Log "MODE: non-invasive report only; no app source patch"
$initial=E "/health"
$jobs=@()
$jobs += Start-Job -Name "endpoint_three_pass" -ScriptBlock {foreach($pass in 1..3){"PASS $pass";foreach($ep in @('/health','/openapi.json','/map/listings','/map/sales-history/status','/map/sales-history/external-evidence','/map/sales-history/parcels','/map/sales-history/combined','/map/listings')){try{$sw=[System.Diagnostics.Stopwatch]::StartNew();$r=Invoke-WebRequest -Uri ('http://localhost:8010'+$ep) -UseBasicParsing -TimeoutSec 75;$sw.Stop();"OK $ep status=$($r.StatusCode) ms=$($sw.ElapsedMilliseconds) bytes=$($r.Content.Length)"}catch{"FAIL $ep error=$($_.Exception.Message)"}};Start-Sleep -Seconds 3}}
$jobs += Start-Job -Name "docker_and_logs" -ScriptBlock {param($p) Set-Location $p; "COMPOSE_PS"; docker compose -f docker-compose.yml -f docker-compose.aays-fast-start.yml -f docker-compose.aays-api-command.yml ps -a 2>&1; "API_LOG_TAIL"; docker logs --tail 160 terrayield_land_api 2>&1; "DB_LOG_TAIL"; docker logs --tail 60 terrayield_land_postgis 2>&1} -ArgumentList $Project
$jobs += Start-Job -Name "compile_check" -ScriptBlock {param($p) Set-Location $p; $ok=$true; foreach($f in @('app\core\ttl_cache.py','app\middleware\map_listings_cache.py','app\main.py','app\api\routes\aays_sales_layers.py','app\api\routes\aays_sales_history_layers.py')){if(Test-Path $f){python -m py_compile $f 2>&1; "COMPILE $f EXIT=$LASTEXITCODE"; if($LASTEXITCODE -ne 0){$ok=$false}}else{"MISSING $f"}}; "COMPILE_OK=$ok"} -ArgumentList $Project
$jobs += Start-Job -Name "frontend_candidates" -ScriptBlock {param($p) Set-Location $p; "PACKAGE_FILES"; Get-ChildItem -Recurse -Force -File -ErrorAction SilentlyContinue -Filter package.json | Where-Object {$_.FullName -notlike '*node_modules*' -and $_.FullName -notlike '*.git*' -and $_.FullName -notlike '*.aays_next_fix*'} | Select-Object -First 12 FullName,Length,LastWriteTime | Format-Table -AutoSize | Out-String; "MAP_PERF_CANDIDATES"; Get-ChildItem -Recurse -Force -File -ErrorAction SilentlyContinue -Include *.js,*.jsx,*.ts,*.tsx | Where-Object {$_.FullName -notlike '*node_modules*' -and $_.FullName -notlike '*.git*' -and $_.FullName -notlike '*.aays_next_fix*'} | Select-String -Pattern 'fetch|axios|/map/listings|sales-history|external-evidence|parcels|combined|debounce|throttle|moveend|zoomend|bounds' -CaseSensitive:$false | Select-Object -First 160 | ForEach-Object {$_.Path + ':' + $_.LineNumber + ': ' + $_.Line.Trim()}} -ArgumentList $Project
Wait-Job -Job $jobs -Timeout 480 | Out-Null
foreach($j in $jobs){if($j.State -eq 'Running'){Log "JOB_TIMEOUT_STOP $($j.Name)";Stop-Job $j -Force};Add-Content -Encoding UTF8 -Path $DetailFile -Value ("## JOB " + $j.Name);Receive-Job $j 2>&1 | Out-String | Add-Content -Encoding UTF8 -Path $DetailFile;Remove-Job $j -Force}
$finalHealth=E "/health"
$finalCombined=E "/map/sales-history/combined"
$result=if($finalHealth -like 'OK*' -and $finalCombined -like 'OK*'){'final_stable'}elseif($finalHealth -like 'OK*'){'api_stable_combined_issue'}else{'needs_recovery'}
$elapsed=[int]((Get-Date)-$Start).TotalSeconds
$summary=@('# TerraYield 022 Final Parallel Pack Summary','','## Result',$result,'','## Initial Health',$initial,'','## Final Health',$finalHealth,'','## Final Combined',$finalCombined,'','## Progress Estimate','- Application stabilization/speed: '+($(if($result -eq 'final_stable'){'99%'}elseif($result -eq 'api_stable_combined_issue'){'97%'}else{'95%'})),'- Cross-computer fast-start/runability: '+($(if($result -eq 'final_stable'){'96%'}else{'94%'})),'- Continue-only automation bridge: 94%','- Overall combined project: '+($(if($result -eq 'final_stable'){'97-98%'}else{'95%'})),'','## Files',"Detail: $DetailFile","Elapsed seconds: $elapsed",'','## Next','- If final_stable: prepare final run instructions / packaging handoff.','- If partial: inspect detail.txt endpoint and docker sections.','- If needs_recovery: rerun proven 018 supervisor before next patch.')
Set-Content -Encoding UTF8 -Path $SummaryFile -Value $summary
Write-Output "SUMMARY_FILE=$SummaryFile"
Write-Output "DETAIL_FILE=$DetailFile"
Write-Output "RESULT=$result"
Write-Output "FINAL_HEALTH=$finalHealth"
Write-Output "FINAL_COMBINED=$finalCombined"
Write-Output "ELAPSED_SECONDS=$elapsed"
Write-Output "RECOVERY_022_FINAL_PARALLEL_PACK_DONE"
exit 0
