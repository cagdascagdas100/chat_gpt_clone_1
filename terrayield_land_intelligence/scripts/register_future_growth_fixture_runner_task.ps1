[CmdletBinding()]
param(
  [string]$ProjectRoot = "C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence",
  [string]$BridgeRoot = "C:\AAYS1_GITHUB_BRIDGE\chat_gpt_clone_1",
  [switch]$CopyScriptToBridge = $true
)

$ErrorActionPreference = "Stop"

$localScriptPath = Join-Path $ProjectRoot "scripts\terrayield_084_future_growth_all_fixture.ps1"
$bridgeTaskScriptsDir = Join-Path $BridgeRoot "ai-task-scripts"
$bridgeTaskQueuePath = Join-Path $BridgeRoot "ai-tasks\aays1-current-task.json"
$bridgeScriptPath = Join-Path $bridgeTaskScriptsDir "terrayield_084_future_growth_all_fixture.ps1"

if (-not (Test-Path -LiteralPath $localScriptPath)) {
  throw "missing_local_script: $localScriptPath"
}

if ($CopyScriptToBridge) {
  if (-not (Test-Path -LiteralPath $bridgeTaskScriptsDir)) {
    New-Item -ItemType Directory -Force -Path $bridgeTaskScriptsDir | Out-Null
  }
  Copy-Item -LiteralPath $localScriptPath -Destination $bridgeScriptPath -Force
}

$task = @{
  id = "terrayield-084-future-growth-all-fixture"
  title = "TerraYield Future Growth Fixture All Pipeline"
  progress = 92
  working_directory = $BridgeRoot
  timeout_seconds = 1800
  created_by = "Codex"
  script_path = "terrayield_084_future_growth_all_fixture.ps1"
  note = "Run future-growth:all --mode fixture and frontend layer+popup smoke, then write sanitized audit."
}

$taskDir = Split-Path -Parent $bridgeTaskQueuePath
if (-not (Test-Path -LiteralPath $taskDir)) {
  New-Item -ItemType Directory -Force -Path $taskDir | Out-Null
}
($task | ConvertTo-Json -Depth 6) | Out-File -FilePath $bridgeTaskQueuePath -Encoding UTF8

Write-Output "bridge_script_path=$bridgeScriptPath"
Write-Output "task_queue_path=$bridgeTaskQueuePath"
Write-Output "task_id=$($task.id)"
Write-Output "status=queued"
