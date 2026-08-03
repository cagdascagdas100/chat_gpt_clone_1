@echo off
setlocal
set "AAYS_CANONICAL_ROOT=%~dp0"
set "AAYS_CMD_FILE=%~f0"
set "AAYS_BOOTSTRAP_FILE=%TEMP%\aays_canonical_bootstrap_%RANDOM%_%RANDOM%.ps1"
powershell -NoProfile -ExecutionPolicy Bypass -Command "$s=[IO.File]::ReadAllText($env:AAYS_CMD_FILE);$m='# AAYS_POWERSHELL_BOOTSTRAP';$i=$s.IndexOf($m);if($i -lt 0){exit 97};$b=$s.Substring($i+$m.Length).TrimStart([char]13,[char]10);[IO.File]::WriteAllText($env:AAYS_BOOTSTRAP_FILE,$b,[Text.UTF8Encoding]::new($false));& $env:AAYS_BOOTSTRAP_FILE;exit $LASTEXITCODE"
set "AAYS_EXIT_CODE=%ERRORLEVEL%"
del /q "%AAYS_BOOTSTRAP_FILE%" >nul 2>&1
endlocal & exit /b %AAYS_EXIT_CODE%
# AAYS_POWERSHELL_BOOTSTRAP
$ErrorActionPreference = 'Stop'
$root = [System.IO.Path]::GetFullPath([string]$env:AAYS_CANONICAL_ROOT).TrimEnd('\')
$branch = 'codex/aays-single-runner-v5-20260706'
$staleMinutes = 15

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

$shallow = (Invoke-AaysGit @('rev-parse','--is-shallow-repository')).Trim().ToLowerInvariant()
$refspec = "+refs/heads/$branch`:refs/remotes/origin/$branch"
$fetchArgs = @('fetch','--no-tags')
if ($shallow -eq 'true') { $fetchArgs += '--unshallow' }
$fetchArgs += @('origin',$refspec)
[void](Invoke-AaysGit $fetchArgs)

$remoteRef = "refs/remotes/origin/$branch"
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
  if ($localHead -ne $remoteHead) {
    if ($syncSafeStates -contains $guardState) {
      [void](Invoke-AaysGit @('merge','--ff-only',$remoteRef))
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
  $wrapper = Join-Path $root 'docs\chatgpt_status\_shared\automation\START_AAYS_CANONICAL_RUNNER_AND_PANEL_20260706.ps1'
  if (-not (Test-Path -LiteralPath $wrapper -PathType Leaf)) {
    throw "BLOCKED_CANONICAL_WRAPPER_MISSING_AFTER_BOOTSTRAP=$wrapper"
  }
  & powershell -NoProfile -ExecutionPolicy Bypass -File $wrapper -RepoRoot $root
  exit $LASTEXITCODE
} finally {
  Remove-Item -LiteralPath $tempGuard -Force -ErrorAction SilentlyContinue
}
