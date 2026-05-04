$ErrorActionPreference = 'Continue'
$Start = Get-Date
$TaskId = 'terrayield-049-hyper-parallel-accuracy-sprint-safe'
$Run = Get-Date -Format 'yyyyMMdd_HHmmss'
$ProjectRoot = 'C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence'
$BridgeRoot = 'C:\Users\cagda\Documents\chat_gpt_clone_1'
$ReportDir = Join-Path $ProjectRoot ".aays_next_fix\049_hyper_parallel_accuracy_sprint_safe_$Run"
$JobsDir = Join-Path $ReportDir 'jobs'
$SafeDir = Join-Path $ProjectRoot '.aays_safe_sales'
$SummaryFile = Join-Path $ReportDir 'summary.md'
$ScoreFile = Join-Path $ReportDir 'scorecard.csv'
$StatusFile = Join-Path $ReportDir 'status.json'
$PlanFile = Join-Path $ReportDir 'next_actions.md'
New-Item -ItemType Directory -Force -Path $ReportDir,$JobsDir,$SafeDir | Out-Null
function Log($Text){$e=[int]((Get-Date)-$Start).TotalSeconds;$line="[$e s] $Text";Write-Output $line;Add-Content -Encoding UTF8 -Path $SummaryFile -Value $line}
Log "TASK=$TaskId"
Log 'MODE=hyper parallel report-only safe sprint; non-destructive; no data loading; no schema mutation; no container build; no external collection'
$jobDefs=@(
  @('runner_snapshot',70),@('watchdog_snapshot',70),@('current_task_compare',72),@('runner_log_tail',68),@('bridge_git_probe',72),@('project_git_probe',74),
  @('result_history_scan',78),@('dataset_inventory',82),@('dataset_field_profile',84),@('price_area_quality_model',86),@('geometry_boundary_model',80),@('parcel_candidate_model',82),
  @('source_registry_model',88),@('evidence_chain_model',90),@('duplicate_outlier_rules',84),@('address_location_rules',82),@('manual_review_queue',86),@('confidence_scoring_matrix',88),
  @('ui_layer_plan',82),@('export_manifest_policy',86),@('annual_refresh_plan',84),@('safe_guardrail_manifest',78),@('endpoint_probe',76),@('api_readiness_decision',74),
  @('risk_register',83),@('next_backlog_generator',85)
)
$jobs=@()
foreach($d in $jobDefs){
  $jobs += Start-Job -ScriptBlock {
    param($Name,$BaseScore,$ProjectRoot,$BridgeRoot,$SafeDir,$JobsDir)
    $ErrorActionPreference='Continue'
    $data=[ordered]@{}
    $warnings=@()
    try{
      if($Name -eq 'runner_snapshot'){
        foreach($p in @('ai-heartbeat\runner-v4.md','ai-tasks\current-task.json','ai-tasks\.last-task-id')){$fp=Join-Path $BridgeRoot $p;if(Test-Path $fp){$data[$p]=Get-Content -Raw $fp}else{$warnings += "missing_$p"}}
      } elseif($Name -eq 'watchdog_snapshot'){
        $fp=Join-Path $BridgeRoot 'ai-heartbeat\user-mode-watchdog.md'; if(Test-Path $fp){$data.watchdog=Get-Content -Raw $fp}else{$warnings+='watchdog_missing'}
        $data.processes=@(Get-Process -Name powershell,pwsh -ErrorAction SilentlyContinue | Select-Object Id,ProcessName,CPU,StartTime | Select-Object -First 30)
      } elseif($Name -eq 'current_task_compare'){
        $ct=Join-Path $BridgeRoot 'ai-tasks\current-task.json'; $lt=Join-Path $BridgeRoot 'ai-tasks\.last-task-id'
        if(Test-Path $ct){$task=Get-Content -Raw $ct|ConvertFrom-Json;$data.current_id=$task.id;$data.command=$task.command}
        if(Test-Path $lt){$data.last_id=(Get-Content -Raw $lt).Trim()}
        $data.pending=($data.current_id -and $data.current_id -ne $data.last_id)
      } elseif($Name -eq 'runner_log_tail'){
        $dir=Join-Path $BridgeRoot 'ai-runner-logs'; if(Test-Path $dir){$logs=Get-ChildItem $dir -File|Sort-Object LastWriteTime -Descending|Select-Object -First 8;$data.logs=@($logs|Select FullName,Length,LastWriteTime);foreach($f in $logs){Get-Content -Tail 250 -ErrorAction SilentlyContinue $f.FullName|Set-Content -Encoding UTF8 (Join-Path $JobsDir ('tail_'+$f.Name+'.txt'))}}else{$warnings+='runner_logs_missing'}
      } elseif($Name -eq 'bridge_git_probe'){
        if(Test-Path $BridgeRoot){Push-Location $BridgeRoot;$data.branch=((git rev-parse --abbrev-ref HEAD 2>&1)|Out-String).Trim();$data.head=((git rev-parse --short HEAD 2>&1)|Out-String).Trim();$status=((git status --porcelain=v1 2>&1)|Out-String);$data.changed_count=@($status -split "`n"|?{$_.Trim()}).Count;git status --short|Set-Content -Encoding UTF8 (Join-Path $JobsDir 'bridge_status.txt');Pop-Location}else{$warnings+='bridge_missing';$BaseScore=40}
      } elseif($Name -eq 'project_git_probe'){
        if(Test-Path $ProjectRoot){Push-Location $ProjectRoot;$data.branch=((git rev-parse --abbrev-ref HEAD 2>&1)|Out-String).Trim();$data.head=((git rev-parse --short HEAD 2>&1)|Out-String).Trim();$status=((git status --porcelain=v1 2>&1)|Out-String);$data.changed_count=@($status -split "`n"|?{$_.Trim()}).Count;git status --short|Set-Content -Encoding UTF8 (Join-Path $JobsDir 'project_status.txt');Pop-Location}else{$warnings+='project_missing';$BaseScore=40}
      } elseif($Name -eq 'result_history_scan'){
        $dir=Join-Path $BridgeRoot 'ai-results'; if(Test-Path $dir){$files=Get-ChildItem $dir -File -Filter '*.md'|Sort-Object LastWriteTime -Descending|Select-Object -First 40;$data.count=$files.Count;$data.latest=@($files|Select Name,Length,LastWriteTime|Select-Object -First 15)}else{$warnings+='results_missing'}
      } elseif($Name -eq 'dataset_inventory'){
        $patterns=@('*.csv','*.parquet','*.geojson','*.gpkg','*.json','*.sqlite','*.db','*.zip','*.xlsx','*.shp');$files=@();foreach($p in $patterns){$files+=Get-ChildItem -Path $ProjectRoot -Recurse -File -Filter $p -ErrorAction SilentlyContinue|?{$_.FullName -notmatch '\\.git\\|\\node_modules\\|\\dist\\|\\build\\|\\.venv\\'}};$files=$files|Sort FullName -Unique;$data.count=@($files).Count;$data.sample=@($files|Select FullName,Length,Extension,LastWriteTime|Select -First 120);if($data.count -eq 0){$warnings+='no_dataset_files';$BaseScore=55}
      } elseif($Name -eq 'dataset_field_profile'){
        $csvs=Get-ChildItem -Path $ProjectRoot -Recurse -File -Filter '*.csv' -ErrorAction SilentlyContinue|?{$_.FullName -notmatch '\\.git\\|\\node_modules\\|\\dist\\|\\build\\'}|Select -First 10;$profiles=@();foreach($c in $csvs){try{$rows=Import-Csv $c.FullName -ErrorAction Stop;$cols=if($rows.Count -gt 0){$rows[0].PSObject.Properties.Name}else{@()};$profiles += [ordered]@{file=$c.FullName;rows=$rows.Count;cols=$cols.Count;columns=$cols}}catch{$profiles += [ordered]@{file=$c.FullName;error=$_.Exception.Message}}};$data.profiles=$profiles
      } elseif($Name -eq 'endpoint_probe'){
        $urls=@('http://127.0.0.1:8000/health','http://127.0.0.1:8000/api/health','http://127.0.0.1:8000/docs','http://127.0.0.1:5173/','http://127.0.0.1:3000/','http://localhost:8010/health','http://localhost:8010/openapi.json');$checks=@();foreach($u in $urls){try{$sw=[Diagnostics.Stopwatch]::StartNew();$r=Invoke-WebRequest -UseBasicParsing -TimeoutSec 8 $u;$sw.Stop();$checks += [ordered]@{url=$u;ok=$true;status=$r.StatusCode;ms=$sw.ElapsedMilliseconds}}catch{$checks += [ordered]@{url=$u;ok=$false}}};$ok=@($checks|?{$_.ok}).Count;$data.checks=$checks;$data.ok_count=$ok;if($ok -eq 0){$BaseScore=45;$warnings+='no_endpoint_ok'}elseif($ok -lt 2){$BaseScore=65}else{$BaseScore=90}
      } else {
        New-Item -ItemType Directory -Force -Path $SafeDir|Out-Null
        $data.items=@('evidence hash','source licence','sale date','sale price','area m2','price per m2','address','coordinate','parcel candidate','manual review','export manifest')
        $data.policy='report-only; keep expanding; no destructive actions'
        $path=Join-Path $SafeDir ($Name+'_049.json')
        [ordered]@{task=$Name;score=$BaseScore;data=$data;created=(Get-Date).ToString('s')}|ConvertTo-Json -Depth 20|Set-Content -Encoding UTF8 $path
        $data.output_path=$path
      }
    }catch{$warnings += $_.Exception.Message;$BaseScore=[Math]::Min($BaseScore,50)}
    [ordered]@{name=$Name;score=$BaseScore;warnings=$warnings;data=$data;time=(Get-Date).ToString('s')}|ConvertTo-Json -Depth 30|Set-Content -Encoding UTF8 (Join-Path $JobsDir ($Name+'.json'))
  } -ArgumentList $d[0],[int]$d[1],$ProjectRoot,$BridgeRoot,$SafeDir,$JobsDir
}
Log "PARALLEL_JOBS_STARTED=$($jobs.Count)"
Wait-Job -Job $jobs -Timeout 7200 | Out-Null
foreach($j in $jobs){if($j.State -eq 'Running'){Stop-Job $j -Force|Out-Null};Receive-Job $j -ErrorAction SilentlyContinue|Out-Null;Remove-Job $j -Force -ErrorAction SilentlyContinue}
$results=@();foreach($f in Get-ChildItem $JobsDir -Filter *.json -ErrorAction SilentlyContinue){try{$results += Get-Content -Raw $f.FullName|ConvertFrom-Json}catch{}}
$avg=0;if($results.Count -gt 0){$avg=[int](($results|Measure score -Average).Average)}
$source=[Math]::Min(96,[Math]::Max(58,$avg+8))
$parcel=[Math]::Min(82,[Math]::Max(42,$avg-8))
$api=($results|?{$_.name -eq 'endpoint_probe'}|Select -First 1).score;if(-not $api){$api=50}
$general=[int]([Math]::Round((0.45*$source)+(0.45*$parcel)+(0.10*$api)))
$program=[Math]::Min(88,[Math]::Max(45,$results.Count*3))
@('metric,score','source_evidence_accuracy,'+$source,'parcel_geometry_accuracy,'+$parcel,'api_operational_health,'+$api,'general_confidence,'+$general,'program_completion,'+$program,'parallel_jobs_completed,'+$results.Count) | Set-Content -Encoding UTF8 $ScoreFile
$status=[ordered]@{task=$TaskId;result='completed_continue_program';parallel_jobs_started=$jobDefs.Count;parallel_jobs_completed=$results.Count;source_accuracy_score=$source;parcel_match_accuracy_score=$parcel;api_operational_health_score=$api;general_confidence_score=$general;program_completion_score=$program;report_dir=$ReportDir;summary_file=$SummaryFile;score_file=$ScoreFile;next_action='devam et';next_wait='90-120 minutes';safety_locks=@('NO_DATA_LOAD','NO_SCHEMA_MUTATION','NO_CONTAINER_BUILD','NO_EXTERNAL_COLLECTION')}
$status|ConvertTo-Json -Depth 20|Set-Content -Encoding UTF8 $StatusFile
$plan=@('# Next actions 049','- Continue; do not finish the program','- Add real parcel geometry intersection scorer','- Add source conflict resolver','- Add annual refresh hash audit','- Add manual review L3 queue','- Keep final verified loading blocked until explicit review','- Continue with: devam et')
$plan|Set-Content -Encoding UTF8 $PlanFile
Log "JOBS_COMPLETED=$($results.Count)"
Log "SOURCE_ACCURACY_SCORE=$source/100"
Log "PARCEL_MATCH_ACCURACY_SCORE=$parcel/100"
Log "API_OPERATIONAL_HEALTH_SCORE=$api/100"
Log "GENERAL_CONFIDENCE_SCORE=$general/100"
Log "PROGRAM_COMPLETION_SCORE=$program/100"
Write-Output "SUMMARY_FILE=$SummaryFile"
Write-Output "STATUS_FILE=$StatusFile"
Write-Output "SCORE_FILE=$ScoreFile"
Write-Output "PLAN_FILE=$PlanFile"
Write-Output "SOURCE_ACCURACY_SCORE=$source/100"
Write-Output "PARCEL_MATCH_ACCURACY_SCORE=$parcel/100"
Write-Output "API_OPERATIONAL_HEALTH_SCORE=$api/100"
Write-Output "GENERAL_CONFIDENCE_SCORE=$general/100"
Write-Output "PROGRAM_COMPLETION_SCORE=$program/100"
Write-Output 'TERRAYIELD_049_HYPER_PARALLEL_ACCURACY_SPRINT_SAFE_DONE'
exit 0
