$ErrorActionPreference = 'Continue'
$TaskId = 'aays-038-runner-watchdog-psql-probe-20260513'
$BridgeRoot = if ($env:AAYS_BRIDGE_ROOT) { $env:AAYS_BRIDGE_ROOT } else { Split-Path -Parent $PSScriptRoot }
$ResultDir = Join-Path $BridgeRoot 'ai-results'
$HeartbeatDir = Join-Path $BridgeRoot 'ai-heartbeat'
$HeartbeatPath = Join-Path $HeartbeatDir 'portable-runner.md'
New-Item -ItemType Directory -Force -Path $ResultDir,$HeartbeatDir | Out-Null
function Log([string]$m){ Write-Output ('[' + (Get-Date -Format s) + '] ' + $m) }
Log "TASK=$TaskId"
Log 'MODE=runner_watchdog_psql_probe_readonly'
Log 'NO_DB_WRITE=true'
Log 'NO_UI_PATCH=true'
$psql = Get-Command psql -ErrorAction SilentlyContinue
$psqlFound = $false
$psqlPath = ''
if($psql){ $psqlFound = $true; $psqlPath = $psql.Source }
else {
  $candidates = @('C:\Program Files\PostgreSQL\17\bin\psql.exe','C:\Program Files\PostgreSQL\16\bin\psql.exe','C:\Program Files\PostgreSQL\15\bin\psql.exe','C:\Program Files\PostgreSQL\14\bin\psql.exe','C:\Program Files\PostgreSQL\13\bin\psql.exe','C:\Program Files\PostgreSQL\12\bin\psql.exe')
  foreach($c in $candidates){ if(Test-Path $c){ $psqlFound = $true; $psqlPath = $c; break } }
}
Log ('PSQL_FOUND=' + $psqlFound)
Log ('PSQL_PATH=' + $psqlPath)
$progress = 72
if($psqlFound){ $progress = 82 }
Log ('PLAN_PROGRESS_PERCENT=' + $progress)
$reportPath = Join-Path $ResultDir ($TaskId + '.report.md')
$report = @('# AAYS 038 Runner Watchdog psql Probe','',('Generated: ' + (Get-Date -Format s)),'','## Summary',('- psql found: ' + $psqlFound),('- psql path: ' + $psqlPath),('- plan progress percent: ' + $progress),'','## Next')
if($psqlFound){ $report += 'Proceed to AAYS 039 DB staging import.'; $report += 'Wait 3-5 minutes, then say: devam et' } else { $report += 'psql is still missing. Install PostgreSQL client or run PATH recovery.'; $report += 'Wait 0 minutes, then say: devam et for install commands.' }
$report += ''; $report += 'AAYS_038_WATCHDOG_PSQL_PROBE_DONE=true'
$report | Set-Content -Encoding UTF8 -Path $reportPath
@('# AAYS Portable Task Runner Fixed','',('Time: ' + (Get-Date -Format 'yyyy-MM-dd HH:mm:ss')),'Status: finished',('TaskId: ' + $TaskId),('BridgeRoot: ' + $BridgeRoot),('TaskFile: ' + (Join-Path $BridgeRoot 'ai-tasks\current-task.json')),('Message: exit=0 aays_038_probe_done progress=' + $progress),'Mode: no-spawn-foreground-loop','SafeScriptOnly: enabled') | Set-Content -Encoding UTF8 -Path $HeartbeatPath
Log ('REPORT_PATH=' + $reportPath)
Log 'TERRAYIELD_TASK_DONE'
exit 0
