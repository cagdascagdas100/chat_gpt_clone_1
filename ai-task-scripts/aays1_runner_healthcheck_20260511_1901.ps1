$ErrorActionPreference = 'Continue'

$TaskId = 'aays1-runner-healthcheck-20260511-1901'
$BridgeRoot = 'C:\AAYS1_GITHUB_BRIDGE\chat_gpt_clone_1'
$ResultsDir = Join-Path $BridgeRoot 'ai-results'
$HeartbeatDir = Join-Path $BridgeRoot 'ai-heartbeat'

New-Item -ItemType Directory -Force -Path $ResultsDir | Out-Null
New-Item -ItemType Directory -Force -Path $HeartbeatDir | Out-Null

$Now = Get-Date -Format 'yyyy-MM-ddTHH:mm:ss'
$Result = [ordered]@{
  task_id = $TaskId
  status = 'completed'
  message = 'Runner healthcheck executed from PowerShell.'
  checked_at = $Now
  computer_name = $env:COMPUTERNAME
  username = $env:USERNAME
  powershell_version = $PSVersionTable.PSVersion.ToString()
  bridge_root = $BridgeRoot
}

$ResultPath = Join-Path $ResultsDir ($TaskId + '.result.json')
$Result | ConvertTo-Json -Depth 5 | Set-Content -Path $ResultPath -Encoding UTF8

$HeartbeatPath = Join-Path $HeartbeatDir 'aays1-healthcheck.md'
@(
  '# AAYS1 Runner Healthcheck',
  '',
  '- Status: completed',
  ('- Task ID: ' + $TaskId),
  ('- Checked at: ' + $Now),
  ('- Computer: ' + $env:COMPUTERNAME),
  ('- User: ' + $env:USERNAME)
) | Set-Content -Path $HeartbeatPath -Encoding UTF8

Write-Host 'AAYS1_RUNNER_HEALTHCHECK_COMPLETE'
exit 0
