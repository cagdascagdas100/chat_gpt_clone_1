$ErrorActionPreference = 'Continue'
$TaskId = 'aays-040-psql-manual-install-launcher-20260513'
$BridgeRoot = if ($env:AAYS_BRIDGE_ROOT) { $env:AAYS_BRIDGE_ROOT } else { Split-Path -Parent $PSScriptRoot }
$ResultDir = Join-Path $BridgeRoot 'ai-results'
$HeartbeatDir = Join-Path $BridgeRoot 'ai-heartbeat'
$HeartbeatPath = Join-Path $HeartbeatDir 'portable-runner.md'
New-Item -ItemType Directory -Force -Path $ResultDir,$HeartbeatDir | Out-Null
function Log([string]$m){ Write-Output ('[' + (Get-Date -Format s) + '] ' + $m) }
function FindPsql {
  $cmd = Get-Command psql -ErrorAction SilentlyContinue
  if($cmd){ return $cmd.Source }
  $paths = @('C:\Program Files\PostgreSQL\17\bin\psql.exe','C:\Program Files\PostgreSQL\16\bin\psql.exe','C:\Program Files\PostgreSQL\15\bin\psql.exe','C:\Program Files\PostgreSQL\14\bin\psql.exe','C:\Program Files\PostgreSQL\13\bin\psql.exe','C:\Program Files\PostgreSQL\12\bin\psql.exe')
  foreach($p in $paths){ if(Test-Path $p){ return $p } }
  return $null
}
Log "TASK=$TaskId"
Log 'MODE=psql_manual_install_launcher'
Log 'NO_DB_WRITE=true'
Log 'NO_UI_PATCH=true'
Log 'MAY_OPEN_INSTALLER_OR_UAC=true'
$before = FindPsql
Log ('PSQL_BEFORE=' + $before)
$winget = Get-Command winget -ErrorAction SilentlyContinue
$attempted = $false
$exitCode = ''
if(-not $before -and $winget){
  Log 'WINGET_FOUND=true'
  Log 'WINGET_INSTALL_INTERACTIVE_START=PostgreSQL.PostgreSQL'
  try {
    winget install --id PostgreSQL.PostgreSQL -e --accept-source-agreements --accept-package-agreements --scope machine
    $exitCode = [string]$LASTEXITCODE
    $attempted = $true
    Log ('WINGET_INSTALL_INTERACTIVE_EXIT_CODE=' + $exitCode)
  } catch {
    Log ('WINGET_INSTALL_INTERACTIVE_ERROR=' + $_.Exception.Message)
  }
} elseif(-not $before) {
  Log 'WINGET_FOUND=false'
}
Start-Sleep -Seconds 5
$after = FindPsql
$found = $false
if($after){
  $found = $true
  $bin = Split-Path $after -Parent
  if($env:Path -notlike ('*' + $bin + '*')){ $env:Path = $bin + ';' + $env:Path; Log ('SESSION_PATH_ADDED=' + $bin) }
  try {
    $userPath = [Environment]::GetEnvironmentVariable('Path','User')
    if($userPath -notlike ('*' + $bin + '*')){ [Environment]::SetEnvironmentVariable('Path', ($bin + ';' + $userPath), 'User'); Log ('USER_PATH_ADDED=' + $bin) } else { Log 'USER_PATH_ALREADY_OK=true' }
  } catch { Log ('USER_PATH_ERROR=' + $_.Exception.Message) }
  try { $ver = & $after --version 2>&1 | Out-String; Log ('PSQL_VERSION=' + $ver.Trim()) } catch {}
}
$progress = 72
if($found){ $progress = 82 }
Log ('PSQL_AFTER=' + $after)
Log ('PSQL_FOUND=' + $found)
Log ('PLAN_PROGRESS_PERCENT=' + $progress)
$reportPath = Join-Path $ResultDir ($TaskId + '.report.md')
$report = @('# AAYS 040 psql Manual Install Launcher','',('Generated: ' + (Get-Date -Format s)),'','## Summary',('- psql before: ' + $before),('- winget found: ' + [bool]$winget),('- install attempted: ' + $attempted),('- install exit code: ' + $exitCode),('- psql after: ' + $after),('- psql found: ' + $found),('- plan progress percent: ' + $progress),'','## Next')
if($found){ $report += 'psql is available. Proceed to DB staging dry-run.'; $report += 'Wait 2 minutes, then say: devam et' } else { $report += 'psql is still missing. Run the manual PostgreSQL installer as Administrator, then say: devam et.'; $report += 'Wait 0 minutes after failed install.' }
$report += ''; $report += 'AAYS_040_PSQL_MANUAL_INSTALL_LAUNCHER_DONE=true'
$report | Set-Content -Encoding UTF8 -Path $reportPath
@('# AAYS Portable Task Runner Fixed','',('Time: ' + (Get-Date -Format 'yyyy-MM-dd HH:mm:ss')),'Status: finished',('TaskId: ' + $TaskId),('BridgeRoot: ' + $BridgeRoot),('TaskFile: ' + (Join-Path $BridgeRoot 'ai-tasks\current-task.json')),('Message: exit=0 aays_040_psql_launcher_done progress=' + $progress),'Mode: no-spawn-foreground-loop','SafeScriptOnly: enabled') | Set-Content -Encoding UTF8 -Path $HeartbeatPath
Log ('REPORT_PATH=' + $reportPath)
Log 'TERRAYIELD_TASK_DONE'
exit 0
