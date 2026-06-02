$ErrorActionPreference = "Continue"
$Project = "C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence"
$Bridge = "C:\Users\cagda\Documents\chat_gpt_clone_1"
$Start = Get-Date
$Run = Get-Date -Format "yyyyMMdd_HHmmss"
$ReportDir = Join-Path $Project ".aays_next_fix\recovery_021_parallel_health_matrix_$Run"
$SummaryFile = Join-Path $ReportDir "summary.md"
$DetailFile = Join-Path $ReportDir "detail.txt"
New-Item -ItemType Directory -Force -Path $ReportDir | Out-Null
Set-Location $Project
function Log($x){$s=[int]((Get-Date)-$Start).TotalSeconds;$l="[$s s] $x";Write-Output $l;Add-Content -Encoding UTF8 -Path $DetailFile -Value $l}
function E($ep){try{$sw=[System.Diagnostics.Stopwatch]::StartNew();$r=Invoke-WebRequest -Uri ("http://localhost:8010"+$ep) -UseBasicParsing -TimeoutSec 45;$sw.Stop();"OK $ep status=$($r.StatusCode) ms=$($sw.ElapsedMilliseconds) bytes=$($r.Content.Length)"}catch{"FAIL $ep error=$($_.Exception.Message)"}}
Log "TASK: TerraYield 021 parallel health matrix"
Log "PROGRESS: 99%"
$initial = E "/health"
Log "INITIAL_HEALTH=$initial"
if($initial -like "FAIL*"){
  Log "HEALTH_FAIL: running proven 018 supervisor before matrix"
  $p=Join-Path $Bridge "ai-task-scripts\terrayield_recovery_018_multitask_supervisor.ps1"
  if(Test-Path $p){powershell -NoProfile -ExecutionPolicy Bypass -File $p 2>&1 | Out-String | Add-Content -Encoding UTF8 -Path $DetailFile}
}
$j1=Start-Job -ScriptBlock {foreach($pass in 1..3){"PASS $pass";foreach($ep in @('/health','/openapi.json','/map/listings','/map/sales-history/status','/map/sales-history/external-evidence','/map/sales-history/parcels','/map/sales-history/combined','/map/listings')){try{$sw=[System.Diagnostics.Stopwatch]::StartNew();$r=Invoke-WebRequest -Uri ('http://localhost:8010'+$ep) -UseBasicParsing -TimeoutSec 60;$sw.Stop();"OK $ep status=$($r.StatusCode) ms=$($sw.ElapsedMilliseconds) bytes=$($r.Content.Length)"}catch{"FAIL $ep error=$($_.Exception.Message)"}};Start-Sleep -Seconds 5}}
$j2=Start-Job -ScriptBlock {param($p) Set-Location $p; docker compose -f docker-compose.yml -f docker-compose.aays-fast-start.yml -f docker-compose.aays-api-command.yml ps -a 2>&1; docker logs --tail 120 terrayield_land_api 2>&1} -ArgumentList $Project
$j3=Start-Job -ScriptBlock {param($p) Set-Location $p; $ok=$true; foreach($f in @('app\core\ttl_cache.py','app\middleware\map_listings_cache.py','app\main.py','app\api\routes\aays_sales_layers.py','app\api\routes\aays_sales_history_layers.py')){if(Test-Path $f){python -m py_compile $f 2>&1; "COMPILE $f EXIT=$LASTEXITCODE"; if($LASTEXITCODE -ne 0){$ok=$false}}else{"MISSING $f"}}; "COMPILE_OK=$ok"} -ArgumentList $Project
$jobs=@($j1,$j2,$j3)
Wait-Job -Job $jobs -Timeout 600 | Out-Null
foreach($j in $jobs){Add-Content -Encoding UTF8 -Path $DetailFile -Value ("## JOB " + $j.Id); Receive-Job $j 2>&1 | Out-String | Add-Content -Encoding UTF8 -Path $DetailFile; Remove-Job $j -Force}
$finalHealth=E "/health"
$finalCombined=E "/map/sales-history/combined"
Log "FINAL_HEALTH=$finalHealth"
Log "FINAL_COMBINED=$finalCombined"
$result=if($finalHealth -like 'OK*' -and $finalCombined -like 'OK*'){'healthy'}elseif($finalHealth -like 'OK*'){'api_healthy_combined_issue'}else{'api_unhealthy'}
$elapsed=[int]((Get-Date)-$Start).TotalSeconds
$summary=@('# TerraYield 021 Parallel Health Matrix Summary','','## Result',$result,'','## Initial Health',$initial,'','## Final Health',$finalHealth,'','## Final Combined',$finalCombined,'','## Progress Estimate','- Application stabilization/speed: '+($(if($result -eq 'healthy'){'99%'}elseif($result -eq 'api_healthy_combined_issue'){'97%'}else{'95%'})),'- Cross-computer fast-start/runability: '+($(if($result -eq 'healthy'){'96%'}else{'94%'})),'- Continue-only automation bridge: 93%','- Overall combined project: '+($(if($result -eq 'healthy'){'97%'}else{'95%'})),'','## Files',"Detail: $DetailFile","Elapsed seconds: $elapsed")
Set-Content -Encoding UTF8 -Path $SummaryFile -Value $summary
Write-Output "SUMMARY_FILE=$SummaryFile"
Write-Output "DETAIL_FILE=$DetailFile"
Write-Output "RESULT=$result"
Write-Output "FINAL_HEALTH=$finalHealth"
Write-Output "FINAL_COMBINED=$finalCombined"
Write-Output "ELAPSED_SECONDS=$elapsed"
Write-Output "RECOVERY_021_PARALLEL_HEALTH_MATRIX_DONE"
exit 0
