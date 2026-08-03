[CmdletBinding()]
param(
  [string]$RepoRoot = "",
  [string]$RepoFullName = "cagdascagdas100/chat_gpt_clone_1",
  [string]$MainBranch = "codex/aays-single-runner-v5-20260706",
  [string]$WorkRoot = "",
  [int]$IntervalSeconds = 60,
  [int]$MaxTasks = 1,
  [int]$StaleMinutes = 15,
  [switch]$NoPanel,
  [switch]$NoLoop,
  [switch]$NoPush
)

$ErrorActionPreference = "Stop"

function Invoke-CanonicalGit([string]$Root, [string[]]$GitArgs) {
  $old = $ErrorActionPreference
  try {
    $ErrorActionPreference = "Continue"
    $output = & git -c "safe.directory=$Root" -C $Root @GitArgs 2>&1
    $code = $LASTEXITCODE
  } finally {
    $ErrorActionPreference = $old
  }
  return [pscustomobject]@{ code=$code; output=(($output | Out-String).Trim()) }
}
function Assert-CanonicalGit([object]$Result, [string]$Code) {
  if ($Result.code -ne 0) { throw ("{0}: {1}" -f $Code, $Result.output) }
}
function Write-JsonAtomic([string]$Path, [object]$Payload) {
  $parent = Split-Path -Parent $Path
  if (-not (Test-Path -LiteralPath $parent)) { New-Item -ItemType Directory -Force -Path $parent | Out-Null }
  $temp = "$Path.tmp.$PID.$([guid]::NewGuid().ToString('N'))"
  [System.IO.File]::WriteAllText($temp, (($Payload | ConvertTo-Json -Depth 30) + "`n"), [System.Text.UTF8Encoding]::new($false))
  Move-Item -LiteralPath $temp -Destination $Path -Force
}

