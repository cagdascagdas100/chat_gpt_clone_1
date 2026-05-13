$ErrorActionPreference='Continue'
$TaskId='aays-050-runner-state-inventory-20260514'
$BridgeRoot=if($env:AAYS_BRIDGE_ROOT){$env:AAYS_BRIDGE_ROOT}else{'C:\AAYS_GITHUB_BRIDGE_CLEAN2'}
$ResultDir=Join-Path $BridgeRoot 'ai-results'
New-Item -ItemType Directory -Force -Path $ResultDir | Out-Null
function Log($m){Write-Output ('['+(Get-Date -Format s)+'] '+$m)}
function Has($p){return [bool](Test-Path $p)}
function Count($r,$f){try{if(Test-Path $r){return @(Get-ChildItem -Path $r -Filter $f -File -Recurse -ErrorAction SilentlyContinue).Count}}catch{};return 0}
Log "TASK=$TaskId"
$checks=[ordered]@{bridge_root=Has $BridgeRoot;v6_runner=Has (Join-Path $BridgeRoot 'AAYS_AUTOPILOT_RUNNER_V6_SAFE_SYNC.ps1');current_task=Has (Join-Path $BridgeRoot 'ai-tasks\current-task.json');last_task=Has (Join-Path $BridgeRoot 'ai-tasks\.last-task-id');results_dir=Has $ResultDir}
$counts=[ordered]@{result_md=Count $ResultDir '*.md';scripts=Count (Join-Path $BridgeRoot 'ai-task-scripts') '*.ps1';logs=Count (Join-Path $BridgeRoot 'ai-runner-logs') '*.log';manifests=Count (Join-Path $BridgeRoot 'manifests') '*.json'}
foreach($k in $checks.Keys){Log ($k+'='+$checks[$k])}
foreach($k in $counts.Keys){Log ($k+'='+$counts[$k])}
$out=Join-Path $ResultDir "$TaskId.report.md"
$r=@('# AAYS 050 Runner State Inventory','',"Generated: $(Get-Date -Format s)","Task: $TaskId",'','## Checks')
foreach($k in $checks.Keys){$r+="- ${k}: $($checks[$k])"}
$r+=''
$r+='## Counts'
foreach($k in $counts.Keys){$r+="- ${k}: $($counts[$k])"}
$r+=''
$r+='PLAN_PROGRESS_PERCENT=99'
$r+='TASK_COMPLETION=100/100'
$r+='TERRAYIELD_TASK_DONE'
$r|Set-Content -Path $out -Encoding UTF8
Log "REPORT_PATH=$out"
Log 'PLAN_PROGRESS_PERCENT=99'
Log 'TASK_COMPLETION=100/100'
exit 0
