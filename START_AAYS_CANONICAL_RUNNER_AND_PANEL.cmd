@echo off
setlocal
set "AAYS_CANONICAL_ROOT=%~dp0"
set "AAYS_CMD_FILE=%~f0"
set "AAYS_BOOTSTRAP_FILE=%TEMP%\aays_canonical_bootstrap_%RANDOM%_%RANDOM%.ps1"
powershell -NoProfile -ExecutionPolicy Bypass -Command "$s=[IO.File]::ReadAllText($env:AAYS_CMD_FILE);$m='# AAYS_'+'POWERSHELL_BOOTSTRAP';$i=$s.IndexOf($m);if($i -lt 0){exit 97};$b=$s.Substring($i+$m.Length).TrimStart([char]13,[char]10);[IO.File]::WriteAllText($env:AAYS_BOOTSTRAP_FILE,$b,[Text.UTF8Encoding]::new($false));& $env:AAYS_BOOTSTRAP_FILE;exit $LASTEXITCODE"
set "AAYS_EXIT_CODE=%ERRORLEVEL%"
del /q "%AAYS_BOOTSTRAP_FILE%" >nul 2>&1
endlocal & exit /b %AAYS_EXIT_CODE%
# AAYS_POWERSHELL_BOOTSTRAP
$ErrorActionPreference = 'Stop'
$root = [System.IO.Path]::GetFullPath([string]$env:AAYS_CANONICAL_ROOT).TrimEnd('\')
$branch = 'codex/aays-single-runner-v5-20260706'
$staleMinutes = 15
$rootLauncherRepoPath = 'START_AAYS_CANONICAL_RUNNER_AND_PANEL.cmd'
$bootstrapStatusRepoPath = 'docs/chatgpt_status/_shared/status/runner_bootstrap_latest.json'

function Invoke-AaysGit {
  param([string[]]$Arguments)
  $old = $ErrorActionPreference
  try {
    $ErrorActionPreference = 'Continue'
    $output = & git -c "safe.directory=$root" -C $root @Arguments 2>&1
    $code = $LASTEXITCODE
  } finally {
    $ErrorActionPreference = $old
  }
  $text = ($output | Out-String).TrimEnd()
  if ($code -ne 0) { throw ("GIT_FAILED[{0}]: {1}" -f ($Arguments -join ' '), $text) }
  return $text
}

if ([string]::IsNullOrWhiteSpace($root) -or $root.StartsWith('C:\', [System.StringComparison]::OrdinalIgnoreCase)) {
  throw "BLOCKED_CANONICAL_ROOT_INVALID=$root"
}
if (-not (Test-Path -LiteralPath (Join-Path $root '.git'))) {
  throw "BLOCKED_CANONICAL_REPO_GIT_MISSING=$root"
}

$currentBranch = (Invoke-AaysGit @('branch','--show-current')).Trim()
if ($currentBranch -ne $branch) {
  throw "BLOCKED_CANONICAL_BRANCH_MISMATCH_CURRENT=$currentBranch`_EXPECTED=$branch"
}
$trackedStatus = Invoke-AaysGit @('status','--porcelain','--untracked-files=no')
if (-not [string]::IsNullOrWhiteSpace($trackedStatus)) {
  throw ("BLOCKED_CANONICAL_TRACKED_WORKTREE_DIRTY: " + $trackedStatus)
}

$executingRootLauncherBlob = (Invoke-AaysGit @('hash-object','--',$env:AAYS_CMD_FILE)).Trim()
if ($executingRootLauncherBlob -notmatch '^[0-9a-f]{40}$') {
  throw "BLOCKED_EXECUTING_ROOT_LAUNCHER_BLOB_INVALID=$executingRootLauncherBlob"
}
$reexecDepth = 0
if (-not [string]::IsNullOrWhiteSpace([string]$env:AAYS_ROOT_LAUNCHER_REEXEC_DEPTH)) {
  if (-not [int]::TryParse([string]$env:AAYS_ROOT_LAUNCHER_REEXEC_DEPTH, [ref]$reexecDepth)) {
    throw "BLOCKED_ROOT_LAUNCHER_REEXEC_DEPTH_INVALID=$($env:AAYS_ROOT_LAUNCHER_REEXEC_DEPTH)"
  }
}
if ($reexecDepth -lt 0 -or $reexecDepth -gt 1) {
  throw "BLOCKED_ROOT_LAUNCHER_REEXEC_DEPTH_OUT_OF_RANGE=$reexecDepth"
}

$shallow = (Invoke-AaysGit @('rev-parse','--is-shallow-repository')).Trim().ToLowerInvariant()
$refspec = "+refs/heads/$branch`:refs/remotes/origin/$branch"
$fetchArgs = @('fetch','--no-tags')
if ($shallow -eq 'true') { $fetchArgs += '--unshallow' }
$fetchArgs += @('origin',$refspec)
[void](Invoke-AaysGit $fetchArgs)

$remoteRef = "refs/remotes/origin/$branch"
$remoteRootLauncherBlobBeforeSync = (Invoke-AaysGit @('rev-parse',("$remoteRef`:$rootLauncherRepoPath"))).Trim()
if ($remoteRootLauncherBlobBeforeSync -notmatch '^[0-9a-f]{40}$') {
  throw "BLOCKED_REMOTE_ROOT_LAUNCHER_BLOB_INVALID=$remoteRootLauncherBlobBeforeSync"
}
$guardRepoPath = 'docs/chatgpt_status/_shared/automation/PREPARE_AAYS_LEGACY_RUNNER_LOCK_COMPAT_20260803.py'
$tempGuard = Join-Path $env:TEMP ("aays_legacy_lock_guard_{0}_{1}.py" -f $PID,[guid]::NewGuid().ToString('N'))

try {
  $guardSource = Invoke-AaysGit @('show',("$remoteRef`:$guardRepoPath"))
  [System.IO.File]::WriteAllText($tempGuard, ($guardSource + "`n"), [System.Text.UTF8Encoding]::new($false))
  $guardOutput = & python $tempGuard --repo-root $root --main-branch $branch --stale-minutes $staleMinutes 2>&1
  $guardExit = $LASTEXITCODE
  $guardText = ($guardOutput | Out-String).Trim()
  if ($guardExit -ne 0) { throw ("BLOCKED_REMOTE_LEGACY_LOCK_GUARD_FAILED: " + $guardText) }
  try {
    $guardState = ([string](($guardText | ConvertFrom-Json).state)).Trim().ToUpperInvariant()
  } catch {
    throw ("BLOCKED_REMOTE_LEGACY_LOCK_GUARD_OUTPUT_INVALID: " + $guardText)
  }

  $localHead = (Invoke-AaysGit @('rev-parse','HEAD')).Trim()
  $remoteHead = (Invoke-AaysGit @('rev-parse',$remoteRef)).Trim()
  $syncSafeStates = @('NO_LOCK','REMOVE_DEAD_LEGACY_LOCK','STOP_VERIFIED_STALE_LEGACY_DAEMON')
  $liveStates = @('MIGRATE_VERIFIED_FRESH_LEGACY_LOCK','NOT_LEGACY')
  $fastForwardApplied = $false
  if ($localHead -ne $remoteHead) {
    if ($syncSafeStates -contains $guardState) {
      [void](Invoke-AaysGit @('merge','--ff-only',$remoteRef))
      $fastForwardApplied = $true
    } elseif ($liveStates -contains $guardState) {
      throw "BLOCKED_CANONICAL_HEAD_BEHIND_WITH_POSSIBLE_LIVE_RUNNER_GUARD_STATE=$guardState`_LOCAL=$localHead`_REMOTE=$remoteHead"
    } else {
      throw "BLOCKED_CANONICAL_HEAD_BEHIND_WITH_UNKNOWN_GUARD_STATE=$guardState"
    }
  }

  $localAfter = (Invoke-AaysGit @('rev-parse','HEAD')).Trim()
  $remoteAfter = (Invoke-AaysGit @('rev-parse',$remoteRef)).Trim()
  if ($localAfter -ne $remoteAfter) {
    throw "BLOCKED_CANONICAL_HEAD_MISMATCH_AFTER_BOOTSTRAP_LOCAL=$localAfter`_REMOTE=$remoteAfter"
  }

  $remoteRootLauncherBlobAfterSync = (Invoke-AaysGit @('rev-parse',("$remoteRef`:$rootLauncherRepoPath"))).Trim()
  $diskRootLauncherBlobAfterSync = (Invoke-AaysGit @('hash-object','--',$env:AAYS_CMD_FILE)).Trim()
  foreach ($blobCheck in @($remoteRootLauncherBlobAfterSync,$diskRootLauncherBlobAfterSync)) {
    if ($blobCheck -notmatch '^[0-9a-f]{40}$') {
      throw "BLOCKED_ROOT_LAUNCHER_SYNC_BLOB_INVALID=$blobCheck"
    }
  }
  if ($remoteRootLauncherBlobBeforeSync -ne $remoteRootLauncherBlobAfterSync) {
    throw "BLOCKED_REMOTE_ROOT_LAUNCHER_CHANGED_DURING_BOOTSTRAP_BEFORE=$remoteRootLauncherBlobBeforeSync`_AFTER=$remoteRootLauncherBlobAfterSync"
  }
  if ($diskRootLauncherBlobAfterSync -ne $remoteRootLauncherBlobAfterSync) {
    throw "BLOCKED_DISK_ROOT_LAUNCHER_BLOB_MISMATCH_AFTER_SYNC_DISK=$diskRootLauncherBlobAfterSync`_REMOTE=$remoteRootLauncherBlobAfterSync"
  }
  if ($executingRootLauncherBlob -ne $remoteRootLauncherBlobAfterSync) {
    if ($reexecDepth -ge 1) {
      throw "BLOCKED_ROOT_LAUNCHER_REEXEC_LOOP_EXECUTING=$executingRootLauncherBlob`_REMOTE=$remoteRootLauncherBlobAfterSync"
    }
    $env:AAYS_ROOT_LAUNCHER_REEXEC_DEPTH = '1'
    & $env:ComSpec /d /c ('"' + $env:AAYS_CMD_FILE + '"')
    exit $LASTEXITCODE
  }

  $starter = Join-Path $root 'docs\chatgpt_status\_shared\automation\START_AAYS_SINGLE_RUNNER_WITH_PANEL_20260706.ps1'
  if (-not (Test-Path -LiteralPath $starter -PathType Leaf)) {
    throw "BLOCKED_CANONICAL_STARTER_MISSING_AFTER_BOOTSTRAP=$starter"
  }
  $rootLauncherBlob = $executingRootLauncherBlob
  $remoteGuardBlob = (Invoke-AaysGit @('rev-parse',("$remoteRef`:$guardRepoPath"))).Trim()
  $starterBlob = (Invoke-AaysGit @('hash-object','--',$starter)).Trim()
  foreach ($blobCheck in @($rootLauncherBlob,$remoteGuardBlob,$starterBlob)) {
    if ($blobCheck -notmatch '^[0-9a-f]{40}$') {
      throw "BLOCKED_CANONICAL_CONTROL_BLOB_PROOF_INVALID=$blobCheck"
    }
  }
  & powershell -NoProfile -ExecutionPolicy Bypass -File $starter -RepoRoot $root
  $starterExitCode = $LASTEXITCODE
  if ($starterExitCode -ne 0) { exit $starterExitCode }

  $bootstrapStatus = Join-Path $root 'docs\chatgpt_status\_shared\status\runner_bootstrap_latest.json'
  if (-not (Test-Path -LiteralPath $bootstrapStatus -PathType Leaf)) {
    throw "BLOCKED_BOOTSTRAP_STATUS_MISSING_AFTER_CANONICAL_START"
  }
  try {
    $state = Get-Content -Raw -LiteralPath $bootstrapStatus -Encoding UTF8 | ConvertFrom-Json
    Add-Member -InputObject $state -NotePropertyName root_launcher_guard_state -NotePropertyValue $guardState -Force
    Add-Member -InputObject $state -NotePropertyName root_launcher_sync_at -NotePropertyValue ((Get-Date).ToUniversalTime().ToString('o')) -Force
    Add-Member -InputObject $state -NotePropertyName root_launcher_refresh_mode -NotePropertyValue 'REMOTE_GUARD_PLUS_FF_ONLY_DIRECT_STARTER' -Force
    Add-Member -InputObject $state -NotePropertyName root_launcher_local_head -NotePropertyValue $localAfter -Force
    Add-Member -InputObject $state -NotePropertyName root_launcher_remote_head -NotePropertyValue $remoteAfter -Force
    Add-Member -InputObject $state -NotePropertyName root_launcher_heads_match -NotePropertyValue ($localAfter -eq $remoteAfter) -Force
    Add-Member -InputObject $state -NotePropertyName root_launcher_fast_forward_applied -NotePropertyValue $fastForwardApplied -Force
    Add-Member -InputObject $state -NotePropertyName root_launcher_blob_sha -NotePropertyValue $rootLauncherBlob -Force
    Add-Member -InputObject $state -NotePropertyName root_launcher_execution_blob_sha_before_sync -NotePropertyValue $executingRootLauncherBlob -Force
    Add-Member -InputObject $state -NotePropertyName root_launcher_remote_blob_sha_after_sync -NotePropertyValue $remoteRootLauncherBlobAfterSync -Force
    Add-Member -InputObject $state -NotePropertyName root_launcher_execution_source_verified -NotePropertyValue ($executingRootLauncherBlob -eq $remoteRootLauncherBlobAfterSync) -Force
    Add-Member -InputObject $state -NotePropertyName root_launcher_reexec_depth -NotePropertyValue $reexecDepth -Force
    Add-Member -InputObject $state -NotePropertyName root_launcher_remote_guard_blob_sha -NotePropertyValue $remoteGuardBlob -Force
    Add-Member -InputObject $state -NotePropertyName root_launcher_starter_blob_sha -NotePropertyValue $starterBlob -Force
    Add-Member -InputObject $state -NotePropertyName root_launcher_contract_version -NotePropertyValue 4 -Force
    Add-Member -InputObject $state -NotePropertyName root_launcher_bootstrap_publish_mode -NotePropertyValue 'PATH_SCOPED_COMMIT_PUSH_REMOTE_READBACK' -Force
    Add-Member -InputObject $state -NotePropertyName root_launcher_bootstrap_remote_readback_required -NotePropertyValue $true -Force
    Add-Member -InputObject $state -NotePropertyName root_launcher_no_reset_hard -NotePropertyValue $true -Force
    Add-Member -InputObject $state -NotePropertyName root_launcher_direct_starter_handoff -NotePropertyValue $true -Force
    Add-Member -InputObject $state -NotePropertyName root_launcher_wrapper_reentry_avoided -NotePropertyValue $true -Force
    $tempStatus = "$bootstrapStatus.tmp.$PID.$([guid]::NewGuid().ToString('N'))"
    [System.IO.File]::WriteAllText($tempStatus, (($state | ConvertTo-Json -Depth 30) + "`n"), [System.Text.UTF8Encoding]::new($false))
    Move-Item -LiteralPath $tempStatus -Destination $bootstrapStatus -Force
  } catch {
    throw ("BLOCKED_ROOT_BOOTSTRAP_EVIDENCE_WRITE_FAILED: " + $_.Exception.Message)
  }

  $bootstrapLocalBlob = (Invoke-AaysGit @('hash-object','--',$bootstrapStatus)).Trim()
  if ($bootstrapLocalBlob -notmatch '^[0-9a-f]{40}$') {
    throw "BLOCKED_BOOTSTRAP_LOCAL_BLOB_INVALID=$bootstrapLocalBlob"
  }
  [void](Invoke-AaysGit @('add','--',$bootstrapStatusRepoPath))
  $stagedBootstrap = (Invoke-AaysGit @('diff','--cached','--name-only','--',$bootstrapStatusRepoPath)).Trim()
  if ($stagedBootstrap -ne $bootstrapStatusRepoPath) {
    throw "BLOCKED_BOOTSTRAP_PATH_NOT_STAGED_EXACTLY=$stagedBootstrap"
  }
  [void](Invoke-AaysGit @('commit','--only','-m','aays: publish canonical bootstrap contract v4 ack','--',$bootstrapStatusRepoPath))
  $bootstrapPublishCommit = (Invoke-AaysGit @('rev-parse','HEAD')).Trim()
  if ($bootstrapPublishCommit -notmatch '^[0-9a-f]{40}$') {
    throw "BLOCKED_BOOTSTRAP_PUBLISH_COMMIT_INVALID=$bootstrapPublishCommit"
  }
  [void](Invoke-AaysGit @('push','origin',("HEAD:refs/heads/$branch")))
  [void](Invoke-AaysGit $fetchArgs)

  $remoteBootstrapBlob = (Invoke-AaysGit @('rev-parse',("$remoteRef`:$bootstrapStatusRepoPath"))).Trim()
  if ($remoteBootstrapBlob -ne $bootstrapLocalBlob) {
    throw "BLOCKED_BOOTSTRAP_REMOTE_BLOB_MISMATCH_LOCAL=$bootstrapLocalBlob`_REMOTE=$remoteBootstrapBlob"
  }
  try {
    $remoteBootstrapState = (Invoke-AaysGit @('show',("$remoteRef`:$bootstrapStatusRepoPath"))) | ConvertFrom-Json
  } catch {
    throw ("BLOCKED_BOOTSTRAP_REMOTE_READBACK_JSON_INVALID: " + $_.Exception.Message)
  }
  $remoteAckValid =
    ([int]$remoteBootstrapState.root_launcher_contract_version -eq 4) -and
    ([bool]$remoteBootstrapState.root_launcher_execution_source_verified) -and
    ([bool]$remoteBootstrapState.root_launcher_heads_match) -and
    ([string]$remoteBootstrapState.root_launcher_blob_sha -eq $rootLauncherBlob) -and
    ([string]$remoteBootstrapState.root_launcher_execution_blob_sha_before_sync -eq $executingRootLauncherBlob) -and
    ([string]$remoteBootstrapState.root_launcher_remote_blob_sha_after_sync -eq $remoteRootLauncherBlobAfterSync) -and
    ([string]$remoteBootstrapState.root_launcher_remote_guard_blob_sha -eq $remoteGuardBlob) -and
    ([string]$remoteBootstrapState.root_launcher_starter_blob_sha -eq $starterBlob) -and
    ([string]$remoteBootstrapState.root_launcher_bootstrap_publish_mode -eq 'PATH_SCOPED_COMMIT_PUSH_REMOTE_READBACK') -and
    ([bool]$remoteBootstrapState.root_launcher_bootstrap_remote_readback_required) -and
    ([bool]$remoteBootstrapState.root_launcher_no_reset_hard) -and
    ([bool]$remoteBootstrapState.root_launcher_direct_starter_handoff) -and
    ([bool]$remoteBootstrapState.root_launcher_wrapper_reentry_avoided)
  if (-not $remoteAckValid) {
    throw "BLOCKED_BOOTSTRAP_REMOTE_READBACK_CONTRACT_V4_INVALID"
  }
  exit 0
} finally {
  Remove-Item -LiteralPath $tempGuard -Force -ErrorAction SilentlyContinue
}
