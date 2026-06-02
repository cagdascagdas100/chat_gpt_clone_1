$ErrorActionPreference = 'Continue'
$TaskId = 'aays-054-supervisor-recovery-status-20260514'
$BridgeRoot = if ($env:AAYS_BRIDGE_ROOT) { $env:AAYS_BRIDGE_ROOT } else { Split-Path -Parent $PSScriptRoot }
$ResultDir = Join-Path $BridgeRoot 'ai-results'
$HeartbeatDir = Join-Path $BridgeRoot 'ai-heartbeat'
New-Item -ItemType Directory -Force -Path $ResultDir,$HeartbeatDir | Out-Null
$Report = Join-Path $ResultDir ('aays-054-supervisor-recovery-status-' + (Get-Date -Format 'yyyyMMdd_HHmmss') + '.md')
$Hb = Join-Path $HeartbeatDir 'portable-runner.md'
function AddR([string]$m){ $m | Add-Content -Encoding UTF8 $Report }
'# AAYS 054 Supervisor Recovery Status' | Set-Content -Encoding UTF8 $Report
AddR ('Generated: ' + (Get-Date -Format s))
AddR 'mode: recovery_status_read_only'
AddR ''
AddR '## PowerShell processes'
try { Get-CimInstance Win32_Process -Filter "name = 'powershell.exe'" | Select-Object ProcessId,ParentProcessId,CommandLine | Format-List | Out-String | Add-Content -Encoding UTF8 $Report } catch { AddR ('PROC_ERROR: ' + $_.Exception.Message) }
AddR ''
AddR '## PostgreSQL processes'
try { Get-CimInstance Win32_Process | Where-Object { $_.Name -match 'postgres|pg_ctl' } | Select-Object ProcessId,ParentProcessId,Name,CommandLine | Format-List | Out-String | Add-Content -Encoding UTF8 $Report } catch { AddR ('PG_PROC_ERROR: ' + $_.Exception.Message) }
AddR ''
AddR '## Repo status'
try { Push-Location $BridgeRoot; git status --short | Out-String | Add-Content -Encoding UTF8 $Report; Pop-Location } catch { AddR ('GIT_STATUS_ERROR: ' + $_.Exception.Message) }
AddR ''
AddR 'plan_progress_percent: 82'
AddR 'AAYS_054_SUPERVISOR_RECOVERY_STATUS_DONE=true'
@('# AAYS Portable Task Runner Fixed','',('Time: ' + (Get-Date -Format 'yyyy-MM-dd HH:mm:ss')),'Status: finished',('TaskId: ' + $TaskId),('BridgeRoot: ' + $BridgeRoot),('TaskFile: ' + (Join-Path $BridgeRoot 'ai-tasks\current-task.json')),('Message: exit=0 aays_054_recovery_status_done progress=82'),'Mode: recovery-status','SafeScriptOnly: enabled') | Set-Content -Encoding UTF8 $Hb
exit 0
