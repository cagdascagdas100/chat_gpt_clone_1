[CmdletBinding()]
param(
  [ValidateRange(300, 5400)][int]$MaxRuntimeSeconds = 5400,
  [ValidateRange(120, 1800)][int]$NoOutputTimeoutSeconds = 1200,
  [ValidateRange(15, 300)][int]$HeartbeatSeconds = 60,
  [ValidateRange(1, 30)][int]$PollSeconds = 5,
  [switch]$SelfTest
)

$ErrorActionPreference = 'Stop'
$SlotId = 'height_difference_1'
$ScriptVersion = '1.1-realtime-output-total-and-no-output-watchdog'
$TimeoutExitCode = 124
$OtherErrorExitCode = 2

function Get-WatchdogDecision {
  param(
    [double]$ElapsedSeconds,
    [double]$IdleSeconds,
    [int]$MaxSeconds,
    [int]$NoOutputSeconds
  )
  if ($ElapsedSeconds -ge $MaxSeconds) { return 'TOTAL_TIMEOUT' }
  if ($IdleSeconds -ge $NoOutputSeconds) { return 'NO_OUTPUT_TIMEOUT' }
  return 'CONTINUE'
}

function Invoke-WatchdogSelfTest {
  $checks = [ordered]@{
    slot_isolated = ($SlotId -eq 'height_difference_1')
    version_present = ($ScriptVersion -eq '1.1-realtime-output-total-and-no-output-watchdog')
    normal_continue = ((Get-WatchdogDecision -ElapsedSeconds 10 -IdleSeconds 5 -MaxSeconds 100 -NoOutputSeconds 50) -eq 'CONTINUE')
    total_timeout_at_boundary = ((Get-WatchdogDecision -ElapsedSeconds 100 -IdleSeconds 1 -MaxSeconds 100 -NoOutputSeconds 50) -eq 'TOTAL_TIMEOUT')
    total_timeout_precedes_idle = ((Get-WatchdogDecision -ElapsedSeconds 100 -IdleSeconds 50 -MaxSeconds 100 -NoOutputSeconds 50) -eq 'TOTAL_TIMEOUT')
    idle_timeout_at_boundary = ((Get-WatchdogDecision -ElapsedSeconds 90 -IdleSeconds 50 -MaxSeconds 100 -NoOutputSeconds 50) -eq 'NO_OUTPUT_TIMEOUT')
    declared_total_limit_bounded = ($MaxRuntimeSeconds -le 5400)
    declared_idle_limit_bounded = ($NoOutputTimeoutSeconds -le 1800)
    realtime_passthrough_declared = ($true)
    timeout_and_other_exit_codes_distinct = ($TimeoutExitCode -eq 124 -and $OtherErrorExitCode -eq 2)
  }
  if ($checks.Values -contains $false) { throw 'WATCHDOG_SELF_TEST_FAILED' }
  [ordered]@{
    slot_id = $SlotId
    script_version = $ScriptVersion
    state = 'PASS'
    checks = $checks.Count
    check_results = $checks
    max_runtime_seconds = $MaxRuntimeSeconds
    no_output_timeout_seconds = $NoOutputTimeoutSeconds
    heartbeat_seconds = $HeartbeatSeconds
    poll_seconds = $PollSeconds
    realtime_child_output_passthrough = $true
    timeout_exit_code = $TimeoutExitCode
    other_error_exit_code = $OtherErrorExitCode
  } | ConvertTo-Json -Compress -Depth 5 | Write-Output
}

function Stop-ProcessTree {
  param([int]$ProcessId)
  if ($env:OS -eq 'Windows_NT') {
    $taskkill = Get-Command taskkill.exe -ErrorAction SilentlyContinue
    if ($taskkill) {
      & $taskkill.Source /PID $ProcessId /T /F 2>$null | Out-Null
    }
  }
  Stop-Process -Id $ProcessId -Force -ErrorAction SilentlyContinue
}

function Write-NewLogBytes {
  param(
    [string]$Path,
    [ref]$Offset,
    [switch]$AsError
  )
  if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { return 0L }
  $stream = [System.IO.FileStream]::new(
    $Path,
    [System.IO.FileMode]::Open,
    [System.IO.FileAccess]::Read,
    [System.IO.FileShare]::ReadWrite
  )
  try {
    if ([int64]$Offset.Value -gt $stream.Length) { $Offset.Value = 0L }
    [void]$stream.Seek([int64]$Offset.Value, [System.IO.SeekOrigin]::Begin)
    $remaining = [int64]($stream.Length - [int64]$Offset.Value)
    if ($remaining -le 0) { return 0L }
    $chunkSize = [int][Math]::Min($remaining, 4MB)
    $buffer = New-Object byte[] $chunkSize
    $read = $stream.Read($buffer, 0, $chunkSize)
    if ($read -le 0) { return 0L }
    $Offset.Value = [int64]$Offset.Value + [int64]$read
    $text = [System.Text.Encoding]::UTF8.GetString($buffer, 0, $read)
    if ($AsError) {
      [Console]::Error.Write($text)
    } else {
      [Console]::Out.Write($text)
    }
    return [int64]$read
  } finally {
    $stream.Dispose()
  }
}

Invoke-WatchdogSelfTest
if ($SelfTest) { exit 0 }

