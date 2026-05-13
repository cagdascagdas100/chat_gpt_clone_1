$ErrorActionPreference = 'Continue'
$BridgeRoot = if ($env:AAYS_BRIDGE_ROOT) { $env:AAYS_BRIDGE_ROOT } else { 'C:\AAYS_GITHUB_BRIDGE_CLEAN2' }
$Runner = Join-Path $BridgeRoot 'AAYS_AUTOPILOT_RUNNER_V6_SAFE_SYNC.ps1'
$LogDir = Join-Path $BridgeRoot 'ai-runner-logs'
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
$Out = Join-Path $LogDir 'aays-runner-v6-status.txt'
$procs = Get-CimInstance Win32_Process -Filter "Name = 'powershell.exe' OR Name = 'pwsh.exe'" | Where-Object { $_.CommandLine -like '*AAYS_AUTOPILOT_RUNNER_V6_SAFE_SYNC.ps1*' }
@(
  'AAYS_RUNNER_V6_STATUS',
  ('time=' + (Get-Date -Format s)),
  ('bridge_root=' + $BridgeRoot),
  ('runner_exists=' + (Test-Path $Runner)),
  ('runner_process_count=' + @($procs).Count),
  ('current_task_exists=' + (Test-Path (Join-Path $BridgeRoot 'ai-tasks\current-task.json'))),
  ('last_task_exists=' + (Test-Path (Join-Path $BridgeRoot 'ai-tasks\.last-task-id')))
) | Set-Content -Encoding UTF8 -Path $Out
Get-Content $Out
exit 0
