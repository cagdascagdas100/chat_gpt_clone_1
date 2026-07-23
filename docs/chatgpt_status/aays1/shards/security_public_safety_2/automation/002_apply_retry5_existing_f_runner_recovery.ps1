[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$slotId = 'security_public_safety_2'
$taskId = 'security_public_safety_2_geometry_lsoa_police_sample_wave1_retry5_20260722'
$attemptId = 'attempt-005'
$branch = 'codex/aays-single-runner-v5-20260706'
$repoRoot = 'F:\TerraYield_AAYS_Portable\runner_system\AAYS_WT\AAYS_RUNNER_HEALTHY_20260707'
$externalLauncher = 'F:\TerraYield_AAYS_Portable\RUN_AAYS_STABLE_RUNNER_FROM_THIS_DISK.cmd'
$outputRel = 'docs\chatgpt_status\aays1\shards\security_public_safety_2\runner_outputs\002_retry5_operator_recovery_preflight_latest.json'

$remoteContract = [ordered]@{
  helper = [ordered]@{path='docs/chatgpt_status/aays1/shards/security_public_safety_2/automation/001_restart_existing_canonical_f_runner_for_retry5.ps1';blob='07ecb487806f4fb80aefb35a94a497cd87dd7f08'}
  queue = [ordered]@{path='docs/chatgpt_status/aays1/queue/000000_security_public_safety_2_wave1_retry5_20260722.v3.task.json';blob='43ba5691e3b4a3c345d2f8fd3303185b3f214d21'}
  bridge = [ordered]@{path='docs/chatgpt_status/aays1/automation/security_public_safety_2_geometry_lsoa_police_sample_wave1_retry5_legacy_adaptive_bridge_20260722.ps1';blob='8f4b09b9713a56d78a9c624202f83028afd77b7a'}
  hardened_python = [ordered]@{path='docs/chatgpt_status/aays1/automation/security_public_safety_2_geometry_lsoa_police_sample_wave1_retry5_hardened_20260722.py';blob='cdb20cb578be5de1789e7821d2a435c1a9f77d58'}
  method = [ordered]@{path='england_map_web/data/aays_21_slots/security_public_safety_2/official_security_scoring_method_preregistration_20260722.json';blob='2d4187b9dc9051bad029b0c81d7328dbff53609e'}
}
$controllerContract = [ordered]@{
  external_launcher = [ordered]@{path=$externalLauncher;blob='d7d3ba35dd0e26c5446b54aeb3bfc0860e30caae';external=$true}
  repo_entry = [ordered]@{path='devam.ps1';blob='6213d351b742eb3597b768cb2ca56ff240d45322';external=$false}
  shared_launcher = [ordered]@{path='docs/chatgpt_status/_shared/automation/START_AAYS_SINGLE_RUNNER_WITH_PANEL_20260706.ps1';blob='ccc703cbbb55f714788e1ee4acd4688cae7ae87e';external=$false}
  daemon = [ordered]@{path='docs/chatgpt_status/_shared/automation/RUN_AAYS_STABLE_LEGACY_RUNNER_DAEMON_20260707.ps1';blob='649e9195f396264d79a1910038a9dc50db567efb';external=$false}
  scan_runner = [ordered]@{path='docs/chatgpt_status/_shared/automation/RUN_SINGLE_AAYS_MULTI_PAGE_QUEUE_RUNNER_STABLE_20260707.ps1';blob='8ac8af78992b96609d81b76c78b59b2b3597a045';external=$false}
  panel_builder = [ordered]@{path='docs/chatgpt_status/_shared/automation/BUILD_AAYS_PAGE_PANEL_INDEX.ps1';blob='9162b4ea0e743ef586f42cea5fce13d0eda7c5ef';external=$false}
}

function Normalize-Rel([string]$Path) { return (($Path -replace '\\','/').TrimStart('/')) }
function Is-RuntimePath([string]$Path) {
  $r = Normalize-Rel $Path
  return (
    $r.StartsWith('docs/chatgpt_status/_shared/runner_outputs/') -or
    $r.StartsWith('docs/chatgpt_status/_shared/smoke/') -or
    $r.StartsWith('docs/chatgpt_status/_shared/smoke_tests/') -or
    $r.StartsWith('docs/chatgpt_status/_shared/heartbeat/') -or
    $r.StartsWith('docs/chatgpt_status/_shared/status/') -or
    $r.StartsWith('docs/chatgpt_status/_shared/control/') -or
    $r.StartsWith('docs/chatgpt_status/_shared/logs/') -or
    $r.StartsWith('docs/chatgpt_status/_shared/reports/') -or
    $r.StartsWith('docs/chatgpt_status/_shared/runner_lock/') -or
    $r.StartsWith('docs/chatgpt_status/_shared/locks/') -or
    $r.StartsWith('docs/chatgpt_status/_shared/panel/') -or
    $r.StartsWith('england_map_web/data/runner_panel/') -or
    $r.StartsWith('docs/chatgpt_status/aays1/shards/security_public_safety_2/runner_outputs/')
  )
}
function Git-BlobForFile([string]$Path) {
  if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { return $null }
  $bytes = [IO.File]::ReadAllBytes($Path)
  $prefix = [Text.Encoding]::ASCII.GetBytes(('blob {0}' -f $bytes.Length) + [char]0)
  $sha = [Security.Cryptography.SHA1]::Create()
  try {
    [void]$sha.TransformBlock($prefix,0,$prefix.Length,$prefix,0)
    [void]$sha.TransformFinalBlock($bytes,0,$bytes.Length)
    return ([BitConverter]::ToString($sha.Hash)).Replace('-','').ToLowerInvariant()
  } finally { $sha.Dispose() }
}
function Remote-Blob([string]$RelativePath) {
  $spec = "origin/${branch}:$RelativePath"
  $value = (& $git.Source -C $repoRoot rev-parse $spec 2>&1 | Select-Object -Last 1).ToString().Trim()
  if ($LASTEXITCODE -ne 0 -or $value -notmatch '^[0-9a-f]{40}$') { return $null }
  return $value
}
function Remote-Text([string]$RelativePath) {
  $spec = "origin/${branch}:$RelativePath"
  $value = (& $git.Source -C $repoRoot show $spec 2>&1 | Out-String)
  if ($LASTEXITCODE -ne 0) { return $null }
  return $value
}
function Write-Receipt([string]$Status,[bool]$FetchAttempted,[bool]$RuntimeDirtyAllowed,[bool]$RemoteVerified,[bool]$ControllerVerified,[bool]$HelperInvoked,[int]$HelperExitCode,[string]$LocalHead,[string]$RemoteHead,[object]$DirtyPaths,[object]$RemoteBlobs,[object]$ControllerBlobs,[string]$Detail) {
  $output = Join-Path $repoRoot $outputRel
  $parent = Split-Path -Parent $output
  if (-not (Test-Path -LiteralPath $parent)) { New-Item -ItemType Directory -Force -Path $parent | Out-Null }
  [ordered]@{
    schema_version = 10
    slot_id = $slotId
    task_id = $taskId
    attempt_id = $attemptId
    status = $Status
    checked_at = [DateTimeOffset]::UtcNow.ToString('o')
    repo_root = $repoRoot
    branch = $branch
    fetch_attempted = $FetchAttempted
    runtime_dirty_paths_allowed = $RuntimeDirtyAllowed
    remote_contract_verified = $RemoteVerified
    local_controller_chain_verified = $ControllerVerified
    helper_invoked = $HelperInvoked
    helper_exit_code = $HelperExitCode
    local_head = $LocalHead
    remote_head = $RemoteHead
    local_head_reset_or_rebase_applied = $false
    dirty_paths = $DirtyPaths
    remote_blobs = $RemoteBlobs
    controller_blobs = $ControllerBlobs
    expected_remote_contract = $remoteContract
    expected_controller_contract = $controllerContract
    exact_target_rows = @(30762..30773)
    canonical_f_process_identity_required = $true
    foreign_runner_process_fail_closed = $true
    heartbeat_pid_and_repo_root_identity_required = $true
    transient_without_fresh_daemon_is_failure = $true
    process_exit_before_kill_is_clean_stop = $true
    stale_daemon_recovery_enabled = $true
    stale_minutes_threshold = 20
    existing_single_runner_architecture_only = $true
    cross_slot_runtime_files_preserved = $true
    new_runner_architecture_created = $false
    parallel_runner_started = $false
    final_ready = $false
    fake_data = $false
    db_write = $false
    migration = $false
    production_deploy = $false
    detail = $Detail
  } | ConvertTo-Json -Depth 16 | Set-Content -LiteralPath $output -Encoding UTF8
}

if (-not (Test-Path -LiteralPath $repoRoot -PathType Container)) { throw "CANONICAL_F_REPO_ROOT_MISSING=$repoRoot" }
$git = Get-Command git -ErrorAction SilentlyContinue
if (-not $git) { throw 'GIT_EXECUTABLE_NOT_FOUND' }
$activeBranch = (& $git.Source -C $repoRoot rev-parse --abbrev-ref HEAD 2>&1 | Select-Object -Last 1).ToString().Trim()
if ($LASTEXITCODE -ne 0 -or $activeBranch -ne $branch) { Write-Receipt 'BLOCKED_CANONICAL_BRANCH_MISMATCH' $false $false $false $false $false -1 '' '' @() @{} @{} "active_branch=$activeBranch"; exit 2 }
$localHead = (& $git.Source -C $repoRoot rev-parse HEAD 2>&1 | Select-Object -Last 1).ToString().Trim()
$statusLines = @(& $git.Source -C $repoRoot status --porcelain 2>&1)
if ($LASTEXITCODE -ne 0) { throw 'CANONICAL_F_REPO_STATUS_FAILED' }
$dirtyPaths = @($statusLines | Where-Object { $_ } | ForEach-Object {
  $p = if ($_.Length -ge 4) { $_.Substring(3).Trim().Trim('"') } else { $_.Trim() }
  if ($p -match ' -> ') { $p = ($p -split ' -> ')[-1] }
  Normalize-Rel $p
})
$nonRuntimeDirty = @($dirtyPaths | Where-Object { -not (Is-RuntimePath $_) })
if ($nonRuntimeDirty.Count -gt 0) { Write-Receipt 'BLOCKED_NON_RUNTIME_DIRTY_PATHS' $false $false $false $false $false -1 $localHead '' $dirtyPaths @{} @{} ($nonRuntimeDirty -join ','); exit 3 }

& $git.Source -C $repoRoot fetch --no-tags origin $branch
if ($LASTEXITCODE -ne 0) { Write-Receipt 'BLOCKED_CANONICAL_FETCH_FAILED' $true ($dirtyPaths.Count -gt 0) $false $false $false -1 $localHead '' $dirtyPaths @{} @{} 'git fetch failed'; exit 4 }
$remoteHead = (& $git.Source -C $repoRoot rev-parse "origin/$branch" 2>&1 | Select-Object -Last 1).ToString().Trim()
if (-not $remoteHead) { Write-Receipt 'BLOCKED_REMOTE_HEAD_READ_FAILED' $true ($dirtyPaths.Count -gt 0) $false $false $false -1 $localHead '' $dirtyPaths @{} @{} 'origin branch head unavailable'; exit 5 }

$remoteActual = [ordered]@{}
foreach ($name in $remoteContract.Keys) {
  $spec = $remoteContract[$name]
  $actual = Remote-Blob ([string]$spec.path)
  $remoteActual[$name] = $actual
  if ([string]::IsNullOrWhiteSpace([string]$actual)) { Write-Receipt ("BLOCKED_REMOTE_{0}_MISSING" -f ([string]$name).ToUpperInvariant()) $true ($dirtyPaths.Count -gt 0) $false $false $false -1 $localHead $remoteHead $dirtyPaths $remoteActual @{} ([string]$spec.path); exit 6 }
  if ([string]$actual -ne [string]$spec.blob) { Write-Receipt ("BLOCKED_REMOTE_{0}_BLOB_MISMATCH" -f ([string]$name).ToUpperInvariant()) $true ($dirtyPaths.Count -gt 0) $false $false $false -1 $localHead $remoteHead $dirtyPaths $remoteActual @{} "expected=$($spec.blob) actual=$actual"; exit 7 }
}

$queueText = Remote-Text ([string]$remoteContract.queue.path)
try { $queue = $queueText | ConvertFrom-Json } catch { Write-Receipt 'BLOCKED_REMOTE_QUEUE_INVALID_JSON' $true ($dirtyPaths.Count -gt 0) $false $false $false -1 $localHead $remoteHead $dirtyPaths $remoteActual @{} $_.Exception.Message; exit 8 }
$expectedPythonPath = ([string]$remoteContract.hardened_python.path)
if ([string]$queue.task_id -ne $taskId -or [string]$queue.attempt_id -ne $attemptId -or [string]$queue.status -ne 'pickup_requested') { Write-Receipt 'BLOCKED_REMOTE_QUEUE_IDENTITY_OR_STATUS_MISMATCH' $true ($dirtyPaths.Count -gt 0) $false $false $false -1 $localHead $remoteHead $dirtyPaths $remoteActual @{} "task=$($queue.task_id) attempt=$($queue.attempt_id) status=$($queue.status)"; exit 9 }
if ([string]$queue.python_script_path -ne $expectedPythonPath) { Write-Receipt 'BLOCKED_REMOTE_QUEUE_PYTHON_PATH_MISMATCH' $true ($dirtyPaths.Count -gt 0) $false $false $false -1 $localHead $remoteHead $dirtyPaths $remoteActual @{} "python=$($queue.python_script_path)"; exit 10 }
if ([string]$queue.implementation_integrity.bridge_blob_sha -ne [string]$remoteContract.bridge.blob -or [string]$queue.implementation_integrity.hardened_python_entry_blob_sha -ne [string]$remoteContract.hardened_python.blob) { Write-Receipt 'BLOCKED_REMOTE_QUEUE_IMPLEMENTATION_INTEGRITY_MISMATCH' $true ($dirtyPaths.Count -gt 0) $false $false $false -1 $localHead $remoteHead $dirtyPaths $remoteActual @{} 'queue implementation_integrity mismatch'; exit 11 }

$controllerActual = [ordered]@{}
foreach ($name in $controllerContract.Keys) {
  $spec = $controllerContract[$name]
  $path = if ([bool]$spec.external) { [string]$spec.path } else { Join-Path $repoRoot (([string]$spec.path) -replace '/','\') }
  $actual = Git-BlobForFile $path
  $controllerActual[$name] = $actual
  if ([string]::IsNullOrWhiteSpace([string]$actual)) { Write-Receipt ("BLOCKED_LOCAL_CONTROLLER_{0}_MISSING" -f ([string]$name).ToUpperInvariant()) $true ($dirtyPaths.Count -gt 0) $true $false $false -1 $localHead $remoteHead $dirtyPaths $remoteActual $controllerActual $path; exit 12 }
  if ([string]$actual -ne [string]$spec.blob) { Write-Receipt ("BLOCKED_LOCAL_CONTROLLER_{0}_BLOB_MISMATCH" -f ([string]$name).ToUpperInvariant()) $true ($dirtyPaths.Count -gt 0) $true $false $false -1 $localHead $remoteHead $dirtyPaths $remoteActual $controllerActual "expected=$($spec.blob) actual=$actual"; exit 13 }
  if (-not [bool]$spec.external) {
    $remoteControllerBlob = Remote-Blob ([string]$spec.path)
    if ([string]$remoteControllerBlob -ne [string]$spec.blob) { Write-Receipt ("BLOCKED_REMOTE_CONTROLLER_{0}_BLOB_MISMATCH" -f ([string]$name).ToUpperInvariant()) $true ($dirtyPaths.Count -gt 0) $true $false $false -1 $localHead $remoteHead $dirtyPaths $remoteActual $controllerActual "expected=$($spec.blob) remote=$remoteControllerBlob"; exit 14 }
  }
}

$helperPath = Join-Path $repoRoot (([string]$remoteContract.helper.path) -replace '/','\')
& powershell.exe -NoProfile -ExecutionPolicy Bypass -File $helperPath -StaleMinutes 20
$helperExit = $LASTEXITCODE
if ($null -eq $helperExit) { $helperExit = 1 }
$status = if ($helperExit -eq 0) { 'RETRY5_RUNTIME_SAFE_REMOTE_CONTRACT_RECOVERY_INVOKED' } else { 'BLOCKED_RETRY5_RUNTIME_SAFE_REMOTE_CONTRACT_RECOVERY_FAILED' }
Write-Receipt $status $true ($dirtyPaths.Count -gt 0) $true $true $true $helperExit $localHead $remoteHead $dirtyPaths $remoteActual $controllerActual "remote and local controller chains verified; helper_exit=$helperExit"
exit $helperExit
