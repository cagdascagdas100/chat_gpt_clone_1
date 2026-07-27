[CmdletBinding()]
param(
  [int]$GitTimeoutSeconds = 300,
  [int]$HelperTimeoutSeconds = 180
)

$ErrorActionPreference = 'Stop'
$taskId = 'aays1-height-difference-2-canonical-export-official-sampling-20260720'
$attemptId = 'height-difference-2-20260721-020'
$branch = 'codex/aays-single-runner-v5-20260706'
$repoRoot = 'F:\TerraYield_AAYS_Portable\runner_system\AAYS_WT\AAYS_RUNNER_HEALTHY_20260707'
$helperRel = 'docs\chatgpt_status\topography\shards\height_difference_2\automation\026_restart_existing_canonical_f_runner_if_stale.ps1'
$expectedHelperBlob = 'b3a18bcdb1b7158d18aab33b42d5797342d23cd1'
$outputRel = 'docs\chatgpt_status\topography\shards\height_difference_2\runner_outputs\015_operator_recovery_preflight_latest.json'
$snapshotRel = 'docs\chatgpt_status\topography\shards\height_difference_2\runner_outputs\016_operator_git_snapshot_latest.json'
$script:snapshotPayload = $null
$script:snapshotWritten = $false

function Invoke-GitBounded {
  param(
    [Parameter(Mandatory=$true)][string[]]$Arguments,
    [Parameter(Mandatory=$true)][int]$TimeoutSeconds
  )
  $stdout = [System.IO.Path]::GetTempFileName()
  $stderr = [System.IO.Path]::GetTempFileName()
  try {
    $process = Start-Process -FilePath 'git.exe' -ArgumentList $Arguments -WorkingDirectory $repoRoot -PassThru -NoNewWindow -RedirectStandardOutput $stdout -RedirectStandardError $stderr
    try {
      Wait-Process -Id $process.Id -Timeout $TimeoutSeconds -ErrorAction Stop
    } catch {
      Stop-Process -Id $process.Id -Force -ErrorAction SilentlyContinue
      throw "GIT_TIMEOUT arguments=$($Arguments -join ' ') timeout_seconds=$TimeoutSeconds"
    }
    $process.Refresh()
    $outText = if (Test-Path -LiteralPath $stdout) { Get-Content -LiteralPath $stdout -Raw -ErrorAction SilentlyContinue } else { '' }
    $errText = if (Test-Path -LiteralPath $stderr) { Get-Content -LiteralPath $stderr -Raw -ErrorAction SilentlyContinue } else { '' }
    [pscustomobject]@{
      ExitCode = [int]$process.ExitCode
      StdOut = [string]$outText
      StdErr = [string]$errText
    }
  } finally {
    Remove-Item -LiteralPath $stdout,$stderr -Force -ErrorAction SilentlyContinue
  }
}

function Write-JsonFile {
  param([string]$RelativePath, [hashtable]$Payload)
  $path = Join-Path $repoRoot $RelativePath
  $parent = Split-Path -Parent $path
  if (-not (Test-Path -LiteralPath $parent)) { New-Item -ItemType Directory -Force -Path $parent | Out-Null }
  $Payload | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath $path -Encoding UTF8
}

function Publish-Snapshot {
  if ($script:snapshotWritten -or $null -eq $script:snapshotPayload) { return }
  Write-JsonFile $snapshotRel $script:snapshotPayload
  $script:snapshotWritten = $true
}

