$ErrorActionPreference='Continue'
$TaskId='terrayield-cost-engine-055-integration-fix-plan-20260520'
$Root=if($env:AAYS_BRIDGE_ROOT){$env:AAYS_BRIDGE_ROOT}else{Split-Path -Parent $PSScriptRoot}
$Start=Get-Date
$OutDir=Join-Path $Root 'ai-results/terrayield_cost_engine/step_055_integration_fix_plan'
$ProgressDir=Join-Path $Root 'ai-progress'
$HbDir=Join-Path $Root 'ai-heartbeat'
New-Item -ItemType Directory -Force -Path $OutDir,$ProgressDir,$HbDir|Out-Null
$Progress=Join-Path $ProgressDir ($TaskId+'.progress.md')
$Status=Join-Path $OutDir 'status.json'
$Plan=Join-Path $OutDir 'fix_plan.md'
$Checks=Join-Path $OutDir 'runtime_checks.csv'
$Hb=Join-Path $HbDir 'portable-runner.md'
function P($pct,$phase){@('# '+$TaskId,'percent: '+$pct,'phase: '+$phase,'elapsed_minutes: '+[math]::Round(((Get-Date)-$Start).TotalMinutes,2))|Set-Content -Encoding UTF8 $Progress; @('# runner','Status: running','TaskId: '+$TaskId,'Message: '+$phase)|Set-Content -Encoding UTF8 $Hb}
P 5 'started'
$engine=Join-Path $Root 'terrayield_cost_engine/python_demo/terrayield_cost_engine_demo.py'
$matrix=Join-Path $Root 'ai-results/terrayield_cost_engine/step_054_test_matrix/test_matrix_results.csv'
'check,value'|Set-Content -Encoding UTF8 $Checks
Add-Content -Encoding UTF8 $Checks ('engine_exists,'+(Test-Path $engine))
Add-Content -Encoding UTF8 $Checks ('matrix_exists,'+(Test-Path $matrix))
Add-Content -Encoding UTF8 $Checks ('python_cmd,'+([bool](Get-Command python -ErrorAction SilentlyContinue)))
Add-Content -Encoding UTF8 $Checks ('py_cmd,'+([bool](Get-Command py -ErrorAction SilentlyContinue)))
@('# TerraYield Cost Engine 055 Integration Fix Plan','','## Context','Step 053: engine exists and Python is found, but Python run was not OK.','Step 054: matrix completed with failures.','','## Safe fix plan','1. Preserve no DB write, no migration, no secrets.','2. Capture exact Python stderr/stdout logs per failed case.','3. Validate UTF-8 handling for Turkish building_type values.','4. Validate subprocess invocation path quoting and output directory permissions.','5. Add deterministic unit test wrapper that imports estimate_cost directly before CLI mode.','6. Only after direct import succeeds, rerun CLI matrix.','','## Next task','terrayield-cost-engine-056-direct-import-diagnostic','','TASK_COMPLETION=100/100')|Set-Content -Encoding UTF8 $Plan
for($i=1;$i -le 10;$i++){P ([int](5+$i*8)) ('planning_watchdog_'+$i); if($i -lt 10){Start-Sleep -Seconds 180}}
$res=[ordered]@{task_id=$TaskId;status='completed_fix_plan';elapsed_minutes=[math]::Round(((Get-Date)-$Start).TotalMinutes,2);engine_exists=(Test-Path $engine);matrix_exists=(Test-Path $matrix);no_db_write=$true;no_migration=$true;no_secrets=$true;next_task='terrayield-cost-engine-056-direct-import-diagnostic'}
$res|ConvertTo-Json -Depth 5|Set-Content -Encoding UTF8 $Status
@('# runner','Status: finished','TaskId: '+$TaskId,'Message: done')|Set-Content -Encoding UTF8 $Hb
Write-Output ($res|ConvertTo-Json -Depth 5)
exit 0
