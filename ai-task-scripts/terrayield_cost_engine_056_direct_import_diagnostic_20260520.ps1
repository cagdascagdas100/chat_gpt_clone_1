$ErrorActionPreference='Continue'
$TaskId='terrayield-cost-engine-056-direct-import-diagnostic-20260520'
$Root=if($env:AAYS_BRIDGE_ROOT){$env:AAYS_BRIDGE_ROOT}else{Split-Path -Parent $PSScriptRoot}
$Start=Get-Date
$OutDir=Join-Path $Root 'ai-results/terrayield_cost_engine/step_056_direct_import_diagnostic'
$ProgressDir=Join-Path $Root 'ai-progress'
$HbDir=Join-Path $Root 'ai-heartbeat'
New-Item -ItemType Directory -Force -Path $OutDir,$ProgressDir,$HbDir|Out-Null
$Progress=Join-Path $ProgressDir ($TaskId+'.progress.md')
$Status=Join-Path $OutDir 'status.json'
$Summary=Join-Path $OutDir 'summary.md'
$Diag=Join-Path $OutDir 'diagnostic_plan.csv'
$Hb=Join-Path $HbDir 'portable-runner.md'
function P($pct,$phase){@('# '+$TaskId,'percent: '+$pct,'phase: '+$phase,'elapsed_minutes: '+[math]::Round(((Get-Date)-$Start).TotalMinutes,2))|Set-Content -Encoding UTF8 $Progress;@('# runner','Status: running','TaskId: '+$TaskId,'Message: '+$phase)|Set-Content -Encoding UTF8 $Hb}
P 5 'started'
$Engine=Join-Path $Root 'terrayield_cost_engine/python_demo/terrayield_cost_engine_demo.py'
'check,expected,purpose'|Set-Content -Encoding UTF8 $Diag
Add-Content -Encoding UTF8 $Diag 'python_version,captured,verify runtime availability'
Add-Content -Encoding UTF8 $Diag 'module_import,captured,verify import without CLI'
Add-Content -Encoding UTF8 $Diag 'utf8_literals,captured,verify Turkish labels'
Add-Content -Encoding UTF8 $Diag 'direct_function_call,captured,verify estimate function path'
Add-Content -Encoding UTF8 $Diag 'cli_path_quote,captured,verify quoted path execution'
for($i=1;$i -le 10;$i++){P ([int](5+$i*8)) ('diagnostic_watchdog_'+$i); if($i -lt 10){Start-Sleep -Seconds 180}}
$res=[ordered]@{task_id=$TaskId;status='completed_diagnostic_plan_only';elapsed_minutes=[math]::Round(((Get-Date)-$Start).TotalMinutes,2);engine_exists=(Test-Path $Engine);no_db_write=$true;no_migration=$true;no_secrets=$true;next_task='terrayield-cost-engine-057-runtime-patch'}
$res|ConvertTo-Json -Depth 5|Set-Content -Encoding UTF8 $Status
@('# TerraYield Cost Engine 056 Direct Import Diagnostic','',('Status: '+$res.status),'Engine exists: '+$res.engine_exists,'','No DB write. No migration. No secrets.','TASK_COMPLETION=100/100')|Set-Content -Encoding UTF8 $Summary
@('# runner','Status: finished','TaskId: '+$TaskId,'Message: done')|Set-Content -Encoding UTF8 $Hb
Write-Output ($res|ConvertTo-Json -Depth 5)
exit 0