if ([string]::IsNullOrWhiteSpace($RepoRoot)) {
  $RepoRoot = Join-Path $PSScriptRoot "..\..\..\.."
}
$repoRootResolved = Resolve-Path -LiteralPath $RepoRoot -ErrorAction Stop
$repoRoot = [System.IO.Path]::GetFullPath($repoRootResolved.Path).TrimEnd('\')
if ($repoRoot.StartsWith('C:\', [System.StringComparison]::OrdinalIgnoreCase)) {
  throw "BLOCKED_C_DRIVE_NOT_CANONICAL=$repoRoot"
}
if (-not (Test-Path -LiteralPath (Join-Path $repoRoot '.git'))) {
  throw "BLOCKED_CANONICAL_REPO_GIT_MISSING=$repoRoot"
}

$branchResult = Invoke-CanonicalGit $repoRoot @('branch','--show-current')
Assert-CanonicalGit $branchResult 'BLOCKED_CANONICAL_BRANCH_READ_FAILED'
$currentBranch = ([string]$branchResult.output).Trim()
if ($currentBranch -ne $MainBranch) {
  throw "BLOCKED_CANONICAL_BRANCH_MISMATCH_CURRENT=$currentBranch`_EXPECTED=$MainBranch"
}

$shallowResult = Invoke-CanonicalGit $repoRoot @('rev-parse','--is-shallow-repository')
Assert-CanonicalGit $shallowResult 'BLOCKED_CANONICAL_SHALLOW_CHECK_FAILED'
$refspec = "+refs/heads/$MainBranch`:refs/remotes/origin/$MainBranch"
$fetchArgs = @('fetch','--no-tags')
if (([string]$shallowResult.output).Trim().ToLowerInvariant() -eq 'true') { $fetchArgs += '--unshallow' }
$fetchArgs += @('origin',$refspec)
$fetchResult = Invoke-CanonicalGit $repoRoot $fetchArgs
Assert-CanonicalGit $fetchResult 'BLOCKED_CANONICAL_REMOTE_FETCH_FAILED'

$legacyLockGuard = Join-Path $repoRoot 'docs\chatgpt_status\_shared\automation\PREPARE_AAYS_LEGACY_RUNNER_LOCK_COMPAT_20260803.py'
if (-not (Test-Path -LiteralPath $legacyLockGuard)) {
  throw "Missing legacy runner lock compatibility guard: $legacyLockGuard"
}
$guardArgs = @(
  $legacyLockGuard,
  "--repo-root", $repoRoot,
  "--main-branch", $MainBranch,
  "--stale-minutes", "$StaleMinutes"
)
$guardOutput = & python @guardArgs 2>&1
$guardExitCode = $LASTEXITCODE
$guardText = (($guardOutput | Out-String).Trim())
if ($guardExitCode -ne 0) { throw ("BLOCKED_LEGACY_LOCK_GUARD_FAILED: " + $guardText) }
try {
  $guardResult = $guardText | ConvertFrom-Json
  $guardState = ([string]$guardResult.state).Trim().ToUpperInvariant()
} catch {
  throw ("BLOCKED_LEGACY_LOCK_GUARD_OUTPUT_INVALID: " + $guardText)
}

$statusResult = Invoke-CanonicalGit $repoRoot @('status','--porcelain','--untracked-files=no')
Assert-CanonicalGit $statusResult 'BLOCKED_CANONICAL_TRACKED_STATUS_FAILED'
if (-not [string]::IsNullOrWhiteSpace([string]$statusResult.output)) {
  throw ("BLOCKED_CANONICAL_TRACKED_WORKTREE_DIRTY: " + $statusResult.output)
}

$localBeforeResult = Invoke-CanonicalGit $repoRoot @('rev-parse','HEAD')
Assert-CanonicalGit $localBeforeResult 'BLOCKED_CANONICAL_LOCAL_HEAD_READ_FAILED'
$remoteResult = Invoke-CanonicalGit $repoRoot @('rev-parse',("refs/remotes/origin/" + $MainBranch))
Assert-CanonicalGit $remoteResult 'BLOCKED_CANONICAL_REMOTE_HEAD_READ_FAILED'
$localBefore = ([string]$localBeforeResult.output).Trim()
$remoteHead = ([string]$remoteResult.output).Trim()
$fastForwardApplied = $false
$syncSafeGuardStates = @('NO_LOCK','REMOVE_DEAD_LEGACY_LOCK','STOP_VERIFIED_STALE_LEGACY_DAEMON')
$liveGuardStates = @('MIGRATE_VERIFIED_FRESH_LEGACY_LOCK','NOT_LEGACY')
$launcherSyncStatus = 'PASS_ALREADY_CURRENT'
if ($localBefore -ne $remoteHead) {
  if ($syncSafeGuardStates -contains $guardState) {
    $mergeResult = Invoke-CanonicalGit $repoRoot @('merge','--ff-only',("refs/remotes/origin/" + $MainBranch))
    Assert-CanonicalGit $mergeResult 'BLOCKED_CANONICAL_FAST_FORWARD_FAILED'
    $fastForwardApplied = $true
    $launcherSyncStatus = 'PASS_FAST_FORWARD_APPLIED'
  } elseif ($liveGuardStates -contains $guardState) {
    throw "BLOCKED_CANONICAL_HEAD_BEHIND_WITH_POSSIBLE_LIVE_RUNNER_GUARD_STATE=$guardState`_LOCAL=$localBefore`_REMOTE=$remoteHead"
  } else {
    throw "BLOCKED_CANONICAL_HEAD_BEHIND_WITH_UNKNOWN_GUARD_STATE=$guardState"
  }
}

$localAfterResult = Invoke-CanonicalGit $repoRoot @('rev-parse','HEAD')
Assert-CanonicalGit $localAfterResult 'BLOCKED_CANONICAL_LOCAL_HEAD_AFTER_SYNC_READ_FAILED'
$localAfter = ([string]$localAfterResult.output).Trim()
if ($localAfter -ne $remoteHead) {
  throw "BLOCKED_CANONICAL_HEAD_MISMATCH_AFTER_SYNC_LOCAL=$localAfter`_REMOTE=$remoteHead"
}

$starter = Join-Path $repoRoot 'docs\chatgpt_status\_shared\automation\START_AAYS_SINGLE_RUNNER_WITH_PANEL_20260706.ps1'
if (-not (Test-Path -LiteralPath $starter)) {
  throw "Missing canonical starter: $starter"
}
$wrapperBlobResult = Invoke-CanonicalGit $repoRoot @('hash-object','--',$MyInvocation.MyCommand.Path)
Assert-CanonicalGit $wrapperBlobResult 'BLOCKED_CANONICAL_WRAPPER_BLOB_READ_FAILED'
$guardBlobResult = Invoke-CanonicalGit $repoRoot @('hash-object','--',$legacyLockGuard)
Assert-CanonicalGit $guardBlobResult 'BLOCKED_CANONICAL_GUARD_BLOB_READ_FAILED'
$starterBlobResult = Invoke-CanonicalGit $repoRoot @('hash-object','--',$starter)
Assert-CanonicalGit $starterBlobResult 'BLOCKED_CANONICAL_STARTER_BLOB_READ_FAILED'
$wrapperBlob = ([string]$wrapperBlobResult.output).Trim()
$guardBlob = ([string]$guardBlobResult.output).Trim()
$starterBlob = ([string]$starterBlobResult.output).Trim()
$syncAt = (Get-Date).ToUniversalTime().ToString('o')

$args = @(
  "-File", $starter,
  "-RepoRoot", $repoRoot,
  "-RepoFullName", $RepoFullName,
  "-MainBranch", $MainBranch,
  "-WorkRoot", $WorkRoot,
  "-IntervalSeconds", "$IntervalSeconds",
  "-MaxTasks", "$MaxTasks",
  "-StaleMinutes", "$StaleMinutes"
)
if ($NoPanel) { $args += "-NoPanel" }
if ($NoLoop) { $args += "-NoLoop" }
if ($NoPush) { $args += "-NoPush" }

& powershell -NoProfile -ExecutionPolicy Bypass @args
$starterExitCode = $LASTEXITCODE

$bootstrapStatus = Join-Path $repoRoot 'docs\chatgpt_status\_shared\status\runner_bootstrap_latest.json'
if ($starterExitCode -eq 0) {
  if (-not (Test-Path -LiteralPath $bootstrapStatus -PathType Leaf)) {
    throw "BLOCKED_BOOTSTRAP_STATUS_MISSING_AFTER_CANONICAL_START"
  }
  try {
    $state = Get-Content -Raw -LiteralPath $bootstrapStatus -Encoding UTF8 | ConvertFrom-Json
    Add-Member -InputObject $state -NotePropertyName launcher_sync_status -NotePropertyValue $launcherSyncStatus -Force
    Add-Member -InputObject $state -NotePropertyName launcher_sync_at -NotePropertyValue $syncAt -Force
    Add-Member -InputObject $state -NotePropertyName launcher_refresh_mode -NotePropertyValue 'FETCH_PLUS_FF_ONLY_NO_RESET' -Force
    Add-Member -InputObject $state -NotePropertyName launcher_guard_state -NotePropertyValue $guardState -Force
    Add-Member -InputObject $state -NotePropertyName launcher_branch_verified -NotePropertyValue $true -Force
    Add-Member -InputObject $state -NotePropertyName launcher_tracked_worktree_clean -NotePropertyValue $true -Force
    Add-Member -InputObject $state -NotePropertyName launcher_local_head_before -NotePropertyValue $localBefore -Force
    Add-Member -InputObject $state -NotePropertyName launcher_local_head -NotePropertyValue $localAfter -Force
    Add-Member -InputObject $state -NotePropertyName launcher_remote_head -NotePropertyValue $remoteHead -Force
    Add-Member -InputObject $state -NotePropertyName launcher_heads_match -NotePropertyValue ($localAfter -eq $remoteHead) -Force
    Add-Member -InputObject $state -NotePropertyName launcher_fast_forward_applied -NotePropertyValue $fastForwardApplied -Force
    Add-Member -InputObject $state -NotePropertyName launcher_wrapper_blob_sha -NotePropertyValue $wrapperBlob -Force
    Add-Member -InputObject $state -NotePropertyName launcher_legacy_guard_blob_sha -NotePropertyValue $guardBlob -Force
    Add-Member -InputObject $state -NotePropertyName launcher_starter_blob_sha -NotePropertyValue $starterBlob -Force
    Add-Member -InputObject $state -NotePropertyName launcher_no_reset_hard -NotePropertyValue $true -Force
    Write-JsonAtomic $bootstrapStatus $state
  } catch {
    throw ("BLOCKED_BOOTSTRAP_SYNC_EVIDENCE_WRITE_FAILED: " + $_.Exception.Message)
  }
}

exit $starterExitCode
