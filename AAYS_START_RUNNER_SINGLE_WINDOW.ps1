$ErrorActionPreference = "Stop"

# Assumption: Bu script sadece AAYS bridge runner icin acilmis fazla PowerShell islemlerini temizler.
# Assumption: Bundan sonra runner bu ayni PowerShell penceresinde calisir; yeni status panel veya runner penceresi acmaz.
# Assumption: Bridge root C:\AAYS_GITHUB_BRIDGE_CLEAN olarak kullanilir.

$BridgeRoot = if ($env:AAYS_BRIDGE_ROOT) { $env:AAYS_BRIDGE_ROOT } else { "C:\AAYS_GITHUB_BRIDGE_CLEAN" }
$RunnerScript = Join-Path $BridgeRoot "AAYS_PORTABLE_TASK_RUNNER_FIXED.ps1"
$ConfigScript = Join-Path $BridgeRoot "AAYS_TASK_BRIDGE_CONFIG.ps1"
$StopLog = Join-Path $BridgeRoot "ai-runner-logs\single-window-startup.log"

function Write-StartupLog([string]$Text) {
  $line = "[" + (Get-Date -Format "s") + "] " + $Text
  Write-Host $line
  try {
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $StopLog) | Out-Null
    Add-Content -Encoding UTF8 -Path $StopLog -Value $line
  } catch {}
}

if (-not (Test-Path $BridgeRoot)) {
  throw "BridgeRoot bulunamadi: $BridgeRoot"
}

Set-Location $BridgeRoot

if (Test-Path $ConfigScript) { . $ConfigScript }

Write-StartupLog "SINGLE_WINDOW_START_BEGIN"
Write-StartupLog "BridgeRoot=$BridgeRoot"

Write-StartupLog "Git sync begin"
git fetch origin main 2>&1 | Out-String | Write-StartupLog
git reset --hard origin/main 2>&1 | Out-String | Write-StartupLog
Write-StartupLog "Git sync done"

if (-not (Test-Path $RunnerScript)) {
  throw "Runner script bulunamadi: $RunnerScript"
}

New-Item -ItemType Directory -Force -Path `
  (Join-Path $BridgeRoot "ai-tasks"), `
  (Join-Path $BridgeRoot "ai-task-scripts"), `
  (Join-Path $BridgeRoot "ai-results"), `
  (Join-Path $BridgeRoot "ai-heartbeat"), `
  (Join-Path $BridgeRoot "ai-runner-logs") | Out-Null

Write-StartupLog "Cleaning duplicate AAYS runner/status PowerShell processes"

$currentPid = $PID
$patterns = @(
  "AAYS_PORTABLE_TASK_RUNNER_FIXED.ps1",
  "AAYS_TASK_STATUS_PANEL_FIXED.ps1",
  "AAYS_START_RUNNER_SINGLE_WINDOW.ps1"
)

$killed = 0
try {
  $procs = Get-CimInstance Win32_Process -Filter "Name = 'powershell.exe' OR Name = 'pwsh.exe'" | Where-Object {
    $_.ProcessId -ne $currentPid -and (
      ($_.CommandLine -like "*AAYS_PORTABLE_TASK_RUNNER_FIXED.ps1*") -or
      ($_.CommandLine -like "*AAYS_TASK_STATUS_PANEL_FIXED.ps1*") -or
      ($_.CommandLine -like "*AAYS_START_RUNNER_SINGLE_WINDOW.ps1*")
    )
  }

  foreach ($p in $procs) {
    Write-StartupLog ("Stopping duplicate pid=" + $p.ProcessId + " cmd=" + $p.CommandLine)
    Stop-Process -Id $p.ProcessId -Force -ErrorAction SilentlyContinue
    $killed++
  }
} catch {
  Write-StartupLog ("Duplicate cleanup warning: " + $_.Exception.Message)
}

Write-StartupLog ("Duplicate processes stopped=" + $killed)

$HeartbeatFile = Join-Path $BridgeRoot "ai-heartbeat\portable-runner.md"
$body = @"
# AAYS Portable Task Runner Fixed

Time: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")
Status: starting_single_window
TaskId:
BridgeRoot: $BridgeRoot
ProjectRoot: $env:AAYS_PROJECT_ROOT
TaskFile: $(Join-Path $BridgeRoot "ai-tasks\current-task.json")
RunnerLog: $StopLog
Message: Single-window runner start requested. No extra PowerShell windows will be opened.
GitRecovery: enabled
SafeScriptOnly: enabled
"@
Set-Content -Encoding UTF8 -Path $HeartbeatFile -Value $body

Write-StartupLog "Starting runner in THIS window. Do not close this PowerShell window."
Write-Host ""
Write-Host "AAYS runner artik bu pencerede calisacak. Yeni PowerShell penceresi acilmayacak." -ForegroundColor Green
Write-Host "Bu pencereyi kapatma. ChatGPT tarafinda 'devam et' yazmaya devam edebilirsin." -ForegroundColor Green
Write-Host ""

powershell -NoProfile -ExecutionPolicy Bypass -File $RunnerScript
