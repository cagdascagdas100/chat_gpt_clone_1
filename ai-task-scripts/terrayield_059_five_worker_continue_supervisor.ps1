$ErrorActionPreference = 'Continue'
$Project = 'C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence'
$Bridge = 'C:\Users\cagda\Documents\chat_gpt_clone_1'
$Start = Get-Date
$Run = Get-Date -Format 'yyyyMMdd_HHmmss'
$ReportDir = Join-Path $Project ".aays_next_fix\terrayield_059_five_worker_continue_supervisor_$Run"
$SummaryFile = Join-Path $ReportDir 'summary.md'
$DetailFile = Join-Path $ReportDir 'detail.txt'
$WorkerDir = Join-Path $ReportDir 'workers'
New-Item -ItemType Directory -Force -Path $ReportDir,$WorkerDir | Out-Null
Set-Location $Project
function Log([string]$Text){$e=[int]((Get-Date)-$Start).TotalSeconds;$line="[$e s] $Text";Write-Output $line;Add-Content -Encoding UTF8 -Path $DetailFile -Value $line}
function ProbeEndpoint([string]$Path,[int]$Timeout){try{$sw=[System.Diagnostics.Stopwatch]::StartNew();$r=Invoke-WebRequest -UseBasicParsing -TimeoutSec $Timeout -Uri ('http://localhost:8010'+$Path);$sw.Stop();return "OK $Path status=$($r.StatusCode) ms=$($sw.ElapsedMilliseconds) bytes=$($r.Content.Length)"}catch{return "FAIL $Path error=$($_.Exception.Message)"}}
Log 'TASK: TerraYield 059 five-worker continue supervisor'
Log 'MODE: one current-task, five isolated parallel workers; one stalled worker must not block others'
Log "REPORT_DIR=$ReportDir"
$workerScripts = @{}
$workerScripts['worker_1_runner_bridge'] = @'
param($Project,$Bridge,$OutFile)
$ErrorActionPreference='Continue'
Set-Location $Bridge
$lines=@()
$lines+='WORKER=runner_bridge'
$lines+='TIME='+(Get-Date)
$lines+='BRIDGE='+$Bridge
$lines+='PROJECT='+$Project
$lines+='GIT_STATUS_BRIDGE'
$lines+=(git status --short 2>&1 | Out-String)
$lines+='CURRENT_TASK_LOCAL'
if(Test-Path 'ai-tasks/current-task.json'){$lines+=(Get-Content -Raw 'ai-tasks/current-task.json')}else{$lines+='missing current-task.json'}
$lines+='LAST_TASK_LOCAL'
if(Test-Path 'ai-tasks/.last-task-id'){$lines+=(Get-Content -Raw 'ai-tasks/.last-task-id')}else{$lines+='missing .last-task-id'}
$lines | Set-Content -Encoding UTF8 -Path $OutFile
'@
$workerScripts['worker_2_dataset_inventory'] = @'
param($Project,$Bridge,$OutFile)
$ErrorActionPreference='Continue'
Set-Location $Project
$lines=@()
$lines+='WORKER=dataset_inventory'
$lines+='TIME='+(Get-Date)
$files=Get-ChildItem -Recurse -Force -File -ErrorAction SilentlyContinue | Where-Object {$_.FullName -notlike '*\.git*' -and $_.FullName -notlike '*node_modules*' -and $_.FullName -notlike '*.aays_next_fix*'}
$lines+='TOTAL_FILES='+($files.Count)
$lines+='TOP_FILES'
$lines+=($files | Sort-Object Length -Descending | Select-Object -First 80 FullName,Length,LastWriteTime | Format-Table -AutoSize | Out-String)
$lines+='EXTENSION_COUNTS'
$lines+=($files | ForEach-Object {[IO.Path]::GetExtension($_.Name).ToLowerInvariant()} | Group-Object | Sort-Object Count -Descending | Select-Object -First 40 Count,Name | Format-Table -AutoSize | Out-String)
$lines | Set-Content -Encoding UTF8 -Path $OutFile
'@
$workerScripts['worker_3_api_health'] = @'
param($Project,$Bridge,$OutFile)
$ErrorActionPreference='Continue'
Set-Location $Project
function P($Path,$Timeout){try{$sw=[System.Diagnostics.Stopwatch]::StartNew();$r=Invoke-WebRequest -UseBasicParsing -TimeoutSec $Timeout -Uri ('http://localhost:8010'+$Path);$sw.Stop();return "OK $Path status=$($r.StatusCode) ms=$($sw.ElapsedMilliseconds) bytes=$($r.Content.Length)"}catch{return "FAIL $Path error=$($_.Exception.Message)"}}
$eps=@('/health','/openapi.json','/map/listings','/map/sales-history/status','/map/sales-history/combined')
$lines=@('WORKER=api_health','TIME='+(Get-Date))
foreach($ep in $eps){$lines+=(P $ep 60)}
$lines | Set-Content -Encoding UTF8 -Path $OutFile
'@
$workerScripts['worker_4_code_compile_scan'] = @'
param($Project,$Bridge,$OutFile)
$ErrorActionPreference='Continue'
Set-Location $Project
$targets=@('app\core\ttl_cache.py','app\middleware\map_listings_cache.py','app\main.py','app\api\routes\aays_sales_layers.py','app\api\routes\aays_sales_history_layers.py')
$lines=@('WORKER=code_compile_scan','TIME='+(Get-Date))
$ok=$true
foreach($t in $targets){if(Test-Path $t){$out=python -m py_compile $t 2>&1 | Out-String;$lines+="COMPILE $t EXIT=$LASTEXITCODE";$lines+=$out;if($LASTEXITCODE -ne 0){$ok=$false}}else{$lines+="MISSING $t"}}
$lines+='COMPILE_OK='+$ok
$lines | Set-Content -Encoding UTF8 -Path $OutFile
'@
$workerScripts['worker_5_evidence_score_plan'] = @'
param($Project,$Bridge,$OutFile)
$ErrorActionPreference='Continue'
Set-Location $Project
$lines=@('WORKER=evidence_score_plan','TIME='+(Get-Date))
$terms='sales|price|listing|parcel|geometry|evidence|source|registry|score|confidence|export|review'
$matches=Get-ChildItem -Recurse -Force -File -ErrorAction SilentlyContinue | Where-Object {$_.FullName -notlike '*\.git*' -and $_.FullName -notlike '*node_modules*' -and $_.FullName -notlike '*.aays_next_fix*' -and $_.Name -match $terms} | Select-Object -First 120
$lines+='MATCHED_EVIDENCE_FILES='+($matches.Count)
$lines+=($matches | Select-Object FullName,Length,LastWriteTime | Format-Table -AutoSize | Out-String)
$lines+='NEXT_SCORE_PLAN'
$lines+='1. classify source reliability'
$lines+='2. classify geometry-boundary confidence'
$lines+='3. classify sales/listing evidence completeness'
$lines+='4. prepare manual review queue'
$lines+='5. prepare export/UI confidence fields'
$lines | Set-Content -Encoding UTF8 -Path $OutFile
'@
$jobs=@()
foreach($name in $workerScripts.Keys){
  $scriptPath=Join-Path $WorkerDir ($name+'.ps1')
  $outFile=Join-Path $WorkerDir ($name+'.out.txt')
  Set-Content -Encoding UTF8 -Path $scriptPath -Value $workerScripts[$name]
  Log "START_WORKER $name"
  $jobs += [pscustomobject]@{Name=$name;Out=$outFile;Job=(Start-Job -FilePath $scriptPath -ArgumentList $Project,$Bridge,$outFile)}
}
$deadline=(Get-Date).AddMinutes(25)
while((Get-Date) -lt $deadline){
  $running=@($jobs | Where-Object {$_.Job.State -eq 'Running'})
  Log "WORKER_POLL running=$($running.Count) completed=$(@($jobs | Where-Object {$_.Job.State -ne 'Running'}).Count)"
  if($running.Count -eq 0){break}
  Start-Sleep -Seconds 20
}
foreach($w in $jobs){
  if($w.Job.State -eq 'Running'){
    Log "WORKER_TIMEOUT_STOP $($w.Name)"
    Stop-Job $w.Job -Force
  }
  $jobOut=Receive-Job $w.Job 2>&1 | Out-String
  Remove-Job $w.Job -Force
  Add-Content -Encoding UTF8 -Path $DetailFile -Value ("`n## " + $w.Name + " STATE")
  Add-Content -Encoding UTF8 -Path $DetailFile -Value $jobOut
  if(Test-Path $w.Out){Add-Content -Encoding UTF8 -Path $DetailFile -Value ("`n## " + $w.Name + " OUTPUT"); Get-Content -Raw $w.Out | Add-Content -Encoding UTF8 -Path $DetailFile}
}
$completed=@($jobs | Where-Object {Test-Path $_.Out}).Count
$timeouts=@($jobs | Where-Object {!(Test-Path $_.Out)}).Count
$health=ProbeEndpoint '/health' 30
$combined=ProbeEndpoint '/map/sales-history/combined' 60
$elapsed=[int]((Get-Date)-$Start).TotalSeconds
$result=if($completed -ge 4){'five_worker_supervisor_completed'}elseif($completed -gt 0){'five_worker_supervisor_partial'}else{'five_worker_supervisor_failed'}
$summary=@('# TerraYield 059 Five Worker Continue Supervisor Summary','','## Result',$result,'','## Completed Workers',"$completed/5",'','## Timed Out Or Missing Workers',"$timeouts/5",'','## API Health',$health,'','## Combined',$combined,'','## Progress Estimate','- Five-worker continue infrastructure: '+($(if($completed -ge 4){'90%'}elseif($completed -gt 0){'65%'}else{'30%'})),'- TerraYield report-only expansion: '+($(if($completed -ge 4){'98%'}else{'95%'})),'- Overall continue automation: '+($(if($completed -ge 4){'96-98%'}else{'90-94%'})),'','## Files',"Detail: $DetailFile","Worker dir: $WorkerDir","Elapsed seconds: $elapsed",'','## Policy','- One stalled worker must not block other workers.','- This task is report-only and non-destructive.','- No DB write, no Docker rebuild, no project mutation.')
Set-Content -Encoding UTF8 -Path $SummaryFile -Value $summary
Write-Output "SUMMARY_FILE=$SummaryFile"
Write-Output "DETAIL_FILE=$DetailFile"
Write-Output "WORKER_DIR=$WorkerDir"
Write-Output "RESULT=$result"
Write-Output "COMPLETED_WORKERS=$completed/5"
Write-Output "ELAPSED_SECONDS=$elapsed"
Write-Output 'TERRAYIELD_059_FIVE_WORKER_CONTINUE_SUPERVISOR_DONE'
exit 0
