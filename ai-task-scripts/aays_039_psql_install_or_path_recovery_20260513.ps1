$ErrorActionPreference = 'Continue'
$TaskId = 'aays-039-psql-install-or-path-recovery-20260513'
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
Log 'MODE=psql_install_or_path_recovery'
Log 'NO_DB_WRITE=true'
Log 'NO_UI_PATCH=true'
Log 'MAY_TRIGGER_INSTALLER_OR_UAC=true'
$before = FindPsql
Log ('PSQL_BEFORE=' + $before)
$installAttempted = $false
$installExit = ''
if(-not $before){
  $winget = Get-Command winget -ErrorAction SilentlyContinue
  if($winget){
    Log 'WINGET_FOUND=true'
    Log 'WINGET_INSTALL_START=PostgreSQL.PostgreSQL'
    try {
      winget install --id PostgreSQL.PostgreSQL -e --accept-source-agreements --accept-package-agreements --silent
      $installExit = [string]$LASTEXITCODE
      $installAttempted = $true
      Log ('WINGET_INSTALL_EXIT_CODE=' + $installExit)
    } catch {
      Log ('WINGET_INSTALL_ERROR=' + $_.Exception.Message)
    }
  } else {
    Log 'WINGET_FOUND=false'
  }
}
Start-Sleep -Seconds 5
$after = FindPsql
Log ('PSQL_AFTER=' + $after)
$psqlFound = $false
if($after){
  $psqlFound = $true
  $bin = Split-Path $after -Parent
  if($env:Path -notlike ('*' + $bin + '*')){ $env:Path = $bin + ';' + $env:Path; Log ('SESSION_PATH_ADDED=' + $bin) }
  try {
    $userPath = [Environment]::GetEnvironmentVariable('Path','User')
    if($userPath -notlike ('*' + $bin + '*')){ [Environment]::SetEnvironmentVariable('Path', ($bin + ';' + $userPath), 'User'); Log ('USER_PATH_ADDED=' + $bin) } else { Log 'USER_PATH_ALREADY_OK=true' }
  } catch { Log ('USER_PATH_ERROR=' + $_.Exception.Message) }
  try { $ver = & $after --version 2>&1 | Out-String; Log ('PSQL_VERSION=' + $ver.Trim()) } catch { Log ('PSQL_VERSION_ERROR=' + $_.Exception.Message) }
}
$progress = 72
if($psqlFound){ $progress = 82 }
Log ('PLAN_PROGRESS_PERCENT=' + $progress)
if($psqlFound){ Log 'NEXT_TASK=aays-040-db-staging-import-dryrun'; Log 'NEXT_WAIT_MINUTES=3-5' } else { Log 'NEXT_TASK=manual-postgresql-client-install'; Log 'NEXT_WAIT_MINUTES=0' }
$reportPath = Join-Path $ResultDir ($TaskId + '.report.md')
$report = @('# AAYS 039 psql Install or PATH Recovery','',('Generated: ' + (Get-Date -Format s)),'','## Summary',('- psql before: ' + $before),('- install attempted: ' + $installAttempted),('- install exit code: ' + $installExit),('- psql after: ' + $after),('- psql found: ' + $psqlFound),('- plan progress percent: ' + $progress),'','## Next')
if($psqlFound){ $report += 'psql is available. Proceed to DB staging import dry-run.'; $report += 'Wait 3-5 minutes, then say: devam et' } else { $report += 'psql is still missing. Manual PostgreSQL client install is required or UAC/winget failed.'; $report += 'Wait 0 minutes, then say: devam et for manual installer commands.' }
$report += ''; $report += 'AAYS_039_PSQL_INSTALL_OR_PATH_RECOVERY_DONE=true'
$report | Set-Content -Encoding UTF8 -Path $reportPath
@('# AAYS Portable Task Runner Fixed','',('Time: ' + (Get-Date -Format 'yyyy-MM-dd HH:mm:ss')),'Status: finished',('TaskId: ' + $TaskId),('BridgeRoot: ' + $BridgeRoot),('TaskFile: ' + (Join-Path $BridgeRoot 'ai-tasks\current-task.json')),('Message: exit=0 aays_039_psql_recovery_done progress=' + $progress),'Mode: no-spawn-foreground-loop','SafeScriptOnly: enabled') | Set-Content -Encoding UTF8 -Path $HeartbeatPath
Log ('REPORT_PATH=' + $reportPath)
Log 'TERRAYIELD_TASK_DONE'
exit 0
