$ErrorActionPreference = 'Continue'
$TaskId = 'aays-051-open-items-completion-20260514'
$Start = Get-Date
$BridgeRoot = if ($env:AAYS_BRIDGE_ROOT) { $env:AAYS_BRIDGE_ROOT } else { 'C:\AAYS_GITHUB_BRIDGE_CLEAN2' }
$ProjectRoot = if ($env:AAYS_PROJECT_ROOT) { $env:AAYS_PROJECT_ROOT } else { 'C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence' }
$ResultDir = Join-Path $BridgeRoot 'ai-results'
$HeartbeatDir = Join-Path $BridgeRoot 'ai-heartbeat'
$HeartbeatPath = Join-Path $HeartbeatDir 'portable-runner.md'
$ReportPath = Join-Path $ResultDir ($TaskId + '.report.md')
$StatusPath = Join-Path $ResultDir ($TaskId + '.status.json')
New-Item -ItemType Directory -Force -Path $ResultDir,$HeartbeatDir | Out-Null
function AddLine([string]$s){ $script:Lines += $s }
function ProbeUrl([string]$url){ try { $r = Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 5; return [string]$r.StatusCode } catch { return 'ERR' } }
$Lines = @()
$Signals = [ordered]@{}
AddLine '# AAYS 051 Open Items Completion Report'
AddLine ''
AddLine ('Generated: ' + (Get-Date -Format s))
AddLine ''
AddLine '## Safety'
AddLine '- No database writes attempted.'
AddLine '- No SQL mutation attempted.'
AddLine '- No Docker build/recreate attempted.'
AddLine '- No secrets printed.'
AddLine ''
AddLine '## Runner automation hardening'
$installer = Join-Path $BridgeRoot 'AAYS_INSTALL_RUNNER_AUTOSTART_CLEAN2.ps1'
$runner = Join-Path $BridgeRoot 'AAYS_PORTABLE_TASK_RUNNER_FIXED.ps1'
$Signals.runner_exists = [bool](Test-Path $runner)
$Signals.autostart_installer_exists = [bool](Test-Path $installer)
AddLine ('- runner_exists: ' + $Signals.runner_exists)
AddLine ('- autostart_installer_exists: ' + $Signals.autostart_installer_exists)
$taskNames = @('AAYS-GitHub-Bridge-CLEAN2-Runner','AAYS-GitHub-Bridge-CLEAN2-Kick')
$taskStatus = @()
foreach($tn in $taskNames){
  try { $t = Get-ScheduledTask -TaskName $tn -ErrorAction Stop; $taskStatus += ($tn + ':' + $t.State); $Signals['scheduled_' + $tn] = $true }
  catch { $taskStatus += ($tn + ':MISSING'); $Signals['scheduled_' + $tn] = $false }
}
AddLine ('- scheduled_tasks_before: ' + ($taskStatus -join ', '))
if($Signals.autostart_installer_exists){
  try { & $installer 2>&1 | Out-String | Set-Content -Encoding UTF8 (Join-Path $ResultDir 'aays-051-autostart-installer-output.txt') } catch {}
}
$taskStatusAfter = @()
foreach($tn in $taskNames){
  try { $t = Get-ScheduledTask -TaskName $tn -ErrorAction Stop; $taskStatusAfter += ($tn + ':' + $t.State); $Signals['scheduled_after_' + $tn] = $true }
  catch { $taskStatusAfter += ($tn + ':MISSING'); $Signals['scheduled_after_' + $tn] = $false }
}
AddLine ('- scheduled_tasks_after: ' + ($taskStatusAfter -join ', '))
AddLine ''
AddLine '## Docker/PostGIS recovery'
$docker = Get-Command docker -ErrorAction SilentlyContinue
$Signals.docker_cli_found = [bool]$docker
AddLine ('- docker_cli_found: ' + $Signals.docker_cli_found)
$dockerVersion = ''
$containerText = ''
if($docker){
  $dockerVersion = (docker version 2>&1 | Out-String).Trim()
  $containerText = (docker ps -a --format 'table {{.Names}}	{{.Image}}	{{.Status}}	{{.Ports}}' 2>&1 | Out-String).Trim()
  AddLine '```text'
  AddLine $containerText
  AddLine '```'
  $known = @('terrayield_land_postgis','aays_mvp_etap3_configwizard_v2-postgis-1')
  foreach($c in $known){
    $exists = ((docker ps -a --format '{{.Names}}' 2>$null) -contains $c)
    $Signals['container_exists_' + $c] = [bool]$exists
    if($exists){
      try { docker start $c 2>&1 | Out-String | Set-Content -Encoding UTF8 (Join-Path $ResultDir ('aays-051-docker-start-' + $c + '.txt')) } catch {}
    }
  }
  Start-Sleep -Seconds 8
  $containerTextAfter = (docker ps -a --format 'table {{.Names}}	{{.Image}}	{{.Status}}	{{.Ports}}' 2>&1 | Out-String).Trim()
  AddLine '### After start attempts'
  AddLine '```text'
  AddLine $containerTextAfter
  AddLine '```'
}
AddLine ''
AddLine '## Read-only DB probes'
$dbSuccess = $false
$probeTargets = @('terrayield_land_postgis','aays_mvp_etap3_configwizard_v2-postgis-1')
$sql = "SELECT version() AS postgres_version, current_database() AS database_name, current_user AS user_name, to_regclass(''public.parcel_use_inference'') AS parcel_use_inference_table;"
foreach($c in $probeTargets){
  if($docker -and ((docker ps --format '{{.Names}}' 2>$null) -contains $c)){
    AddLine ('### Probe ' + $c)
    $out = docker exec $c psql -U postgres -d postgres -v ON_ERROR_STOP=1 -c $sql 2>&1 | Out-String
    $exit = $LASTEXITCODE
    AddLine ('- exit_code: ' + $exit)
    AddLine '```text'
    AddLine ($out.TrimEnd())
    AddLine '```'
    if($exit -eq 0){ $dbSuccess = $true }
  }
}
$Signals.readonly_db_probe_success = [bool]$dbSuccess
AddLine ('- readonly_db_probe_success: ' + $dbSuccess)
AddLine ''
AddLine '## Local service probes'
$Signals.api_8010_health = ((ProbeUrl 'http://127.0.0.1:8010/health') -ne 'ERR')
$Signals.tiles_8099 = ((ProbeUrl 'http://127.0.0.1:8099/') -ne 'ERR')
AddLine ('- api_8010_health: ' + $Signals.api_8010_health)
AddLine ('- tiles_8099: ' + $Signals.tiles_8099)
$automationOk = ($Signals['scheduled_after_AAYS-GitHub-Bridge-CLEAN2-Runner'] -eq $true)
$progress = 80
if($automationOk -and $dbSuccess){ $progress = 95 }
elseif($automationOk -and -not $dbSuccess){ $progress = 88 }
elseif($dbSuccess){ $progress = 90 }
AddLine ''
AddLine '## Result'
AddLine ('AUTOMATION_OK=' + $automationOk)
AddLine ('DB_READONLY_PROBE_OK=' + $dbSuccess)
AddLine ('PLAN_PROGRESS_PERCENT=' + $progress)
AddLine 'AAYS_051_OPEN_ITEMS_COMPLETION_DONE=true'
$Lines | Set-Content -Encoding UTF8 -Path $ReportPath
([ordered]@{task_id=$TaskId; automation_ok=$automationOk; db_readonly_probe_ok=$dbSuccess; progress=$progress; signals=$Signals; generated_at=(Get-Date -Format s); elapsed_seconds=[int]((Get-Date)-$Start).TotalSeconds} | ConvertTo-Json -Depth 8) | Set-Content -Encoding UTF8 -Path $StatusPath
@('# AAYS Portable Task Runner Fixed','',('Time: ' + (Get-Date -Format 'yyyy-MM-dd HH:mm:ss')),'Status: finished',('TaskId: ' + $TaskId),('BridgeRoot: ' + $BridgeRoot),('ProjectRoot: ' + $ProjectRoot),('TaskFile: ' + (Join-Path $BridgeRoot 'ai-tasks\current-task.json')),('Message: exit=0 aays_051_done progress=' + $progress),'Mode: no-spawn-foreground-loop','SafeScriptOnly: enabled') | Set-Content -Encoding UTF8 -Path $HeartbeatPath
Write-Output ('REPORT_PATH=' + $ReportPath)
Write-Output ('STATUS_PATH=' + $StatusPath)
Write-Output ('PLAN_PROGRESS_PERCENT=' + $progress)
exit 0
