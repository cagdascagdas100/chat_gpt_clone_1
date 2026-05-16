$ErrorActionPreference = "Continue"

$RunnerScript = $MyInvocation.MyCommand.Path
$RunnerRoot = Split-Path -Parent $RunnerScript
$Inbox = Join-Path $RunnerRoot "inbox"
$Done = Join-Path $RunnerRoot "done"
$Failed = Join-Path $RunnerRoot "failed"
$Outputs = Join-Path $RunnerRoot "outputs"
$Log = Join-Path $Outputs "LOCAL_RUNNER.log"
$Lock = Join-Path $RunnerRoot "AAYS_LOCAL_RUNNER.lock"

New-Item -ItemType Directory -Force -Path $Inbox, $Done, $Failed, $Outputs | Out-Null

function Write-RunnerLog {
  param([string]$Message)
  $line = "$(Get-Date -Format o) $Message"
  Add-Content -LiteralPath $Log -Value $line -Encoding UTF8
  Write-Host $line
}

function Test-ProcessAlive {
  param([int]$PidValue)
  try {
    $p = Get-Process -Id $PidValue -ErrorAction Stop
    return $true
  } catch {
    return $false
  }
}

# Single-runner lock. If a stale lock exists, remove it.
if (Test-Path $Lock) {
  try {
    $existing = Get-Content -LiteralPath $Lock -ErrorAction Stop | Select-Object -First 1
    $existingPid = [int]$existing
    if (Test-ProcessAlive $existingPid) {
      Write-RunnerLog "RUNNER_ALREADY_ACTIVE pid=$existingPid"
      return
    }
  } catch {}
  Remove-Item -LiteralPath $Lock -Force -ErrorAction SilentlyContinue
}

$PID | Set-Content -LiteralPath $Lock -Encoding ASCII

try {
  Write-RunnerLog "AAYS_LOCAL_RUNNER_STARTED"

  while ($true) {
    $task = Get-ChildItem -LiteralPath $Inbox -Filter "*.ps1" -File -ErrorAction SilentlyContinue |
      Sort-Object Name |
      Select-Object -First 1

    if (-not $task) {
      Start-Sleep -Seconds 5
      continue
    }

    $stamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $safeName = [IO.Path]::GetFileNameWithoutExtension($task.Name)
    $outDir = Join-Path $Outputs "${stamp}_${safeName}"
    New-Item -ItemType Directory -Force -Path $outDir | Out-Null

    $stdout = Join-Path $outDir "stdout.log"
    $stderr = Join-Path $outDir "stderr.log"
    $status = Join-Path $outDir "status.txt"

    Write-RunnerLog "TASK_STARTED name=$($task.Name)"

    try {
      $taskPath = $task.FullName
      powershell -NoProfile -ExecutionPolicy Bypass -File $taskPath *> $stdout
      $exitCode = $LASTEXITCODE

      if ($exitCode -eq 0) {
        "exit_code=0" | Set-Content -LiteralPath $status -Encoding UTF8
        Move-Item -LiteralPath $taskPath -Destination (Join-Path $Done $task.Name) -Force
        Write-RunnerLog "TASK_SUCCESS name=$($task.Name) output=$outDir"
      } else {
        "exit_code=$exitCode" | Set-Content -LiteralPath $status -Encoding UTF8
        Move-Item -LiteralPath $taskPath -Destination (Join-Path $Failed $task.Name) -Force
        Write-RunnerLog "TASK_FAILED name=$($task.Name) exit=$exitCode output=$outDir"
      }
    } catch {
      "runner_exception=$($_.Exception.Message)" | Set-Content -LiteralPath $status -Encoding UTF8
      try { Move-Item -LiteralPath $task.FullName -Destination (Join-Path $Failed $task.Name) -Force } catch {}
      Write-RunnerLog "RUNNER_ERROR $($_.Exception.Message)"
    }
  }
} finally {
  Remove-Item -LiteralPath $Lock -Force -ErrorAction SilentlyContinue
}
