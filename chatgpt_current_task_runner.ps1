$ErrorActionPreference = "Continue"

$Bridge = "C:\AAYS_GITHUB_BRIDGE_CLEAN2"
$TaskPath = Join-Path $Bridge "ai-tasks\current-task.json"
$ScriptsDir = Join-Path $Bridge "ai-task-scripts"
$HeartbeatDir = Join-Path $Bridge "ai-heartbeat"
$ResultsDir = Join-Path $Bridge "ai-results"
$MarkerPath = Join-Path $Bridge "ai-tasks\.direct-autopilot-last-task-id"

New-Item -ItemType Directory -Force $HeartbeatDir, $ResultsDir | Out-Null

while ($true) {
  try {
    cd $Bridge
    git pull | Out-Null

    $Task = Get-Content $TaskPath -Raw | ConvertFrom-Json
    $TaskId = [string]$Task.id
    $ScriptPath = Join-Path $ScriptsDir ([string]$Task.script_path)

    $LastTask = ""
    if (Test-Path $MarkerPath) {
      $LastTask = (Get-Content $MarkerPath -Raw).Trim()
    }

    if ($TaskId -and ($TaskId -ne $LastTask)) {
      Write-Host "Yeni task calisiyor: $TaskId"

      if (Test-Path $ScriptPath) {
        powershell -NoProfile -ExecutionPolicy Bypass -File $ScriptPath
        Set-Content -LiteralPath $MarkerPath -Encoding UTF8 -Value $TaskId

        git add ai-heartbeat ai-results ready_to_sell_accuracy_runs ai-tasks 2>$null
        git commit -m "Add runner outputs for $TaskId" 2>$null
        git push 2>$null
      } else {
        Write-Host "Script bulunamadi: $ScriptPath"
      }
    }
  } catch {
    Write-Host ("Runner hata: " + $_.Exception.Message)
  }

  Start-Sleep -Seconds 30
}
