[CmdletBinding()]
param(
  [ValidateRange(30,600)][int]$PreflightTimeoutSeconds = 180,
  [ValidateRange(300,7200)][int]$ChainTimeoutSeconds = 5700
)

$ErrorActionPreference = 'Stop'
$rawRoot = [string]$env:AAYS_REPO_ROOT
if ([string]::IsNullOrWhiteSpace($rawRoot)) { throw 'AAYS_REPO_ROOT_REQUIRED' }
$root = [System.IO.Path]::GetFullPath($rawRoot)
if (-not (Test-Path -LiteralPath $root -PathType Container)) { throw 'AAYS_REPO_ROOT_NOT_FOUND' }
if ([string]$env:AAYS_TASK_ID -ne 'height-difference-3-canonical-point-extract-v1-1-20260722') { throw 'AAYS_TASK_ID_MISMATCH' }

$preflightScript = Join-Path $root 'docs\chatgpt_status\height_difference\automation\height_difference_3_runner_preflight_v1.ps1'
$chainScript = Join-Path $root 'docs\chatgpt_status\height_difference\automation\height_difference_3_single_pass_chain_v1.ps1'
$preflightOutput = Join-Path $root 'docs\chatgpt_status\height_difference\runner_outputs\height_difference_3_runner_preflight_latest.json'
$reportPath = Join-Path $root 'docs\chatgpt_status\height_difference\runner_outputs\height_difference_3_outer_watchdog_latest.json'
$websitePath = Join-Path $root 'england_map_web\data\height_difference\height_difference_3_outer_watchdog_latest.json'
$work = Join-Path $root 'docs\chatgpt_status\height_difference\runner_work\height_difference_3_outer_watchdog'
foreach ($path in @($preflightScript,$chainScript)) {
  if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { throw ('REQUIRED_FILE_MISSING:' + $path) }
}
New-Item -ItemType Directory -Force -Path $work | Out-Null