function Write-Receipt {
  param(
    [string]$Status,
    [bool]$DirtyBefore,
    [bool]$SnapshotWritten,
    [bool]$StashCreated,
    [string]$StashRef,
    [bool]$FetchAttempted,
    [bool]$ResetApplied,
    [bool]$HelperInvoked,
    [bool]$HelperTimedOut,
    [int]$HelperExitCode,
    [string]$LocalHeadBefore,
    [string]$RemoteHead,
    [string]$LocalHeadAfter,
    [string]$Detail
  )
  Publish-Snapshot
  $SnapshotWritten = $script:snapshotWritten
  Write-JsonFile $outputRel ([ordered]@{
    schema_version = 5
    slot_id = 'height_difference_2'
    task_id = $taskId
    attempt_id = $attemptId
    status = $Status
    checked_at = (Get-Date).ToUniversalTime().ToString('o')
    repo_root = $repoRoot
    branch = $branch
    helper_path = $helperRel
    expected_helper_blob_sha = $expectedHelperBlob
    dirty_before = $DirtyBefore
    snapshot_written = $SnapshotWritten
    snapshot_required_for_clean_and_dirty = $true
    snapshot_publication_phase = 'receipt_exit_after_sync_or_on_blocked_exit'
    stash_created = $StashCreated
    stash_ref = $StashRef
    stash_auto_restore_attempted = $false
    fetch_attempted = $FetchAttempted
    reset_applied = $ResetApplied
    hard_reset_used = $false
    sync_mode = 'atomic_fetch_ff_only_exact_head_no_hard_reset'
    helper_invoked = $HelperInvoked
    helper_timed_out = $HelperTimedOut
    helper_exit_code = $HelperExitCode
    local_head_before = $LocalHeadBefore
    remote_head = $RemoteHead
    local_head_after = $LocalHeadAfter
    git_timeout_seconds = $GitTimeoutSeconds
    helper_timeout_seconds = $HelperTimeoutSeconds
    exact_target_rows = @(30762,46142,61522)
    nearest_row_fallback_allowed = $false
    existing_single_runner_architecture_only = $true
    new_runner_architecture_created = $false
    parallel_runner_started = $false
    final_ready = $false
    fake_data = $false
    db_write = $false
    migration = $false
    production_deploy = $false
    detail = $Detail
  })
}

if (-not (Test-Path -LiteralPath $repoRoot -PathType Container)) {
  throw "CANONICAL_F_REPO_ROOT_MISSING=$repoRoot"
}
$git = Get-Command git.exe -ErrorAction SilentlyContinue
if (-not $git) { $git = Get-Command git -ErrorAction SilentlyContinue }
if (-not $git) { throw 'GIT_EXECUTABLE_NOT_FOUND' }

$activeBranchResult = Invoke-GitBounded @('-C',$repoRoot,'rev-parse','--abbrev-ref','HEAD') $GitTimeoutSeconds
if ($activeBranchResult.ExitCode -ne 0) { throw "CANONICAL_BRANCH_READ_FAILED=$($activeBranchResult.StdErr)" }
$activeBranch = $activeBranchResult.StdOut.Trim()
if ($activeBranch -ne $branch) {
  Write-Receipt 'BLOCKED_CANONICAL_BRANCH_MISMATCH' $false $false $false '' $false $false $false $false -1 '' '' '' "active_branch=$activeBranch"
  exit 3
}

$localBeforeResult = Invoke-GitBounded @('-C',$repoRoot,'rev-parse','HEAD') $GitTimeoutSeconds
if ($localBeforeResult.ExitCode -ne 0) { throw 'CANONICAL_LOCAL_HEAD_READ_FAILED' }
$localBefore = $localBeforeResult.StdOut.Trim()

$statusResult = Invoke-GitBounded @('-C',$repoRoot,'status','--porcelain=v1','-uall') $GitTimeoutSeconds
if ($statusResult.ExitCode -ne 0) { throw "CANONICAL_F_REPO_STATUS_FAILED=$($statusResult.StdErr)" }
$dirtyLines = @($statusResult.StdOut -split "`r?`n" | Where-Object { $_ })
$dirtyBefore = $dirtyLines.Count -gt 0
$snapshotWritten = $false
$stashCreated = $false
$stashRef = ''
$script:snapshotPayload = [ordered]@{
  schema_version = 4
  slot_id = 'height_difference_2'
  task_id = $taskId
  attempt_id = $attemptId
  captured_at = (Get-Date).ToUniversalTime().ToString('o')
  repo_root = $repoRoot
  branch = $branch
  local_head_before = $localBefore
  dirty_before = $dirtyBefore
  dirty_entry_count = $dirtyLines.Count
  dirty_entries = $dirtyLines
  snapshot_kind = 'pre_recovery_git_status_clean_or_dirty'
  snapshot_capture_phase = 'memory_before_stash_fetch_sync'
  snapshot_publication_phase = 'receipt_exit_after_sync_or_on_blocked_exit'
  recovery_policy = 'snapshot_always_stash_if_dirty_no_auto_pop_then_ff_only'
  hard_reset_forbidden = $true
  stash_required = $dirtyBefore
  final_ready = $false
}

