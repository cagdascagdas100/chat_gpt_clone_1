$ErrorActionPreference = 'Continue'

$TaskId = 'terrayield-057-remote-control-path-lock'
$ActiveBridgeRoot = 'C:\Users\cagda\Documents\chat_gpt_clone_1'
$ProjectRoot = 'C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence'
$ResultDir = Join-Path $ActiveBridgeRoot 'ai-results'
$HeartbeatDir = Join-Path $ActiveBridgeRoot 'ai-heartbeat'
$StateDir = Join-Path $ActiveBridgeRoot 'ai-runner-state'

function Step([string]$Text) {
  Write-Output ('[' + (Get-Date -Format 's') + '] ' + $Text)
}

New-Item -ItemType Directory -Force -Path $ResultDir,$HeartbeatDir,$StateDir | Out-Null

Step "TASK=$TaskId"
Step 'MODE=remote_control_path_lock'
Step "ACTIVE_BRIDGE_ROOT=$ActiveBridgeRoot"
Step "PROJECT_ROOT=$ProjectRoot"
Step 'DECISION=Use the currently alive V5 bridge root as the operational canonical runner path until a separate local maintenance window is available.'

$Status = 'completed'
$Warnings = New-Object System.Collections.Generic.List[string]

if (-not (Test-Path $ActiveBridgeRoot)) { $Warnings.Add("Active bridge root missing: $ActiveBridgeRoot") | Out-Null; $Status = 'warning' }
if (-not (Test-Path $ProjectRoot)) { $Warnings.Add("Project root missing: $ProjectRoot") | Out-Null; $Status = 'warning' }

try {
  Push-Location $ActiveBridgeRoot
  $GitStatus = git status --short 2>&1 | Out-String
  $GitHead = git rev-parse HEAD 2>&1 | Out-String
  Pop-Location
} catch {
  try { Pop-Location } catch {}
  $GitStatus = 'git status check failed: ' + $_.Exception.Message
  $GitHead = ''
  $Warnings.Add('Git status check failed') | Out-Null
  $Status = 'warning'
}

$ControlPolicy = @(
  '# AAYS Remote Control Path Lock',
  '',
  "status: $Status",
  "task_id: $TaskId",
  "checked_at: $(Get-Date -Format s)",
  "active_bridge_root: $ActiveBridgeRoot",
  "project_root: $ProjectRoot",
  '',
  'policy:',
  '- Treat the currently alive V5 runner path as the operational control root.',
  '- ChatGPT should continue by updating GitHub ai-task-scripts and ai-tasks/current-task.json.',
  '- Do not require repeated local PowerShell commands while this runner keeps processing tasks.',
  '- Defer root migration to a separate maintenance task only after long jobs are complete.',
  '',
  'warnings:',
  (($Warnings | ForEach-Object { '- ' + $_ }) -join "`n"),
  '',
  'git_head:',
  $GitHead.Trim(),
  '',
  'git_status:',
  '```text',
  $GitStatus,
  '```'
) -join "`n"

$PolicyPath = Join-Path $HeartbeatDir 'remote-control-path-lock.md'
$ReportPath = Join-Path $ResultDir "$TaskId.report.md"
$ControlPolicy | Set-Content -Path $PolicyPath -Encoding UTF8
$ControlPolicy | Set-Content -Path $ReportPath -Encoding UTF8

Step "POLICY_PATH=$PolicyPath"
Step "REPORT_PATH=$ReportPath"
Step 'PLAN_PROGRESS_PERCENT=58'
Step 'NEXT_EXPECTED_ACTION=queue_long_contractor_or_estate_agent_job_using_active_v5_runner'
Step 'TASK_COMPLETION=100/100'
Step 'TERRAYIELD_TASK_DONE'
exit 0
