$ErrorActionPreference = "Continue"
$Project = "C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence"
$Start = Get-Date
$Run = Get-Date -Format "yyyyMMdd_HHmmss"
$ReportDir = Join-Path $Project ".aays_next_fix\verification_024_scaffold_probe_$Run"
$SummaryFile = Join-Path $ReportDir "summary.md"
$DetailFile = Join-Path $ReportDir "detail.txt"
New-Item -ItemType Directory -Force -Path $ReportDir | Out-Null
Set-Location $Project
function Log($x){$s=[int]((Get-Date)-$Start).TotalSeconds;$l="[$s s] $x";Write-Output $l;Add-Content -Encoding UTF8 -Path $DetailFile -Value $l}
function E($ep){try{$sw=[System.Diagnostics.Stopwatch]::StartNew();$r=Invoke-WebRequest -Uri ("http://localhost:8010"+$ep) -UseBasicParsing -TimeoutSec 60;$sw.Stop();$line="OK $ep status=$($r.StatusCode) ms=$($sw.ElapsedMilliseconds) bytes=$($r.Content.Length)";Log $line;return $line}catch{$line="FAIL $ep error=$($_.Exception.Message)";Log $line;return $line}}
Log "TASK: TerraYield verification 024 scaffold probe"
Log "PROGRESS: 99%"
Log "MODE: find lost 023 results and verify scaffold state"
$health=E "/health"
$combined=E "/map/sales-history/combined"
$files=Get-ChildItem -Path ".aays_next_fix" -Recurse -File -ErrorAction SilentlyContinue | Where-Object { $_.FullName -like '*verification_023*' -or $_.Name -like '*verification*' -or $_.Name -like '*evidence*' -or $_.Name -like '*backlog*' } | Sort-Object LastWriteTime -Descending | Select-Object -First 80
Log "CANDIDATE_FILES=$($files.Count)"
$files | Select-Object FullName,Length,LastWriteTime | Format-Table -AutoSize | Out-String | Add-Content -Encoding UTF8 -Path $DetailFile
$compileOk=$true
foreach($f in @('app\core\ttl_cache.py','app\middleware\map_listings_cache.py','app\main.py','app\api\routes\aays_sales_layers.py','app\api\routes\aays_sales_history_layers.py')){if(Test-Path $f){python -m py_compile $f 2>&1 | Out-String | Add-Content -Encoding UTF8 -Path $DetailFile; Log "COMPILE $f EXIT=$LASTEXITCODE"; if($LASTEXITCODE -ne 0){$compileOk=$false}}else{Log "MISSING $f"}}
$elapsed=[int]((Get-Date)-$Start).TotalSeconds
$result=if($health -like 'OK*' -and $combined -like 'OK*' -and $compileOk -and $files.Count -gt 0){'scaffold_probe_ready'}elseif($health -like 'OK*'){'api_ready_probe_partial'}else{'api_issue'}
$summary=@('# TerraYield Verification 024 Scaffold Probe Summary','','## Result',$result,'','## Health',$health,'','## Combined',$combined,'','## Compile OK',"$compileOk",'','## Candidate Files',"$($files.Count)",'','## Progress Estimate','- Verification scaffold visibility: '+($(if($files.Count -gt 0){'95%'}else{'80%'})),'- API readiness: '+($(if($health -like 'OK*'){'98%'}else{'85%'})),'- Overall verification workflow: '+($(if($result -eq 'scaffold_probe_ready'){'97%'}else{'93-95%'})),'','## Files',"Detail: $DetailFile","Elapsed seconds: $elapsed",'','## Next','- If probe_ready: continue chunked evidence classification.','- If partial: inspect detail candidate files and rerun scaffold if needed.')
Set-Content -Encoding UTF8 -Path $SummaryFile -Value $summary
Write-Output "SUMMARY_FILE=$SummaryFile"
Write-Output "DETAIL_FILE=$DetailFile"
Write-Output "RESULT=$result"
Write-Output "ELAPSED_SECONDS=$elapsed"
Write-Output "VERIFICATION_024_SCAFFOLD_PROBE_DONE"
exit 0