if ($dirtyBefore) {
  $stashMessage = "height_difference_2 attempt020 guarded recovery $((Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssZ'))"
  $stashResult = Invoke-GitBounded @('-C',$repoRoot,'stash','push','--include-untracked','--message',$stashMessage) $GitTimeoutSeconds
  if ($stashResult.ExitCode -ne 0) {
    Write-Receipt 'BLOCKED_CANONICAL_STASH_FAILED' $true $snapshotWritten $false '' $false $false $false $false -1 $localBefore '' $localBefore ($stashResult.StdErr.Trim())
    exit 2
  }
  $stashVerify = Invoke-GitBounded @('-C',$repoRoot,'rev-parse','--verify','refs/stash') $GitTimeoutSeconds
  if ($stashVerify.ExitCode -ne 0 -or -not $stashVerify.StdOut.Trim()) {
    Write-Receipt 'BLOCKED_CANONICAL_STASH_REF_MISSING' $true $snapshotWritten $false '' $false $false $false $false -1 $localBefore '' $localBefore 'refs/stash unavailable after stash push'
    exit 2
  }
  $stashRef = $stashVerify.StdOut.Trim()
  $stashCreated = $true

  $cleanVerify = Invoke-GitBounded @('-C',$repoRoot,'status','--porcelain=v1','-uall') $GitTimeoutSeconds
  if ($cleanVerify.ExitCode -ne 0 -or $cleanVerify.StdOut.Trim()) {
    Write-Receipt 'BLOCKED_CANONICAL_REPO_NOT_CLEAN_AFTER_STASH' $true $snapshotWritten $stashCreated $stashRef $false $false $false $false -1 $localBefore '' $localBefore ($cleanVerify.StdOut.Trim())
    exit 2
  }
}

$fetch = Invoke-GitBounded @('-C',$repoRoot,'fetch','--atomic','origin',$branch,'--prune') $GitTimeoutSeconds
if ($fetch.ExitCode -ne 0) {
  Write-Receipt 'BLOCKED_CANONICAL_FETCH_FAILED' $dirtyBefore $snapshotWritten $stashCreated $stashRef $true $false $false $false -1 $localBefore '' $localBefore ($fetch.StdErr.Trim())
  exit 4
}
$remoteHeadResult = Invoke-GitBounded @('-C',$repoRoot,'rev-parse',"origin/$branch") $GitTimeoutSeconds
if ($remoteHeadResult.ExitCode -ne 0 -or -not $remoteHeadResult.StdOut.Trim()) {
  Write-Receipt 'BLOCKED_REMOTE_HEAD_READ_FAILED' $dirtyBefore $snapshotWritten $stashCreated $stashRef $true $false $false $false -1 $localBefore '' $localBefore 'origin branch head unavailable'
  exit 5
}
$remoteHead = $remoteHeadResult.StdOut.Trim()

$resetApplied = $false
if ($localBefore -ne $remoteHead) {
  $ancestor = Invoke-GitBounded @('-C',$repoRoot,'merge-base','--is-ancestor',$localBefore,$remoteHead) $GitTimeoutSeconds
  if ($ancestor.ExitCode -ne 0) {
    Write-Receipt 'BLOCKED_CANONICAL_NON_FF_DIVERGENCE' $dirtyBefore $snapshotWritten $stashCreated $stashRef $true $false $false $false -1 $localBefore $remoteHead $localBefore 'Local canonical branch is not an ancestor of remote; hard reset is forbidden. Preserve state and reconcile separately.'
    exit 6
  }
  $fastForward = Invoke-GitBounded @('-C',$repoRoot,'merge','--ff-only',"origin/$branch") $GitTimeoutSeconds
  if ($fastForward.ExitCode -ne 0) {
    Write-Receipt 'BLOCKED_CANONICAL_FF_ONLY_FAILED' $dirtyBefore $snapshotWritten $stashCreated $stashRef $true $false $false $false -1 $localBefore $remoteHead $localBefore ($fastForward.StdErr.Trim())
    exit 6
  }
}

