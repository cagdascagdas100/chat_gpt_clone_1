$ErrorActionPreference = 'Continue'
$TaskId = 'aays-057-direct-autopilot-recovery-status-20260514'
$BridgeRoot = if ($env:AAYS_BRIDGE_ROOT) { $env:AAYS_BRIDGE_ROOT } else { Split-Path -Parent $PSScriptRoot }
$ResultDir = Join-Path $BridgeRoot 'ai-results'
$HeartbeatDir = Join-Path $BridgeRoot 'ai-heartbeat'
New-Item -ItemType Directory -Force -Path $ResultDir,$HeartbeatDir | Out-Null
$Report = Join-Path $ResultDir ('aays-057-direct-autopilot-recovery-status-' + (Get-Date -Format 'yyyyMMdd_HHmmss') + '.md')
function AddR([string]$m){ $m | Add-Content -Encoding UTF8 $Report }
'# AAYS 057 Direct Autopilot Recovery Status' | Set-Content -Encoding UTF8 $Report
AddR ('Generated: ' + (Get-Date -Format s))
AddR 'mode: direct_autopilot_recovery_read_only'
AddR ''
AddR '## Heartbeats'
foreach($f in @('ai-heartbeat/direct-autopilot.md','ai-heartbeat/autopilot-watcher-v4.md','ai-heartbeat/autopilot-supervisor-v2.md','ai-heartbeat/portable-runner.md')){ $p=Join-Path $BridgeRoot $f; AddR ('### ' + $f); if(Test-Path $p){ Get-Content -Raw -Encoding UTF8 $p | Add-Content -Encoding UTF8 $Report } else { AddR 'MISSING' }; AddR '' }
AddR '## Current task'
$pTask=Join-Path $BridgeRoot 'ai-tasks/current-task.json'; if(Test-Path $pTask){ Get-Content -Raw -Encoding UTF8 $pTask | Add-Content -Encoding UTF8 $Report }
AddR ''
AddR '## Last task markers'
foreach($f in @('ai-tasks/.direct-autopilot-last-task-id','ai-tasks/.watcher-v4-last-task-id','ai-tasks/.supervisor-v2-last-task-id','ai-tasks/.supervisor-last-task-id','ai-tasks/.last-task-id')){ $p=Join-Path $BridgeRoot $f; AddR ('### ' + $f); if(Test-Path $p){ Get-Content -Raw -Encoding UTF8 $p | Add-Content -Encoding UTF8 $Report } else { AddR 'MISSING' }; AddR '' }
AddR '## Recent result files'
try { Get-ChildItem (Join-Path $BridgeRoot 'ai-results') -File | Sort-Object LastWriteTime -Descending | Select-Object -First 30 Name,LastWriteTime,Length | Format-Table -AutoSize | Out-String | Add-Content -Encoding UTF8 $Report } catch { AddR ('RESULT_LIST_ERROR: ' + $_.Exception.Message) }
AddR '## Recent runner logs'
try { Get-ChildItem (Join-Path $BridgeRoot 'ai-runner-logs') -File | Sort-Object LastWriteTime -Descending | Select-Object -First 20 Name,LastWriteTime,Length | Format-Table -AutoSize | Out-String | Add-Content -Encoding UTF8 $Report } catch { AddR ('LOG_LIST_ERROR: ' + $_.Exception.Message) }
AddR ''
AddR 'plan_progress_percent: 82'
AddR 'AAYS_057_DIRECT_AUTOPILOT_RECOVERY_STATUS_DONE=true'
$Hb = Join-Path $HeartbeatDir 'direct-autopilot-task-status.md'
@('# AAYS Direct Autopilot Task Status','',('Time: ' + (Get-Date -Format 'yyyy-MM-dd HH:mm:ss')),'Status: finished',('TaskId: ' + $TaskId),('Message: recovery status generated'),('Report: ' + $Report)) | Set-Content -Encoding UTF8 $Hb
exit 0
