# AAYS 6.1 Security - 069 long watchdog/status sync
# Safe: DB write disabled, production deploy disabled.
$ErrorActionPreference = 'Continue'
$ProgressPreference = 'SilentlyContinue'
$BridgeRoot = 'C:/AAYS_GITHUB_BRIDGE_CLEAN2'
$PageKey = '6.1 Security'
$Start = Get-Date
$RunDir = Join-Path $BridgeRoot 'docs/chatgpt_status/security_069_watchdog'
New-Item -ItemType Directory -Force -Path $RunDir | Out-Null
$Log = Join-Path $RunDir 'HEARTBEAT_SECURITY_069.log'
function Write-HB([string]$Message) {
  $line = "$(Get-Date -Format o) | $Message"
  Add-Content -Path $Log -Value $line
  Write-Host $line
}
function Update-Status([string]$RunnerMessage,[string]$Status='running') {
  $helper = Join-Path $BridgeRoot 'ai-task-scripts/update_chatgpt_status.ps1'
  if (Test-Path $helper) {
    & $helper -PageKey $PageKey -ActiveTask 'auto-6-security-long-watchdog-069-20260521' -Status $Status -OverallProgress 95 -WaitMinutes '35-45' -NextCommand 'devam et' -RunnerStatus 'running' -RunnerMessage $RunnerMessage -Blocker '' -LastMessageText 'Devam et - uzun watchdog işleri ve web status güncellemesi' -DbWrite:$false -ProductionDeploy:$false
  } else {
    Write-HB 'status helper missing; cannot update shared status through helper'
  }
}
Write-HB 'Security 069 watchdog started; no DB write, no production deploy.'
Update-Status 'Security 069 watchdog started; checking runner/current-task/status files and keeping page status fresh.' 'running'
$files = @('ai-tasks/current-task.json','docs/chatgpt_status/multi_page_status.json','docs/chatgpt_status/status.md','docs/chatgpt_status/index.html')
foreach ($rel in $files) {
  $p = Join-Path $BridgeRoot $rel
  if (Test-Path $p) { Write-HB "found $rel lastWrite=$((Get-Item $p).LastWriteTime)" } else { Write-HB "missing $rel" }
}
$End = $Start.AddMinutes(42)
$cycle = 0
while ((Get-Date) -lt $End) {
  $cycle++
  $procs = Get-Process | Where-Object { $_.ProcessName -match 'powershell|pwsh|python|node|cmd' } | Measure-Object
  Write-HB "cycle=$cycle active_interesting_processes=$($procs.Count)"
  if (($cycle % 3) -eq 0) {
    Update-Status "Security 069 watchdog cycle $cycle active; existing runner/processes watched without duplicate start." 'running'
  }
  Start-Sleep -Seconds 180
}
Update-Status 'Security 069 watchdog completed; ready for next devam et.' 'polling'
Write-HB 'Security 069 watchdog completed.'
exit 0
