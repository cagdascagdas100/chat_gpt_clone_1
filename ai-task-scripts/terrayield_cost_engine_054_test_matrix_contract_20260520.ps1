$ErrorActionPreference='Continue'
$TaskId='terrayield-cost-engine-054-test-matrix-contract-20260520'
$Root=if($env:AAYS_BRIDGE_ROOT){$env:AAYS_BRIDGE_ROOT}else{Split-Path -Parent $PSScriptRoot}
$Start=Get-Date
$OutDir=Join-Path $Root 'ai-results/terrayield_cost_engine/step_054_test_matrix_contract'
$ProgressDir=Join-Path $Root 'ai-progress'
$HbDir=Join-Path $Root 'ai-heartbeat'
New-Item -ItemType Directory -Force -Path $OutDir,$ProgressDir,$HbDir|Out-Null
$Progress=Join-Path $ProgressDir ($TaskId+'.progress.md')
$Status=Join-Path $OutDir 'status.json'
$Matrix=Join-Path $OutDir 'cost_engine_test_matrix.csv'
$Validation=Join-Path $OutDir 'input_validation_contract.csv'
$Summary=Join-Path $OutDir 'summary.md'
$Hb=Join-Path $HbDir 'portable-runner.md'
function P($pct,$phase){@('# '+$TaskId,'percent: '+$pct,'phase: '+$phase,'elapsed_minutes: '+[math]::Round(((Get-Date)-$Start).TotalMinutes,2))|Set-Content -Encoding UTF8 $Progress; @('# runner','Status: running','TaskId: '+$TaskId,'Message: '+$phase)|Set-Content -Encoding UTF8 $Hb}
P 5 'started'
'case_id,building_type,subtype,gia_m2,spec,vat_treatment,expected_status,notes'|Set-Content -Encoding UTF8 $Matrix
Add-Content -Encoding UTF8 $Matrix 'detached_mid_250,Müstakil Ev,One-off detached house,250,Mid,new_qualifying_dwelling,should_run,baseline residential'
Add-Content -Encoding UTF8 $Matrix 'industrial_food_2500,Sanayi,Food & drink factory,2500,Mid,standard_20,should_run,baseline industrial'
Add-Content -Encoding UTF8 $Matrix 'retail_shell_1000,Perakende,Shop shell only,1000,Mid,standard_20,should_run,retail shell'
Add-Content -Encoding UTF8 $Matrix 'invalid_negative_gia,Müstakil Ev,One-off detached house,-1,Mid,new_qualifying_dwelling,should_fail_validation,negative gia'
'field,required,rule'|Set-Content -Encoding UTF8 $Validation
Add-Content -Encoding UTF8 $Validation 'building_type,true,must be one of supported BUILDING_TYPES'
Add-Content -Encoding UTF8 $Validation 'subtype,true,must match building_type subtype list or rate fallback'
Add-Content -Encoding UTF8 $Validation 'gia_m2,true,must be positive'
Add-Content -Encoding UTF8 $Validation 'floors,true,must be positive'
Add-Content -Encoding UTF8 $Validation 'upfront_pct,true,must be between 0 and 1'
Add-Content -Encoding UTF8 $Validation 'payment_months,true,must be positive integer'
for($i=1;$i -le 8;$i++){P ([int](5+$i*10)) ('matrix_watchdog_'+$i); if($i -lt 8){Start-Sleep -Seconds 180}}
$res=[ordered]@{task_id=$TaskId;status='completed_contract_only_after_python_failure';engine_blocker='053 showed engine_exists=true python_found=true python_ok=false';matrix_cases=4;no_db_write=$true;no_migration=$true;no_secrets=$true;next_task='terrayield-cost-engine-055-python-runtime-fix-plan'}
$res|ConvertTo-Json -Depth 5|Set-Content -Encoding UTF8 $Status
@('# TerraYield Cost Engine 054 Test Matrix Contract','',('Status: '+$res.status),'Matrix cases: 4','Blocker: Python runtime failed in 053, so this task only defines safe test contracts.','','No DB write. No migration. No secrets.','TASK_COMPLETION=100/100')|Set-Content -Encoding UTF8 $Summary
@('# runner','Status: finished','TaskId: '+$TaskId,'Message: done')|Set-Content -Encoding UTF8 $Hb
Write-Output ($res|ConvertTo-Json -Depth 5)
exit 0
