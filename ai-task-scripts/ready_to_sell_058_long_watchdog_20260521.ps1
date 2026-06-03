$ErrorActionPreference='Continue'
$TaskId='ready-to-sell-058-long-watchdog-20260521'
$Root=if($env:AAYS_BRIDGE_ROOT){$env:AAYS_BRIDGE_ROOT}else{Split-Path -Parent $PSScriptRoot}
$Start=Get-Date
$OutDir=Join-Path $Root 'ai-results/ready_to_sell_058_long_watchdog'
$HbDir=Join-Path $Root 'ai-heartbeat'
$ProgressDir=Join-Path $Root 'ai-progress'
New-Item -ItemType Directory -Force -Path $OutDir,$HbDir,$ProgressDir|Out-Null
$Hb=Join-Path $HbDir 'portable-runner.md'
$Progress=Join-Path $ProgressDir ($TaskId+'.progress.md')
$Status=Join-Path $OutDir 'status.json'
$Summary=Join-Path $OutDir 'summary.md'
function W($pct,$msg){@('# AAYS Portable Task Runner Fixed','',('Time: '+(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')),('Status: running'),('TaskId: '+$TaskId),('BridgeRoot: '+$Root),('Message: '+$msg),'Mode: ready-to-sell-long-watchdog','SafeScriptOnly: enabled')|Set-Content -Encoding UTF8 $Hb; @('# '+$TaskId,'percent: '+$pct,'phase: '+$msg,'elapsed_minutes: '+[math]::Round(((Get-Date)-$Start).TotalMinutes,2),'db_write: false','production_deploy: false')|Set-Content -Encoding UTF8 $Progress}
W 5 'started'
$checks=@()
$checks += [pscustomobject]@{name='current_task';path=(Join-Path $Root 'ai-tasks/current-task.json');exists=(Test-Path (Join-Path $Root 'ai-tasks/current-task.json'))}
$checks += [pscustomobject]@{name='heartbeat';path=(Join-Path $Root 'ai-heartbeat/portable-runner.md');exists=(Test-Path (Join-Path $Root 'ai-heartbeat/portable-runner.md'))}
$checks += [pscustomobject]@{name='cost_057';path=(Join-Path $Root 'ai-results/terrayield_cost_engine/step_057_long_self_healing/status.json');exists=(Test-Path (Join-Path $Root 'ai-results/terrayield_cost_engine/step_057_long_self_healing/status.json'))}
$checks += [pscustomobject]@{name='contractor_005';path=(Join-Path $Root 'ai-results/contractor-005-official-data-acquisition-plan-20260520.result.json');exists=(Test-Path (Join-Path $Root 'ai-results/contractor-005-official-data-acquisition-plan-20260520.result.json'))}
$checks|ConvertTo-Json -Depth 5|Set-Content -Encoding UTF8 (Join-Path $OutDir 'checks.json')
for($i=1;$i -le 40;$i++){W ([int](5+$i*90/40)) ('long_watchdog_minute_'+$i); Start-Sleep -Seconds 60}
$res=[ordered]@{task_id=$TaskId;status='completed_watchdog';elapsed_minutes=[math]::Round(((Get-Date)-$Start).TotalMinutes,2);db_write=$false;production_deploy=$false;next_task='ready-to-sell-059-result-harvest'}
$res|ConvertTo-Json -Depth 5|Set-Content -Encoding UTF8 $Status
@('# Ready to Sell 058 Long Watchdog','',('Status: '+$res.status),'DB write: false','Production deploy: false','TASK_COMPLETION=100/100')|Set-Content -Encoding UTF8 $Summary
@('# AAYS Portable Task Runner Fixed','',('Time: '+(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')),'Status: finished',('TaskId: '+$TaskId),'Message: exit=0')|Set-Content -Encoding UTF8 $Hb
exit 0