$localAfterResult = Invoke-GitBounded @('-C',$repoRoot,'rev-parse','HEAD') $GitTimeoutSeconds
$localAfter = $localAfterResult.StdOut.Trim()
if ($localAfterResult.ExitCode -ne 0 -or $localAfter -ne $remoteHead) {
  Write-Receipt 'BLOCKED_REMOTE_HEAD_NOT_APPLIED' $dirtyBefore $snapshotWritten $stashCreated $stashRef $true $false $false $false -1 $localBefore $remoteHead $localAfter 'local head does not exactly match remote head after ff-only synchronization'
  exit 7
}
$postSyncStatus = Invoke-GitBounded @('-C',$repoRoot,'status','--porcelain=v1','-uall') $GitTimeoutSeconds
if ($postSyncStatus.ExitCode -ne 0 -or $postSyncStatus.StdOut.Trim()) {
  Write-Receipt 'BLOCKED_CANONICAL_REPO_DIRTY_AFTER_SYNC' $dirtyBefore $snapshotWritten $stashCreated $stashRef $true $false $false $false -1 $localBefore $remoteHead $localAfter ($postSyncStatus.StdOut.Trim())
  exit 7
}

$helper = Join-Path $repoRoot $helperRel
if (-not (Test-Path -LiteralPath $helper -PathType Leaf)) {
  Write-Receipt 'BLOCKED_ATTEMPT_020_HELPER_MISSING' $dirtyBefore $snapshotWritten $stashCreated $stashRef $true $false $false $false -1 $localBefore $remoteHead $localAfter $helper
  exit 8
}
$helperBlobResult = Invoke-GitBounded @('-C',$repoRoot,'hash-object','--',$helper) $GitTimeoutSeconds
$helperBlob = $helperBlobResult.StdOut.Trim()
if ($helperBlobResult.ExitCode -ne 0 -or $helperBlob -ne $expectedHelperBlob) {
  Write-Receipt 'BLOCKED_ATTEMPT_020_HELPER_BLOB_MISMATCH' $dirtyBefore $snapshotWritten $stashCreated $stashRef $true $false $false $false -1 $localBefore $remoteHead $localAfter "helper_blob=$helperBlob"
  exit 9
}

$helperProcess = Start-Process -FilePath 'powershell.exe' -ArgumentList @('-NoProfile','-ExecutionPolicy','Bypass','-File',('"' + $helper + '"')) -WorkingDirectory $repoRoot -PassThru -WindowStyle Hidden
$helperTimedOut = $false
try {
  Wait-Process -Id $helperProcess.Id -Timeout $HelperTimeoutSeconds -ErrorAction Stop
} catch {
  $helperTimedOut = $true
  Stop-Process -Id $helperProcess.Id -Force -ErrorAction SilentlyContinue
}
$helperProcess.Refresh()
$helperExit = if ($helperTimedOut) { 124 } elseif ($null -eq $helperProcess.ExitCode) { 1 } else { [int]$helperProcess.ExitCode }
$status = if ($helperTimedOut) {
  'BLOCKED_ATTEMPT_020_EXISTING_F_RUNNER_RECOVERY_TIMEOUT'
} elseif ($helperExit -eq 0) {
  'ATTEMPT_020_EXISTING_F_RUNNER_RECOVERY_INVOKED'
} else {
  'BLOCKED_ATTEMPT_020_EXISTING_F_RUNNER_RECOVERY_FAILED'
}
$detail = "helper_blob=$helperBlob;sync_mode=atomic_fetch_ff_only_exact_head_no_hard_reset;snapshot_capture=memory;snapshot_publish=receipt_exit"
if ($stashCreated) { $detail += ";stash_ref=$stashRef;stash_restore=manual_only" }
Write-Receipt $status $dirtyBefore $snapshotWritten $stashCreated $stashRef $true $false $true $helperTimedOut $helperExit $localBefore $remoteHead $localAfter $detail
exit $helperExit
