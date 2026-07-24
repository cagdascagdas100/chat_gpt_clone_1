[CmdletBinding()]
param(
  [ValidateSet("Start", "Stop", "Restart", "Status", "Preflight", "FixtureTest")]
  [string]$Action = "Start",
  [int]$StopTimeoutSeconds = 120
)

$ErrorActionPreference = "Stop"
$root = [System.IO.Path]::GetFullPath($PSScriptRoot).TrimEnd("\")
$identityPath = Join-Path $root ".aays_portable_identity.json"
$coordinator = Join-Path $root "AAYS_ADAPTIVE_15_WORKER_COORDINATOR.py"
$recoverySupervisor = Join-Path $root "AAYS_21_SLOT_RECOVERY_SUPERVISOR.py"
$logRoot = Join-Path $root "logs\adaptive_v3"
$stdout = Join-Path $logRoot "coordinator.out.log"
$stderr = Join-Path $logRoot "coordinator.err.log"

if (-not (Test-Path -LiteralPath $identityPath -PathType Leaf)) { throw "PORTABLE_IDENTITY_MISSING: $identityPath" }
if (-not (Test-Path -LiteralPath $coordinator -PathType Leaf)) { throw "COORDINATOR_SCRIPT_MISSING: $coordinator" }
if (-not (Test-Path -LiteralPath $recoverySupervisor -PathType Leaf)) { throw "RECOVERY_SUPERVISOR_MISSING: $recoverySupervisor" }
$identity = Get-Content -LiteralPath $identityPath -Raw | ConvertFrom-Json
if ($identity.portable_product -ne "AAYS_TerraYield" -or $identity.schema_version -ne 2) { throw "PORTABLE_IDENTITY_INVALID" }
if ([int]$identity.architecture_version -ne 3) { throw "PORTABLE_IDENTITY_ARCHITECTURE_MUST_BE_3" }
if ($identity.relative_launcher_path -ne "RUN_AAYS_ADAPTIVE_15_WORKER.cmd") { throw "PORTABLE_IDENTITY_LAUNCHER_MISMATCH" }
New-Item -ItemType Directory -Force -Path $logRoot | Out-Null

$publisherRepo = Join-Path $root ([string]$identity.relative_repo_path)
$worktreeRoot = Join-Path $root ([string]$identity.relative_worktree_root)
$portableGit = Join-Path $root "runtime\git\cmd\git.exe"
$systemGit = Join-Path $env:ProgramFiles "Git\mingw64\bin\git.exe"
if (Test-Path -LiteralPath $systemGit -PathType Leaf) { $portableGit = $systemGit }
$portableGitConfig = Join-Path $root "runtime\gitconfig.aays.portable"
$stateRoot = Join-Path $root "state"
$manualStopPath = Join-Path $stateRoot "manual_stop.requested.json"
$writeProbe = Join-Path $stateRoot ("write_probe_" + [guid]::NewGuid().ToString("N") + ".tmp")
$runtimeRoot = Join-Path $root "runtime"
$tempRoot = Join-Path $runtimeRoot "tmp"
$cacheRoot = Join-Path $runtimeRoot "cache"
$homeRoot = Join-Path $runtimeRoot "home"
$pycacheRoot = Join-Path $runtimeRoot "pycache"
$pythonUserRoot = Join-Path $runtimeRoot "python-user"

@($stateRoot, $tempRoot, $cacheRoot, $homeRoot, $pycacheRoot, $pythonUserRoot) | ForEach-Object {
  New-Item -ItemType Directory -Force -Path $_ | Out-Null
}
try {
  [System.IO.File]::WriteAllText($writeProbe, "ok", (New-Object System.Text.UTF8Encoding($false)))
} finally {
  Remove-Item -LiteralPath $writeProbe -Force -ErrorAction SilentlyContinue
}
if (-not (Test-Path -LiteralPath $portableGit -PathType Leaf)) { throw "PORTABLE_GIT_NOT_AVAILABLE: $portableGit" }
if (-not (Test-Path -LiteralPath $publisherRepo -PathType Container)) { throw "PUBLISHER_REPO_MISSING: $publisherRepo" }
if (-not (Test-Path -LiteralPath $worktreeRoot -PathType Container)) { throw "WORKTREE_ROOT_MISSING: $worktreeRoot" }

$env:AAYS_PORTABLE_ROOT = $root
$env:AAYS_REPO_ROOT = $publisherRepo
$env:AAYS_RUNNER_MODE = "F_PORTABLE_SINGLE_COORDINATOR_21_SLOT"
$env:TEMP = $tempRoot
$env:TMP = $tempRoot
$env:HOME = $homeRoot
$env:PYTHONNOUSERSITE = "1"
$env:PYTHONUSERBASE = $pythonUserRoot
$env:PYTHONPYCACHEPREFIX = $pycacheRoot
$env:PIP_CACHE_DIR = Join-Path $cacheRoot "pip"
$env:UV_CACHE_DIR = Join-Path $cacheRoot "uv"
$env:XDG_CACHE_HOME = Join-Path $cacheRoot "xdg"
$env:MPLCONFIGDIR = Join-Path $cacheRoot "matplotlib"
$env:NUMBA_CACHE_DIR = Join-Path $cacheRoot "numba"
$env:JOBLIB_TEMP_FOLDER = Join-Path $tempRoot "joblib"
$env:HF_HOME = Join-Path $cacheRoot "huggingface"
$env:TORCH_HOME = Join-Path $cacheRoot "torch"
$env:PLAYWRIGHT_BROWSERS_PATH = Join-Path $runtimeRoot "playwright-browsers"
$env:GIT_CONFIG_GLOBAL = $portableGitConfig
$env:GIT_TERMINAL_PROMPT = "0"
$env:GCM_INTERACTIVE = "Never"
$env:GIT_HTTP_LOW_SPEED_LIMIT = "1"
$env:GIT_HTTP_LOW_SPEED_TIME = "30"

# Store Git ownership and long-path settings on the portable disk. Multiple
# keepalive/manual launches can overlap, so serialize one atomic replacement;
# never let Git's own config writer contend on a shared *.lock file.
$gitConfigMutex = [Threading.Mutex]::new($false, "Local\AAYSPortableGitConfigV3")
$gitConfigLockTaken = $false
$configTemporary = $null
try {
  try { $gitConfigLockTaken = $gitConfigMutex.WaitOne([TimeSpan]::FromSeconds(30)) }
  catch [Threading.AbandonedMutexException] { $gitConfigLockTaken = $true }
  if (-not $gitConfigLockTaken) { throw "PORTABLE_GIT_CONFIG_MUTEX_TIMEOUT" }

  $safeRepos = @($publisherRepo)
  $slotRoot = Join-Path $worktreeRoot "slots"
  if (Test-Path -LiteralPath $slotRoot -PathType Container) {
    $safeRepos += Get-ChildItem -LiteralPath $slotRoot -Directory | ForEach-Object { $_.FullName }
  }
  $overridePath = Join-Path $stateRoot "worktree_overrides.json"
  if (Test-Path -LiteralPath $overridePath -PathType Leaf) {
    try {
      $overrides = Get-Content -LiteralPath $overridePath -Raw | ConvertFrom-Json -ErrorAction Stop
      foreach ($property in $overrides.PSObject.Properties) {
        $candidate = [System.IO.Path]::GetFullPath((Join-Path $root ([string]$property.Value)))
        $worktreePrefix = [System.IO.Path]::GetFullPath($worktreeRoot).TrimEnd("\") + "\"
        if ($candidate.StartsWith($worktreePrefix, [StringComparison]::OrdinalIgnoreCase) -and (Test-Path -LiteralPath $candidate -PathType Container)) { $safeRepos += $candidate }
      }
    } catch {
      Write-Warning "WORKTREE_OVERRIDES_IGNORED: $($_.Exception.Message)"
    }
  }
  $configLines = [System.Collections.Generic.List[string]]::new()
  $configLines.Add("[core]"); $configLines.Add("`tlongpaths = true")
  $configLines.Add("[user]"); $configLines.Add("`tname = AAYS Portable Runner"); $configLines.Add("`temail = aays-portable-runner@local.invalid")
  $configLines.Add("[safe]")
  foreach ($safeRepo in ($safeRepos | Sort-Object -Unique)) { $configLines.Add("`tdirectory = " + ([System.IO.Path]::GetFullPath($safeRepo)).Replace("\", "/")) }
  $configText = ($configLines -join "`n") + "`n"
  $currentConfigText = $null
  if (Test-Path -LiteralPath $portableGitConfig -PathType Leaf) {
    try { $currentConfigText = [System.IO.File]::ReadAllText($portableGitConfig, [System.Text.Encoding]::UTF8) } catch { $currentConfigText = $null }
  }
  if ($currentConfigText -ne $configText) {
    $configTemporary = $portableGitConfig + ".atomic." + [guid]::NewGuid().ToString("N")
    [System.IO.File]::WriteAllText($configTemporary, $configText, (New-Object System.Text.UTF8Encoding($false)))
    Move-Item -LiteralPath $configTemporary -Destination $portableGitConfig -Force
    $configTemporary = $null
  }
} finally {
  if ($configTemporary -and (Test-Path -LiteralPath $configTemporary -PathType Leaf)) { Remove-Item -LiteralPath $configTemporary -Force -ErrorAction SilentlyContinue }
  if ($gitConfigLockTaken) { $gitConfigMutex.ReleaseMutex() }
  $gitConfigMutex.Dispose()
}
function Test-PublisherGitReady {
  param([string]$GitPath, [string]$RepositoryPath, [int]$TimeoutMilliseconds = 10000)
  $startInfo = [System.Diagnostics.ProcessStartInfo]::new()
  $startInfo.FileName = $GitPath
  $startInfo.UseShellExecute = $false
  $startInfo.CreateNoWindow = $true
  $startInfo.RedirectStandardOutput = $true
  $startInfo.RedirectStandardError = $true
  [void]$startInfo.ArgumentList.Add("-C")
  [void]$startInfo.ArgumentList.Add($RepositoryPath)
  [void]$startInfo.ArgumentList.Add("rev-parse")
  [void]$startInfo.ArgumentList.Add("--is-inside-work-tree")
  $process = [System.Diagnostics.Process]::new()
  $process.StartInfo = $startInfo
  try {
    if (-not $process.Start()) { return $false }
    if (-not $process.WaitForExit($TimeoutMilliseconds)) {
      try { $process.Kill($true) } catch { }
      try { $process.WaitForExit() } catch { }
      return $false
    }
    return $process.ExitCode -eq 0
  } finally {
    $process.Dispose()
  }
}

$publisherGitReady = $false
for ($gitCheckAttempt = 1; $gitCheckAttempt -le 5; $gitCheckAttempt++) {
  if (Test-PublisherGitReady -GitPath $portableGit -RepositoryPath $publisherRepo) { $publisherGitReady = $true; break }
  Start-Sleep -Milliseconds (250 * $gitCheckAttempt)
}
if (-not $publisherGitReady) { throw "PUBLISHER_REPO_GIT_CHECK_FAILED_AFTER_RETRY" }

$pythonCandidates = @(
  (Join-Path $root "runtime\python312\python.exe"),
  (Join-Path $root "runtime\python\python.exe")
)
$python = $pythonCandidates | Where-Object { Test-Path -LiteralPath $_ -PathType Leaf } | Select-Object -First 1
if (-not $python) { throw "PORTABLE_PYTHON_NOT_AVAILABLE" }

$hostProof = [ordered]@{
  status = "PASS"
  checked_at = [DateTime]::UtcNow.ToString("o")
  computer_name = $env:COMPUTERNAME
  portable_root = $root
  drive_letter_runtime_only = $true
  architecture_version = 3
  workstream_id = "AAYS_21_SLOT_SAFE_PARALLEL_V1"
  portable_python = $python
  portable_git = $portableGit
  publisher_repo = $publisherRepo
  safe_directory_count = @($safeRepos).Count
  root_writable = $true
  final_ready = $false
}
$hostProofJson = $hostProof | ConvertTo-Json -Depth 6
[System.IO.File]::WriteAllText((Join-Path $stateRoot "host_compatibility_latest.json"), $hostProofJson + "`n", (New-Object System.Text.UTF8Encoding($false)))

function Get-CoordinatorStatus {
  $raw = & $python $coordinator status --root $root
  if ($LASTEXITCODE -ne 0) { throw "COORDINATOR_STATUS_FAILED" }
  return $raw | ConvertFrom-Json
}

function Request-Stop {
  $before = Get-CoordinatorStatus
  if (-not $before.pid_alive) { return $before }
  & $python $coordinator request-stop --root $root | Out-Null
  if ($LASTEXITCODE -ne 0) { throw "STOP_REQUEST_FAILED" }
  $deadline = (Get-Date).AddSeconds($StopTimeoutSeconds)
  do {
    Start-Sleep -Milliseconds 500
    $current = Get-CoordinatorStatus
    if (-not $current.pid_alive) { return $current }
  } while ((Get-Date) -lt $deadline)
  throw "GRACEFUL_STOP_TIMEOUT_PID_$($before.pid)"
}

if ($Action -eq "Status") {
  Get-CoordinatorStatus | ConvertTo-Json -Depth 10
  exit 0
}
if ($Action -eq "Stop") {
  $manualStop = [ordered]@{
    requested = $true
    requested_at = [DateTime]::UtcNow.ToString("o")
    reason = "USER_REQUESTED_STOP"
    final_ready = $false
  } | ConvertTo-Json
  [System.IO.File]::WriteAllText($manualStopPath, $manualStop + "`n", (New-Object System.Text.UTF8Encoding($false)))
  Request-Stop | ConvertTo-Json -Depth 10
  exit 0
}
if ($Action -eq "Preflight") {
  & $python $coordinator preflight --root $root
  exit $LASTEXITCODE
}
if ($Action -eq "FixtureTest") {
  & $python $coordinator fixtures --root $root
  exit $LASTEXITCODE
}
if ($Action -eq "Restart") {
  Request-Stop | Out-Null
}

# Only explicit Start and Restart actions clear a persistent manual stop.
Remove-Item -LiteralPath $manualStopPath -Force -ErrorAction SilentlyContinue

$preflightRaw = & $python $coordinator preflight --root $root
if ($LASTEXITCODE -ne 0) {
  Write-Output $preflightRaw
  throw "PORTABLE_PREFLIGHT_FAILED"
}
$current = Get-CoordinatorStatus
if ($current.pid_alive) {
  [ordered]@{ status = "already_running"; pid = $current.pid; second_launch_blocked = $true; final_ready = $false } | ConvertTo-Json
  exit 0
}
$coordinatorArgs = ('"{0}" run --root "{1}"' -f $coordinator, $root)
$process = Start-Process -FilePath $python -ArgumentList $coordinatorArgs -WorkingDirectory $root -WindowStyle Hidden -RedirectStandardOutput $stdout -RedirectStandardError $stderr -PassThru
$deadline = (Get-Date).AddSeconds(30)
do {
  Start-Sleep -Milliseconds 500
  $current = Get-CoordinatorStatus
  if ($current.pid_alive) {
    [ordered]@{ status = "started"; pid = $current.pid; child_capacity = $current.max_child_workers; resource_profile = $current.resource_profile; portable_root = $root; final_ready = $false } | ConvertTo-Json
    exit 0
  }
} while ((Get-Date) -lt $deadline)
throw "COORDINATOR_START_TIMEOUT_LAUNCHER_PID_$($process.Id)"
