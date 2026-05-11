$ErrorActionPreference = 'Continue'

$TaskId = 'terrayield-054-bridge-status-push-probe'
$BridgeRoot = if ($env:AAYS_BRIDGE_ROOT) { $env:AAYS_BRIDGE_ROOT } else { 'C:\AAYS_GITHUB_BRIDGE_CLEAN' }
$ProjectRoot = if ($env:AAYS_PROJECT_ROOT) { $env:AAYS_PROJECT_ROOT } else { 'C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence' }
$ResultDir = Join-Path $BridgeRoot 'ai-results'
$HeartbeatDir = Join-Path $BridgeRoot 'ai-heartbeat'
$LogDir = Join-Path $BridgeRoot 'ai-runner-logs'

function Step([string]$Text) { Write-Output ('[' + (Get-Date -Format 's') + '] ' + $Text) }

New-Item -ItemType Directory -Force -Path $ResultDir,$HeartbeatDir,$LogDir | Out-Null

Step "TASK=$TaskId"
Step "MODE=bridge_status_push_probe"
Step "BRIDGE_ROOT=$BridgeRoot"
Step "PROJECT_ROOT=$ProjectRoot"
Step "COMPUTER=$env:COMPUTERNAME"
Step "USER=$env:USERNAME"
Step "POWERSHELL=$($PSVersionTable.PSVersion.ToString())"

Step 'PROCESS_CHECK_BEGIN'
try {
  Get-CimInstance Win32_Process -Filter "Name = 'powershell.exe' OR Name = 'pwsh.exe'" |
    Where-Object { $_.CommandLine -like '*AAYS*' -or $_.CommandLine -like '*terrayield*' -or $_.CommandLine -like '*chat_gpt_clone_1*' } |
    Select-Object ProcessId,ParentProcessId,Name,CommandLine |
    Format-List | Out-String | Write-Output
} catch {
  Step "PROCESS_CHECK_ERROR=$($_.Exception.Message)"
}
Step 'PROCESS_CHECK_END'

Step 'FILE_CHECK_BEGIN'
$files = @(
  'AAYS_PORTABLE_TASK_RUNNER_FIXED.ps1',
  'AAYS_START_RUNNER_SINGLE_WINDOW.ps1',
  'AAYS_AUTOPILOT_RUNNER_V5.ps1',
  'ai-tasks/current-task.json',
  'ai-tasks/.last-task-id'
)
foreach ($rel in $files) {
  $p = Join-Path $BridgeRoot $rel
  if (Test-Path $p) { Step "FOUND=$rel" } else { Step "MISSING=$rel" }
}
Step 'FILE_CHECK_END'

Step 'GIT_STATUS_BEGIN'
try {
  Push-Location $BridgeRoot
  git status --short 2>&1 | Out-String | Write-Output
  git rev-parse --abbrev-ref HEAD 2>&1 | Out-String | ForEach-Object { Step ("GIT_BRANCH=" + $_.Trim()) }
  git rev-parse HEAD 2>&1 | Out-String | ForEach-Object { Step ("GIT_HEAD=" + $_.Trim()) }
  Pop-Location
} catch {
  try { Pop-Location } catch {}
  Step "GIT_STATUS_ERROR=$($_.Exception.Message)"
}
Step 'GIT_STATUS_END'

Step 'PROJECT_CHECK_BEGIN'
if (Test-Path $ProjectRoot) { Step "PROJECT_ROOT_FOUND=$ProjectRoot" } else { Step "PROJECT_ROOT_MISSING=$ProjectRoot" }
if (Test-Path (Join-Path $ProjectRoot 'future_growth')) { Step 'FUTURE_GROWTH_FOUND=true' } else { Step 'FUTURE_GROWTH_FOUND=false' }
Step 'PROJECT_CHECK_END'

$LocalReport = Join-Path $ResultDir "$TaskId.local-report.md"
$lines = @(
  '# TerraYield Bridge Status Push Probe',
  '',
  "Task: $TaskId",
  "Generated: $(Get-Date -Format s)",
  "BridgeRoot: $BridgeRoot",
  "ProjectRoot: $ProjectRoot",
  '',
  'Status: completed',
  '',
  'TASK_COMPLETION=100/100',
  'TERRAYIELD_TASK_DONE'
)
$lines | Set-Content -Path $LocalReport -Encoding UTF8
Step "LOCAL_REPORT=$LocalReport"
Step 'TASK_COMPLETION=100/100'
Step 'TERRAYIELD_TASK_DONE'
exit 0