function Write-JsonAtomic([string]$Path,[object]$Payload) {
  $dir = Split-Path -Parent $Path
  New-Item -ItemType Directory -Force -Path $dir | Out-Null
  $tmp = $Path + '.tmp'
  [System.IO.File]::WriteAllText($tmp,($Payload | ConvertTo-Json -Depth 100),[System.Text.UTF8Encoding]::new($false))
  Move-Item -LiteralPath $tmp -Destination $Path -Force
}
function Read-Bounded([string]$Path,[int]$MaxChars=200000) {
  if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { return '' }
  $text = [System.IO.File]::ReadAllText($Path)
  if ($text.Length -gt $MaxChars) { return $text.Substring(0,$MaxChars) + "`n[TRUNCATED]" }
  return $text
}
function Invoke-BoundedPowerShell([string]$Name,[string]$Script,[int]$TimeoutSeconds) {
  $powershell = Get-Command powershell -ErrorAction SilentlyContinue | Select-Object -First 1
  if ($null -eq $powershell) { throw 'POWERSHELL_COMMAND_NOT_AVAILABLE' }
  $stamp = (Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssfffZ')
  $stdout = Join-Path $work ($stamp + '_' + $Name + '.stdout.log')
  $stderr = Join-Path $work ($stamp + '_' + $Name + '.stderr.log')
  $started = (Get-Date).ToUniversalTime()
  $proc = $null
  $timedOut = $false
  $killAttempted = $false
  $killSucceeded = $false
  $exitCode = $null
  try {
    $proc = Start-Process -FilePath $powershell.Source -ArgumentList @('-NoProfile','-NonInteractive','-ExecutionPolicy','Bypass','-File',$Script) -WorkingDirectory $root -NoNewWindow -PassThru -RedirectStandardOutput $stdout -RedirectStandardError $stderr
    $completed = $proc.WaitForExit($TimeoutSeconds * 1000)
    if (-not $completed) {
      $timedOut = $true
      $killAttempted = $true
      $taskkill = Get-Command taskkill.exe -ErrorAction SilentlyContinue
      if ($null -ne $taskkill) {
        & $taskkill.Source /PID $proc.Id /T /F 2>&1 | Out-Null
        $killSucceeded = $true
      } else {
        try { $proc.Kill(); $killSucceeded = $true } catch { $killSucceeded = $false }
      }
      [void]$proc.WaitForExit(15000)
    }
    if ($proc.HasExited) { $exitCode = $proc.ExitCode }
  } finally {
    if ($null -ne $proc) { $proc.Dispose() }
  }
  $completedAt = (Get-Date).ToUniversalTime()
  return [pscustomobject]@{
    name = $Name
    script = $Script.Substring($root.Length).TrimStart('\').Replace('\','/')
    started_at = $started.ToString('yyyy-MM-ddTHH:mm:ss.fffZ')
    completed_at = $completedAt.ToString('yyyy-MM-ddTHH:mm:ss.fffZ')
    duration_seconds = [math]::Round(($completedAt-$started).TotalSeconds,3)
    timeout_seconds = $TimeoutSeconds
    timed_out = $timedOut
    kill_attempted = $killAttempted
    kill_succeeded = $killSucceeded
    exit_code = $exitCode
    stdout = Read-Bounded $stdout
    stderr = Read-Bounded $stderr
    passed = ((-not $timedOut) -and $exitCode -eq 0)
  }
}

$startedAt = (Get-Date).ToUniversalTime()
$rows = @()
$blockers = @()
$state = 'STARTED'
$exitCode = 0
try {
  $preflightStarted = (Get-Date).ToUniversalTime()
  $preflight = Invoke-BoundedPowerShell 'slot_preflight' $preflightScript $PreflightTimeoutSeconds
  $rows += $preflight
  if (-not $preflight.passed) { throw 'RUNNER_PREFLIGHT_PROCESS_FAILED' }
  if (-not (Test-Path -LiteralPath $preflightOutput -PathType Leaf)) { throw 'RUNNER_PREFLIGHT_OUTPUT_MISSING' }
  $item = Get-Item -LiteralPath $preflightOutput
  if ($item.LastWriteTimeUtc -lt $preflightStarted.AddSeconds(-2)) { throw 'RUNNER_PREFLIGHT_OUTPUT_STALE' }
  $preflightDoc = Get-Content -LiteralPath $preflightOutput -Raw | ConvertFrom-Json
  if (-not [bool]$preflightDoc.accepted) { throw 'RUNNER_PREFLIGHT_NOT_ACCEPTED' }
  $chain = Invoke-BoundedPowerShell 'single_pass_chain_v1' $chainScript $ChainTimeoutSeconds
  $rows += $chain
  if (-not $chain.passed) { throw ('SINGLE_PASS_CHAIN_CHILD_FAILED:' + $chain.exit_code) }
  $state = 'OUTER_WATCHDOG_PASS_NONFINAL'
} catch {
  $state = 'OUTER_WATCHDOG_BLOCKED'
  $blockers += $_.Exception.Message
  $exitCode = 5
}
$completedAt = (Get-Date).ToUniversalTime()
$report = [ordered]@{
  schema_version = 1
  slot_id = 'height_difference_3'
  task_id = 'height-difference-3-single-pass-chain-v2-20260723'
  started_at = $startedAt.ToString('yyyy-MM-ddTHH:mm:ss.fffZ')
  completed_at = $completedAt.ToString('yyyy-MM-ddTHH:mm:ss.fffZ')
  duration_seconds = [math]::Round(($completedAt-$startedAt).TotalSeconds,3)
  state = $state
  process_rows = @($rows)
  timeout_count = @($rows | Where-Object { $_.timed_out }).Count
  killed_process_tree_count = @($rows | Where-Object { $_.kill_succeeded }).Count
  preflight_output_exists = (Test-Path -LiteralPath $preflightOutput -PathType Leaf)
  child_watchdog_output_exists = (Test-Path -LiteralPath (Join-Path $root 'docs\chatgpt_status\height_difference\runner_outputs\height_difference_3_execution_watchdog_latest.json') -PathType Leaf)
  child_chain_output_exists = (Test-Path -LiteralPath (Join-Path $root 'docs\chatgpt_status\height_difference\runner_outputs\height_difference_3_chain_orchestration_latest.json') -PathType Leaf)
  blockers = @($blockers | Select-Object -Unique)
  actual_business_data_rows_written = 0
  fake_data = $false
  db_write = $false
  migration = $false
  production_deploy = $false
  final_ready = $false
  output_semantics = 'OUTER_BOUNDED_PREFLIGHT_AND_EXISTING_SINGLE_PASS_CHAIN_NONFINAL'
}
Write-JsonAtomic $reportPath $report
Write-JsonAtomic $websitePath $report
Write-Host ('HEIGHT_DIFFERENCE_3_OUTER_WATCHDOG_STATE=' + $state)
Write-Host ('HEIGHT_DIFFERENCE_3_OUTER_WATCHDOG_STEPS=' + @($rows).Count)
Write-Host 'FINAL_READY=false'
exit $exitCode
