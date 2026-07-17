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
$logRoot = Join-Path $root "logs\adaptive_v3"
$stdout = Join-Path $logRoot "coordinator.out.log"
$stderr = Join-Path $logRoot "coordinator.err.log"

if (-not (Test-Path -LiteralPath $identityPath -PathType Leaf)) { throw "PORTABLE_IDENTITY_MISSING: $identityPath" }
if (-not (Test-Path -LiteralPath $coordinator -PathType Leaf)) { throw "COORDINATOR_SCRIPT_MISSING: $coordinator" }
$identity = Get-Content -LiteralPath $identityPath -Raw | ConvertFrom-Json
if ($identity.portable_product -ne "AAYS_TerraYield" -or $identity.schema_version -ne 2) { throw "PORTABLE_IDENTITY_INVALID" }
if ([int]$identity.architecture_version -ne 3) { throw "PORTABLE_IDENTITY_ARCHITECTURE_MUST_BE_3" }
if ($identity.relative_launcher_path -ne "RUN_AAYS_ADAPTIVE_15_WORKER.cmd") { throw "PORTABLE_IDENTITY_LAUNCHER_MISMATCH" }
New-Item -ItemType Directory -Force -Path $logRoot | Out-Null

$publisherRepo = Join-Path $root ([string]$identity.relative_repo_path)
$worktreeRoot = Join-Path $root ([string]$identity.relative_worktree_root)
$portableGit = Join-Path $root "runtime\git\cmd\git.exe"
$portableGitConfig = Join-Path $root "runtime\gitconfig.aays.portable"
$stateRoot = Join-Path $root "state"
$writeProbe = Join-Path $stateRoot ("write_probe_" + [guid]::NewGuid().ToString("N") + ".tmp")

New-Item -ItemType Directory -Force -Path $stateRoot | Out-Null
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
$env:AAYS_RUNNER_MODE = "F_PORTABLE_SINGLE_COORDINATOR_15_SLOT"
$env:GIT_CONFIG_GLOBAL = $portableGitConfig
$env:GIT_TERMINAL_PROMPT = "0"
$env:GCM_INTERACTIVE = "Never"
$env:GIT_HTTP_LOW_SPEED_LIMIT = "1"
$env:GIT_HTTP_LOW_SPEED_TIME = "30"

# Store Git ownership and long-path settings on the portable disk. Rebuild the
# entries on every launch so a changed drive letter cannot leave stale paths.
& $portableGit config --file $portableGitConfig core.longpaths true | Out-Null
& $portableGit config --file $portableGitConfig user.name "AAYS Portable Runner" | Out-Null
& $portableGit config --file $portableGitConfig user.email "aays-portable-runner@local.invalid" | Out-Null
& $portableGit config --file $portableGitConfig --unset-all safe.directory 2>$null
$safeRepos = @($publisherRepo)
$slotRoot = Join-Path $worktreeRoot "slots"
if (Test-Path -LiteralPath $slotRoot -PathType Container) {
  $safeRepos += Get-ChildItem -LiteralPath $slotRoot -Directory | ForEach-Object { $_.FullName }
}
foreach ($safeRepo in $safeRepos) {
  & $portableGit config --file $portableGitConfig --add safe.directory ([System.IO.Path]::GetFullPath($safeRepo)) | Out-Null
  if ($LASTEXITCODE -ne 0) { throw "PORTABLE_GIT_SAFE_DIRECTORY_FAILED: $safeRepo" }
}
& $portableGit -C $publisherRepo rev-parse --is-inside-work-tree *> $null
if ($LASTEXITCODE -ne 0) { throw "PUBLISHER_REPO_GIT_CHECK_FAILED" }

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
  workstream_id = "AAYS_15_SLOT_SAFE_PARALLEL_V1"
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