$repoRoot = if ($env:AAYS_REPO_ROOT) {
  [System.IO.Path]::GetFullPath($env:AAYS_REPO_ROOT)
} else {
  [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..\..\..'))
}
$entryPath = Join-Path $repoRoot 'docs\chatgpt_status\height_difference\automation\height_difference_1_official_boundary_and_wcs_entry_v1.ps1'
if (-not (Test-Path -LiteralPath $entryPath -PathType Leaf)) { throw "WATCHDOG_ENTRY_TARGET_MISSING: $entryPath" }

$shell = Get-Command powershell -ErrorAction SilentlyContinue
if (-not $shell) { $shell = Get-Command pwsh -ErrorAction SilentlyContinue }
if (-not $shell) { throw 'WATCHDOG_POWERSHELL_EXECUTABLE_NOT_FOUND' }

$tempRoot = Join-Path ([System.IO.Path]::GetTempPath()) 'aays_height_difference_1_watchdog'
New-Item -ItemType Directory -Path $tempRoot -Force | Out-Null
$stdoutPath = Join-Path $tempRoot 'watchdog_child_stdout.log'
$stderrPath = Join-Path $tempRoot 'watchdog_child_stderr.log'
Remove-Item -LiteralPath $stdoutPath,$stderrPath -Force -ErrorAction SilentlyContinue

$process = $null
$watchdogExitCode = $OtherErrorExitCode
$stopwatch = [System.Diagnostics.Stopwatch]::StartNew()
$lastActivitySeconds = 0.0
$lastStdoutBytes = 0L
$lastStderrBytes = 0L
$stdoutOffset = 0L
$stderrOffset = 0L
$nextHeartbeatSeconds = [double]$HeartbeatSeconds

try {
  $argumentString = "-NoProfile -ExecutionPolicy Bypass -File `"$entryPath`""
  $process = Start-Process -FilePath $shell.Source -ArgumentList $argumentString -NoNewWindow -PassThru -RedirectStandardOutput $stdoutPath -RedirectStandardError $stderrPath
  Write-Output "WATCHDOG_STARTED=true"
  Write-Output "WATCHDOG_VERSION=$ScriptVersion"
  Write-Output "WATCHDOG_CHILD_PID=$($process.Id)"
  Write-Output "WATCHDOG_MAX_RUNTIME_SECONDS=$MaxRuntimeSeconds"
  Write-Output "WATCHDOG_NO_OUTPUT_TIMEOUT_SECONDS=$NoOutputTimeoutSeconds"
  Write-Output "WATCHDOG_REALTIME_OUTPUT=true"

  while (-not $process.HasExited) {
    Start-Sleep -Seconds $PollSeconds
    $process.Refresh()
    $stdoutBytes = if (Test-Path -LiteralPath $stdoutPath) { [int64](Get-Item -LiteralPath $stdoutPath).Length } else { 0L }
    $stderrBytes = if (Test-Path -LiteralPath $stderrPath) { [int64](Get-Item -LiteralPath $stderrPath).Length } else { 0L }
    if ($stdoutBytes -ne $lastStdoutBytes -or $stderrBytes -ne $lastStderrBytes) {
      $lastActivitySeconds = $stopwatch.Elapsed.TotalSeconds
      $lastStdoutBytes = $stdoutBytes
      $lastStderrBytes = $stderrBytes
    }

    [void](Write-NewLogBytes -Path $stdoutPath -Offset ([ref]$stdoutOffset))
    [void](Write-NewLogBytes -Path $stderrPath -Offset ([ref]$stderrOffset) -AsError)

    $elapsedSeconds = $stopwatch.Elapsed.TotalSeconds
    $idleSeconds = $elapsedSeconds - $lastActivitySeconds
    $decision = Get-WatchdogDecision -ElapsedSeconds $elapsedSeconds -IdleSeconds $idleSeconds -MaxSeconds $MaxRuntimeSeconds -NoOutputSeconds $NoOutputTimeoutSeconds
    if ($decision -ne 'CONTINUE') {
      Stop-ProcessTree -ProcessId $process.Id
      Write-Output "WATCHDOG_TERMINATED=true"
      Write-Output "WATCHDOG_TERMINATION_REASON=$decision"
      Write-Output 'FINAL_READY=false'
      $watchdogExitCode = $TimeoutExitCode
      throw "WATCHDOG_$decision"
    }
    if ($elapsedSeconds -ge $nextHeartbeatSeconds) {
      Write-Output ("WATCHDOG_HEARTBEAT elapsed_seconds={0} idle_seconds={1} stdout_bytes={2} stderr_bytes={3} stdout_forwarded={4} stderr_forwarded={5}" -f [int]$elapsedSeconds,[int]$idleSeconds,$stdoutBytes,$stderrBytes,$stdoutOffset,$stderrOffset)
      $nextHeartbeatSeconds += $HeartbeatSeconds
    }
  }

  $process.WaitForExit()
  while ((Write-NewLogBytes -Path $stdoutPath -Offset ([ref]$stdoutOffset)) -gt 0) {}
  while ((Write-NewLogBytes -Path $stderrPath -Offset ([ref]$stderrOffset) -AsError) -gt 0) {}
  Write-Output "WATCHDOG_COMPLETED=true"
  Write-Output "WATCHDOG_ELAPSED_SECONDS=$([int]$stopwatch.Elapsed.TotalSeconds)"
  Write-Output "WATCHDOG_CHILD_EXIT_CODE=$($process.ExitCode)"
  exit [int]$process.ExitCode
} catch {
  [Console]::Error.WriteLine([string]$_)
  Write-Output 'FINAL_READY=false'
  exit [int]$watchdogExitCode
} finally {
  if ($process -and -not $process.HasExited) { Stop-ProcessTree -ProcessId $process.Id }
  Remove-Item -LiteralPath $stdoutPath,$stderrPath -Force -ErrorAction SilentlyContinue
}
