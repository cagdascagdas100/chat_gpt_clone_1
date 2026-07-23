[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$slotId = 'security_public_safety_2'
$taskId = 'security_public_safety_2_geometry_lsoa_police_sample_wave1_retry5_20260722'
$attemptId = 'attempt-005'
$branch = 'codex/aays-single-runner-v5-20260706'
$repoRoot = 'F:\TerraYield_AAYS_Portable\runner_system\AAYS_WT\AAYS_RUNNER_HEALTHY_20260707'
$innerRel = 'docs/chatgpt_status/aays1/shards/security_public_safety_2/automation/002_apply_retry5_existing_f_runner_recovery.ps1'
$outputRel = 'docs/chatgpt_status/aays1/shards/security_public_safety_2/runner_outputs/003_retry5_ffsafe_bootstrap_latest.json'

$contract = [ordered]@{
  inner = [ordered]@{path=$innerRel;blob='ea0d0da2c137c5e0b31592094e1a80d1ac0b49e1'}
  helper = [ordered]@{path='docs/chatgpt_status/aays1/shards/security_public_safety_2/automation/001_restart_existing_canonical_f_runner_for_retry5.ps1';blob='ced75abf0eb51712ad8284904655a23a69cbda30'}
  queue = [ordered]@{path='docs/chatgpt_status/aays1/queue/000000_security_public_safety_2_wave1_retry5_20260722.v3.task.json';blob='43ba5691e3b4a3c345d2f8fd3303185b3f214d21'}
  bridge = [ordered]@{path='docs/chatgpt_status/aays1/automation/security_public_safety_2_geometry_lsoa_police_sample_wave1_retry5_legacy_adaptive_bridge_20260722.ps1';blob='8f4b09b9713a56d78a9c624202f83028afd77b7a'}
  hardened_python = [ordered]@{path='docs/chatgpt_status/aays1/automation/security_public_safety_2_geometry_lsoa_police_sample_wave1_retry5_hardened_20260722.py';blob='cdb20cb578be5de1789e7821d2a435c1a9f77d58'}
  method = [ordered]@{path='england_map_web/data/aays_21_slots/security_public_safety_2/official_security_scoring_method_preregistration_20260722.json';blob='2d4187b9dc9051bad029b0c81d7328dbff53609e'}
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
  $value = (& $git.Source -C $repoRoot rev-parse "origin/${branch}:$RelativePath" 2>&1 | Select-Object -Last 1).ToString().Trim()
  if ($LASTEXITCODE -ne 0 -or $value -notmatch '^[0-9a-f]{40}$') { return $null }
  return $value
}
function Atomic-Json([string]$Path,[object]$Value) {
  $parent = Split-Path -Parent $Path
  if (-not (Test-Path -LiteralPath $parent)) { New-Item -ItemType Directory -Force -Path $parent | Out-Null }
  $temp = "$Path.tmp.$PID"
  [IO.File]::WriteAllText($temp,(($Value | ConvertTo-Json -Depth 16) + "`n"),[Text.UTF8Encoding]::new($false))
  Move-Item -LiteralPath $temp -Destination $Path -Force
}
function Receipt([string]$Status,[string]$Before,[string]$Remote,[string]$After,[bool]$FastForwarded,[bool]$InnerInvoked,[int]$InnerExit,[object]$Dirty,[object]$LocalBlobs,[object]$RemoteBlobs,[string]$Detail) {
  $out = Join-Path $repoRoot ($outputRel -replace '/','\')
  Atomic-Json $out ([ordered]@{
    schema_version = 5
    slot_id = $slotId
    task_id = $taskId
    attempt_id = $attemptId
    status = $Status
    checked_at = [DateTimeOffset]::UtcNow.ToString('o')
    branch = $branch
    local_head_before = $Before
    remote_head = $Remote
    local_head_after = $After
    fast_forward_only_applied = $FastForwarded
    reset_or_rebase_applied = $false
    runtime_dirty_paths_preserved = $true
    non_runtime_dirty_paths_blocked = $true
    local_contract_blobs = $LocalBlobs
    remote_contract_blobs = $RemoteBlobs
    expected_contract = $contract
    canonical_f_process_identity_required = $true
    foreign_runner_process_fail_closed = $true
    heartbeat_repo_root_optional_with_bound_lock_fallback = $true
    lock_fallback_requires_pid_repo_root_instance_start_freshness_scope_branch = $true
    transient_without_fresh_daemon_is_failure = $true
    process_exit_before_kill_is_clean_stop = $true
    inner_preflight_invoked = $InnerInvoked
    inner_preflight_exit_code = $InnerExit
    dirty_paths = $Dirty
    existing_single_runner_architecture_only = $true
    new_runner_created = $false
    parallel_runner_started = $false
    continuation_key = 'b687f02892911b3faa36c6eb40ded780029bb49e50c1c52aaaa8e3a94157b4ad'
    detail = $Detail
    final_ready = $false
    fake_data = $false
  })
}

if (-not (Test-Path -LiteralPath $repoRoot -PathType Container)) { throw "CANONICAL_F_REPO_ROOT_MISSING=$repoRoot" }
$git = Get-Command git -ErrorAction SilentlyContinue
if (-not $git) { throw 'GIT_EXECUTABLE_NOT_FOUND' }
$activeBranch = (& $git.Source -C $repoRoot rev-parse --abbrev-ref HEAD 2>&1 | Select-Object -Last 1).ToString().Trim()
if ($LASTEXITCODE -ne 0 -or $activeBranch -ne $branch) { Receipt 'BLOCKED_CANONICAL_BRANCH_MISMATCH' '' '' '' $false $false -1 @() @{} @{} "active_branch=$activeBranch"; exit 2 }

$before = (& $git.Source -C $repoRoot rev-parse HEAD 2>&1 | Select-Object -Last 1).ToString().Trim()
$statusLines = @(& $git.Source -C $repoRoot status --porcelain 2>&1)
if ($LASTEXITCODE -ne 0) { throw 'CANONICAL_F_REPO_STATUS_FAILED' }
$dirty = @($statusLines | Where-Object { $_ } | ForEach-Object {
  $p = if ($_.Length -ge 4) { $_.Substring(3).Trim().Trim('"') } else { $_.Trim() }
  if ($p -match ' -> ') { $p = ($p -split ' -> ')[-1] }
  Normalize-Rel $p
})
$nonRuntimeDirty = @($dirty | Where-Object { -not (Is-RuntimePath $_) })
if ($nonRuntimeDirty.Count -gt 0) { Receipt 'BLOCKED_NON_RUNTIME_DIRTY_PATHS' $before '' $before $false $false -1 $dirty @{} @{} ($nonRuntimeDirty -join ','); exit 3 }

& $git.Source -C $repoRoot fetch --no-tags origin $branch
if ($LASTEXITCODE -ne 0) { Receipt 'BLOCKED_CANONICAL_FETCH_FAILED' $before '' $before $false $false -1 $dirty @{} @{} 'git fetch failed'; exit 4 }
$remote = (& $git.Source -C $repoRoot rev-parse "origin/$branch" 2>&1 | Select-Object -Last 1).ToString().Trim()
if ($remote -notmatch '^[0-9a-f]{40}$') { Receipt 'BLOCKED_REMOTE_HEAD_READ_FAILED' $before $remote $before $false $false -1 $dirty @{} @{} 'origin head unavailable'; exit 5 }

$ff = $false
$after = $before
if ($before -ne $remote) {
  & $git.Source -C $repoRoot merge-base --is-ancestor $before $remote
  if ($LASTEXITCODE -ne 0) { Receipt 'BLOCKED_LOCAL_REMOTE_HISTORY_DIVERGED' $before $remote $before $false $false -1 $dirty @{} @{} 'local HEAD is not an ancestor of remote HEAD'; exit 6 }
  & $git.Source -C $repoRoot merge --ff-only "origin/$branch"
  if ($LASTEXITCODE -ne 0) { Receipt 'BLOCKED_FAST_FORWARD_ONLY_FAILED' $before $remote $before $false $false -1 $dirty @{} @{} 'ff-only failed; no reset or rebase attempted'; exit 7 }
  $after = (& $git.Source -C $repoRoot rev-parse HEAD 2>&1 | Select-Object -Last 1).ToString().Trim()
  if ($after -ne $remote) { Receipt 'BLOCKED_FAST_FORWARD_READBACK_MISMATCH' $before $remote $after $true $false -1 $dirty @{} @{} 'local HEAD does not equal remote after ff-only'; exit 8 }
  $ff = $true
}

$localBlobs = [ordered]@{}
$remoteBlobs = [ordered]@{}
foreach ($name in $contract.Keys) {
  $spec = $contract[$name]
  $remoteBlob = Remote-Blob ([string]$spec.path)
  $localPath = Join-Path $repoRoot (([string]$spec.path) -replace '/','\')
  $localBlob = Git-BlobForFile $localPath
  $remoteBlobs[$name] = $remoteBlob
  $localBlobs[$name] = $localBlob
  if ([string]$remoteBlob -ne [string]$spec.blob) { Receipt ("BLOCKED_REMOTE_{0}_BLOB_MISMATCH" -f ([string]$name).ToUpperInvariant()) $before $remote $after $ff $false -1 $dirty $localBlobs $remoteBlobs "expected=$($spec.blob) remote=$remoteBlob"; exit 9 }
  if ([string]$localBlob -ne [string]$spec.blob) { Receipt ("BLOCKED_LOCAL_{0}_BLOB_MISMATCH" -f ([string]$name).ToUpperInvariant()) $before $remote $after $ff $false -1 $dirty $localBlobs $remoteBlobs "expected=$($spec.blob) local=$localBlob"; exit 10 }
}

$innerPath = Join-Path $repoRoot ($innerRel -replace '/','\')
& powershell.exe -NoProfile -ExecutionPolicy Bypass -File $innerPath
$innerExit = $LASTEXITCODE
if ($null -eq $innerExit) { $innerExit = 1 }
$finalStatus = if ($innerExit -eq 0) { 'FFSAFE_SYNC_AND_RETRY5_RECOVERY_INVOKED' } else { 'BLOCKED_INNER_RETRY5_RECOVERY_FAILED' }
Receipt $finalStatus $before $remote $after $ff $true $innerExit $dirty $localBlobs $remoteBlobs "inner_exit=$innerExit"
exit $innerExit
