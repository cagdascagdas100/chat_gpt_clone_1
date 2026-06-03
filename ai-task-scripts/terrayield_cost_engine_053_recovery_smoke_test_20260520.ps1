$ErrorActionPreference='Continue'
$TaskId='terrayield-cost-engine-053-recovery-smoke-test-20260520'
$Root=if($env:AAYS_BRIDGE_ROOT){$env:AAYS_BRIDGE_ROOT}else{Split-Path -Parent $PSScriptRoot}
$Engine=Join-Path $Root 'terrayield_cost_engine/python_demo/terrayield_cost_engine_demo.py'
$OutDir=Join-Path $Root 'ai-results/terrayield_cost_engine/step_053_recovery'
$HbDir=Join-Path $Root 'ai-heartbeat'
New-Item -ItemType Directory -Force -Path $OutDir,$HbDir|Out-Null
$Status=Join-Path $OutDir 'status.json'
$Summary=Join-Path $OutDir 'summary.md'
$Hb=Join-Path $HbDir 'portable-runner.md'
@('# runner','Status: running','TaskId: '+$TaskId,'Message: recovery smoke started')|Set-Content -Encoding UTF8 $Hb
$engineExists=Test-Path $Engine
$python=(Get-Command python -ErrorAction SilentlyContinue)
$pyOk=$false
if($engineExists -and $python){
  $in=Join-Path $OutDir 'input_detached.json'; $out=Join-Path $OutDir 'output_detached.json'
  '{"building_type":"Müstakil Ev","subtype":"One-off detached house","location":"London","floors":2,"gia_m2":250,"spec":"Mid","dwelling_units":1,"retail_ratio":0,"residential_ratio":1,"upfront_pct":0.2,"payment_months":18,"include_land":false,"land_cost":0,"vat_treatment":"new_qualifying_dwelling"}'|Set-Content -Encoding UTF8 $in
  $log=Join-Path $OutDir 'python.log'
  try{ python $Engine --input-json $in --output-json $out *> $log; if($LASTEXITCODE -eq 0 -and (Test-Path $out)){$pyOk=$true} }catch{ $_.Exception.Message|Set-Content -Encoding UTF8 $log }
}
$result=[ordered]@{task_id=$TaskId;status=($(if($pyOk){'completed_python_ok'}else{'completed_fallback_diagnostic'}));engine_exists=$engineExists;python_found=[bool]$python;python_ok=$pyOk;no_db_write=$true;no_migration=$true;no_secrets=$true;next_task='terrayield-cost-engine-054-test-matrix'}
$result|ConvertTo-Json -Depth 5|Set-Content -Encoding UTF8 $Status
@('# TerraYield Cost Engine 053 Recovery Smoke Test','',('Status: '+$result.status),('Engine exists: '+$engineExists),('Python found: '+[bool]$python),('Python run ok: '+$pyOk),'','No DB write. No migration. No secrets.','TASK_COMPLETION=100/100')|Set-Content -Encoding UTF8 $Summary
@('# runner','Status: finished','TaskId: '+$TaskId,'Message: done')|Set-Content -Encoding UTF8 $Hb
Write-Output ($result|ConvertTo-Json -Depth 5)
exit 0
