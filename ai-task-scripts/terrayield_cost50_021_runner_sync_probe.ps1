$ErrorActionPreference='Continue'
$TaskId='cost50-021-runner-sync-probe-20260512'
$BridgeRoot=Split-Path -Parent $PSScriptRoot
$ResultDir=Join-Path $BridgeRoot 'ai-results'
New-Item -ItemType Directory -Force -Path $ResultDir|Out-Null
function Log($m){Write-Output ('['+(Get-Date -Format s)+'] '+$m)}
Log "TASK=$TaskId"
Log 'MODE=runner_sync_probe_readonly'
Log "BRIDGE_ROOT=$BridgeRoot"
Log ('CURRENT_TASK_EXISTS='+(Test-Path (Join-Path $BridgeRoot 'ai-tasks\current-task.json')))
Log ('LAST_TASK_EXISTS='+(Test-Path (Join-Path $BridgeRoot 'ai-tasks\.last-task-id')))
Log ('HEARTBEAT_EXISTS='+(Test-Path (Join-Path $BridgeRoot 'ai-heartbeat\portable-runner.md')))
$out=Join-Path $ResultDir "$TaskId.report.md"
@('# Cost50 021 Runner Sync Probe','',"Generated: $(Get-Date -Format s)",'','PLAN_PROGRESS_PERCENT=100','TASK_COMPLETION=100/100','TERRAYIELD_TASK_DONE')|Set-Content -Encoding UTF8 -Path $out
Log "REPORT_PATH=$out"
Log 'PLAN_PROGRESS_PERCENT=100'
Log 'TASK_COMPLETION=100/100'
Log 'TERRAYIELD_TASK_DONE'
exit 0
