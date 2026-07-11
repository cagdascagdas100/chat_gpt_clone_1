[CmdletBinding()]
param(
  [string]$PortableRoot,
  [string]$TaskName = "AAYS_TerraYield_SingleRunner",
  [switch]$LogonOnly,
  [switch]$Uninstall
)

$ErrorActionPreference = "Stop"
function Now-Utc { (Get-Date).ToUniversalTime().ToString("o") }
function Resolve-PortableRoot {
  if ($PortableRoot) { return [System.IO.Path]::GetFullPath($PortableRoot).TrimEnd("\") }
  if ($env:AAYS_PORTABLE_ROOT) { return [System.IO.Path]::GetFullPath($env:AAYS_PORTABLE_ROOT).TrimEnd("\") }
  $repoRoot = (& git -C $PSScriptRoot rev-parse --show-toplevel 2>$null)
  if (-not $repoRoot) { throw "Portable root could not be resolved; pass -PortableRoot." }
  $repoRoot = [System.IO.Path]::GetFullPath($repoRoot.Trim())
  $marker = "\runner_system\"
  $index = $repoRoot.IndexOf($marker, [System.StringComparison]::OrdinalIgnoreCase)
  if ($index -lt 1) { throw "Repo is not under a portable runner_system path: $repoRoot" }
  return $repoRoot.Substring(0,$index)
}

$portable = Resolve-PortableRoot
if ($portable.StartsWith("C:\", [System.StringComparison]::OrdinalIgnoreCase)) { throw "C_DRIVE_NOT_CANONICAL: $portable" }
$repoRoot = Join-Path $portable "runner_system\AAYS_WT\AAYS_RUNNER_HEALTHY_20260707"
$workRoot = Join-Path $portable "runner_system\AAYS_WT\AAYS_STABLE_RUNNER_WORKTREES"
$daemon = Join-Path $repoRoot "docs\chatgpt_status\_shared\automation\RUN_AAYS_STABLE_LEGACY_RUNNER_DAEMON_20260707.ps1"
$proofPath = Join-Path $repoRoot "docs\chatgpt_status\_shared\status\persistent_runner_scheduled_task_latest.json"
if ($Uninstall) {
  Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue
  [pscustomobject]@{ task_name=$TaskName; status="uninstalled"; checked_at=Now-Utc } | ConvertTo-Json -Depth 10
  exit 0
}
if (-not (Test-Path -LiteralPath $daemon)) { throw "Canonical daemon missing: $daemon" }

$powerShell = "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe"
$arguments = @(
  "-NoProfile","-WindowStyle","Hidden","-ExecutionPolicy","Bypass","-File",('"'+$daemon+'"'),
  "-RepoRoot",('"'+$repoRoot+'"'),"-RepoFullName","cagdascagdas100/chat_gpt_clone_1",
  "-MainBranch","codex/aays-single-runner-v5-20260706","-WorkRoot",('"'+$workRoot+'"'),
  "-IntervalSeconds","60","-HeartbeatSeconds","15","-MaxTasks","8","-MaxLoops","0",
  "-RefreshIntervalSeconds","43200","-SiteCheckIntervalSeconds","60"
) -join " "
$action = New-ScheduledTaskAction -Execute $powerShell -Argument $arguments -WorkingDirectory $portable
$triggers = @((New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME))
if (-not $LogonOnly) { $triggers += New-ScheduledTaskTrigger -AtStartup }
$settings = New-ScheduledTaskSettingsSet -MultipleInstances IgnoreNew -RestartCount 999 -RestartInterval (New-TimeSpan -Minutes 1) -ExecutionTimeLimit ([TimeSpan]::Zero) -StartWhenAvailable -WakeToRun -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
$principal = New-ScheduledTaskPrincipal -UserId ([System.Security.Principal.WindowsIdentity]::GetCurrent().Name) -LogonType Interactive -RunLevel Limited
$task = New-ScheduledTask -Action $action -Trigger $triggers -Settings $settings -Principal $principal -Description "AAYS TerraYield canonical F portable single shared runner supervisor"
$triggerMode = if ($LogonOnly) { "logon_only" } else { "startup_and_logon" }
try {
  Register-ScheduledTask -TaskName $TaskName -InputObject $task -Force | Out-Null
} catch {
  if ($LogonOnly) { throw }
  # A standard user can always retain restart persistence through the logon trigger.
  $triggers = @((New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME))
  $task = New-ScheduledTask -Action $action -Trigger $triggers -Settings $settings -Principal $principal -Description "AAYS TerraYield canonical F portable single shared runner supervisor"
  Register-ScheduledTask -TaskName $TaskName -InputObject $task -Force | Out-Null
  $triggerMode = "logon_only_fallback"
}
$registered = Get-ScheduledTask -TaskName $TaskName -ErrorAction Stop
$info = Get-ScheduledTaskInfo -TaskName $TaskName -ErrorAction Stop
$payload = [ordered]@{
  task_name = $TaskName
  status = $registered.State.ToString()
  installed = $true
  portable_root = $portable
  repo_root = $repoRoot
  daemon_path = $daemon
  action_execute = $registered.Actions.Execute
  action_arguments = $registered.Actions.Arguments
  action_working_directory = $registered.Actions.WorkingDirectory
  trigger_count = @($registered.Triggers).Count
  trigger_mode = $triggerMode
  multiple_instances = $registered.Settings.MultipleInstances
  restart_count = $registered.Settings.RestartCount
  restart_interval = $registered.Settings.RestartInterval
  execution_time_limit = $registered.Settings.ExecutionTimeLimit
  start_when_available = $registered.Settings.StartWhenAvailable
  wake_to_run = $registered.Settings.WakeToRun
  last_run_time = $info.LastRunTime
  last_task_result = $info.LastTaskResult
  checked_at = Now-Utc
  single_runner_only = $true
  parallel_runner = $false
  final_ready = $false
  fake_data = $false
  db_write = $false
  migration = $false
  production_deploy = $false
}
$directory = Split-Path -Parent $proofPath
if (-not (Test-Path -LiteralPath $directory)) { New-Item -ItemType Directory -Force -Path $directory | Out-Null }
$payload | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath $proofPath -Encoding UTF8
$payload | ConvertTo-Json -Depth 20
