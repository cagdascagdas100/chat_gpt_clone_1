$ErrorActionPreference = "Continue"

$ConfigPath = Join-Path $PSScriptRoot "AAYS_TASK_BRIDGE_CONFIG.ps1"
if (Test-Path $ConfigPath) { . $ConfigPath }

$BridgeRoot = if ($env:AAYS_BRIDGE_ROOT) { $env:AAYS_BRIDGE_ROOT } else { $PSScriptRoot }
$TaskFile = Join-Path $BridgeRoot "ai-tasks\current-task.json"
$LastTaskFile = Join-Path $BridgeRoot "ai-tasks\.last-task-id"
$HeartbeatFile = Join-Path $BridgeRoot "ai-heartbeat\portable-runner.md"
$ResultDir = Join-Path $BridgeRoot "ai-results"
$LogDir = Join-Path $BridgeRoot "ai-runner-logs"

function Read-TextSafe([string]$Path, [int]$Tail = 0) {
  try {
    if (-not (Test-Path $Path)) { return "MISSING: $Path" }
    if ($Tail -gt 0) { return (Get-Content -Path $Path -Tail $Tail -Encoding UTF8 | Out-String) }
    return (Get-Content -Path $Path -Raw -Encoding UTF8)
  } catch {
    return "READ_ERROR: $Path :: $($_.Exception.Message)"
  }
}

function Get-LatestFile([string]$Path, [string]$Filter) {
  try {
    if (-not (Test-Path $Path)) { return $null }
    return Get-ChildItem -Path $Path -Filter $Filter -File -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1
  } catch {
    return $null
  }
}

while ($true) {
  Clear-Host
  Write-Host "AAYS / TerraYield Task Status Panel" -ForegroundColor Cyan
  Write-Host "==================================" -ForegroundColor Cyan
  Write-Host "Time:       $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
  Write-Host "BridgeRoot: $BridgeRoot"
  Write-Host "TaskFile:   $TaskFile"
  Write-Host ""

  Write-Host "CURRENT TASK" -ForegroundColor Yellow
  Write-Host "------------" -ForegroundColor Yellow
  if (Test-Path $TaskFile) {
    try {
      $task = Get-Content -Raw -Encoding UTF8 $TaskFile | ConvertFrom-Json
      Write-Host "Id:       $($task.id)"
      Write-Host "Title:    $($task.title)"
      Write-Host "Progress: $($task.progress)"
      Write-Host "Script:   $($task.script_path)"
      Write-Host "Timeout:  $($task.timeout_seconds)"
    } catch {
      Write-Host "TASK_JSON_ERROR: $($_.Exception.Message)" -ForegroundColor Red
      Write-Host (Read-TextSafe $TaskFile)
    }
  } else {
    Write-Host "No current-task.json yet."
  }

  Write-Host ""
  Write-Host "LAST PROCESSED" -ForegroundColor Yellow
  Write-Host "--------------" -ForegroundColor Yellow
  if (Test-Path $LastTaskFile) {
    Write-Host ((Get-Content -Raw -Encoding UTF8 $LastTaskFile).Trim())
  } else {
    Write-Host "No .last-task-id yet."
  }

  Write-Host ""
  Write-Host "HEARTBEAT" -ForegroundColor Yellow
  Write-Host "---------" -ForegroundColor Yellow
  Write-Host (Read-TextSafe $HeartbeatFile)

  Write-Host ""
  Write-Host "LATEST RESULT" -ForegroundColor Yellow
  Write-Host "-------------" -ForegroundColor Yellow
  $latestResult = Get-LatestFile $ResultDir "*.md"
  if ($latestResult) {
    Write-Host "File: $($latestResult.FullName)"
    Write-Host (Read-TextSafe $latestResult.FullName 80)
  } else {
    Write-Host "No result file yet."
  }

  Write-Host ""
  Write-Host "LATEST RUNNER LOG" -ForegroundColor Yellow
  Write-Host "-----------------" -ForegroundColor Yellow
  $latestLog = Get-LatestFile $LogDir "*.log"
  if ($latestLog) {
    Write-Host "File: $($latestLog.FullName)"
    Write-Host (Read-TextSafe $latestLog.FullName 40)
  } else {
    Write-Host "No runner log yet."
  }

  Write-Host ""
  Write-Host "Refresh: 5 seconds. Leave this window open." -ForegroundColor DarkGray
  Start-Sleep -Seconds 5
}
