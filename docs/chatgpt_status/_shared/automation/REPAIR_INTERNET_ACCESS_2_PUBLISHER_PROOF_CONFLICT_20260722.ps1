[CmdletBinding()]
param(
  [string]$RepoRoot = $env:AAYS_REPO_ROOT,
  [string]$Branch = 'codex/aays-single-runner-v5-20260706',
  [switch]$NoPush
)

$ErrorActionPreference = 'Stop'
$SlotId = 'internet_access_2'
$TaskMarker = 'internet-access-2-ofcom-2026-schema-and-sample-wave1-20260722T003722Z'
$AllowedConflictPaths = @(
  'docs/chatgpt_status/_shared/slots_21/internet_access_2/heartbeat_latest.json',
  'docs/chatgpt_status/_shared/slots_21/internet_access_2/status_latest.json'
)

function Now-Utc { [DateTimeOffset]::UtcNow.ToString('o') }
function Invoke-Git([string[]]$Args) {
  $output = & git -c "safe.directory=$RepoRoot" -C $RepoRoot @Args 2>&1
  $code = $LASTEXITCODE
  [pscustomobject]@{ code=$code; output=(($output | Out-String).Trim()) }
}
function Normalize-Path([string]$Value) { ($Value -replace '\\','/').Trim() }
function Resolve-RepoRoot {
  if ($RepoRoot) { return [IO.Path]::GetFullPath($RepoRoot).TrimEnd('\') }
  $cursor = Split-Path -Parent $MyInvocation.MyCommand.Path
  while ($cursor) {
    if (Test-Path -LiteralPath (Join-Path $cursor '.git')) { return $cursor }
    $parent = Split-Path -Parent $cursor
    if (-not $parent -or $parent -eq $cursor) { break }
    $cursor = $parent
  }
  throw 'PUBLISHER_REPO_ROOT_NOT_RESOLVED'
}
function Write-Report([hashtable]$Payload) {
  $path = Join-Path $RepoRoot 'docs\chatgpt_status\internet_access_parcel_layer_low_credit_20260612\shards\internet_access_2\recovery\004_publisher_conflict_recovery.json'
  New-Item -ItemType Directory -Force -Path (Split-Path -Parent $path) | Out-Null
  $Payload.final_ready = $false
  $Payload.fake_data = $false
  $Payload.db_write = $false
  $Payload.migration = $false
  $Payload.production_deploy = $false
  [IO.File]::WriteAllText($path, (($Payload | ConvertTo-Json -Depth 20) + "`n"), [Text.UTF8Encoding]::new($false))
  return $path
}

$RepoRoot = Resolve-RepoRoot
if ($RepoRoot.StartsWith('C:\',[StringComparison]::OrdinalIgnoreCase)) { throw "C_DRIVE_NOT_CANONICAL: $RepoRoot" }
if (-not (Test-Path -LiteralPath (Join-Path $RepoRoot '.git'))) { throw "PUBLISHER_REPO_INVALID: $RepoRoot" }

$report = [ordered]@{
  schema_version = 1
  slot_id = $SlotId
  task_marker = $TaskMarker
  checked_at = Now-Utc
  repo_root = $RepoRoot
  branch = $Branch
  state = 'STARTED'
  allowed_conflict_paths = $AllowedConflictPaths
  actions = @()
  blockers = @()
  commit = $null
  push = $null
  remote_readback = $false
}

try {
  $branchResult = Invoke-Git @('branch','--show-current')
  $currentBranch = $branchResult.output.Trim()
  if ($branchResult.code -ne 0 -or $currentBranch -ne $Branch) {
    throw "WRONG_PUBLISHER_BRANCH: current=$currentBranch expected=$Branch"
  }

  $unmergedResult = Invoke-Git @('diff','--name-only','--diff-filter=U','--')
  if ($unmergedResult.code -ne 0) { throw "UNMERGED_SCAN_FAILED: $($unmergedResult.output)" }
  $unmerged = @($unmergedResult.output -split "`r?`n" | Where-Object { $_ } | ForEach-Object { Normalize-Path $_ })
  $outsideConflict = @($unmerged | Where-Object { $_ -notin $AllowedConflictPaths })
  if ($outsideConflict.Count -gt 0) {
    throw ('RECOVERY_REFUSED_UNMERGED_OUTSIDE_SLOT_PROOFS: ' + ($outsideConflict -join ','))
  }

  $statusResult = Invoke-Git @('status','--porcelain')
  if ($statusResult.code -ne 0) { throw "GIT_STATUS_FAILED: $($statusResult.output)" }
  $dirtyPaths = @($statusResult.output -split "`r?`n" | Where-Object { $_ } | ForEach-Object {
    if ($_.Length -gt 3) { Normalize-Path $_.Substring(3).Trim() }
  } | Where-Object { $_ })
  $outsideDirty = @($dirtyPaths | Where-Object {
    $_ -notin $AllowedConflictPaths -and
    $_ -notlike 'docs/chatgpt_status/_shared/heartbeat/*' -and
    $_ -notlike 'docs/chatgpt_status/_shared/status/*' -and
    $_ -notlike 'docs/chatgpt_status/_shared/logs/*' -and
    $_ -notlike 'docs/chatgpt_status/_shared/locks/*'
  })
  if ($outsideDirty.Count -gt 0) {
    throw ('RECOVERY_REFUSED_NON_RUNTIME_DIRTY_PATHS: ' + ($outsideDirty -join ','))
  }

  $gitDirResult = Invoke-Git @('rev-parse','--git-dir')
  if ($gitDirResult.code -ne 0) { throw "GIT_DIR_NOT_RESOLVED: $($gitDirResult.output)" }
  $gitDir = $gitDirResult.output.Trim()
  if (-not [IO.Path]::IsPathRooted($gitDir)) { $gitDir = Join-Path $RepoRoot $gitDir }

  if (Test-Path -LiteralPath (Join-Path $gitDir 'rebase-merge') -or Test-Path -LiteralPath (Join-Path $gitDir 'rebase-apply')) {
    $abort = Invoke-Git @('rebase','--abort')
    if ($abort.code -ne 0) { throw "REBASE_ABORT_FAILED: $($abort.output)" }
    $report.actions += 'rebase_aborted'
  }
  if (Test-Path -LiteralPath (Join-Path $gitDir 'MERGE_HEAD')) {
    $abort = Invoke-Git @('merge','--abort')
    if ($abort.code -ne 0) { throw "MERGE_ABORT_FAILED: $($abort.output)" }
    $report.actions += 'merge_aborted'
  }

  $fetch = Invoke-Git @('fetch','--no-tags','origin',("+refs/heads/$Branch`:refs/remotes/origin/$Branch"))
  if ($fetch.code -ne 0) { throw "FETCH_FAILED: $($fetch.output)" }
  $report.actions += 'remote_fetched'

  $subject = (Invoke-Git @('log','-1','--pretty=%s')).output
  $aheadText = (Invoke-Git @('rev-list','--count',"origin/$Branch..HEAD")).output
  $ahead = 0
  [void][int]::TryParse($aheadText.Trim(), [ref]$ahead)
  if ($ahead -gt 0) {
    if ($subject -notlike "*Publish $SlotId task*" -and $subject -notlike "*$TaskMarker*") {
      throw "RECOVERY_REFUSED_LATEST_LOCAL_COMMIT_NOT_SLOT_PUBLISH: $subject"
    }
    foreach ($path in $AllowedConflictPaths) {
      $restore = Invoke-Git @('restore',"--source=origin/$Branch",'--staged','--worktree','--',$path)
      if ($restore.code -ne 0) { throw "PROOF_RESTORE_FAILED path=$path error=$($restore.output)" }
    }
    $staged = Invoke-Git @('diff','--cached','--name-only','--')
    if ($staged.code -ne 0) { throw "STAGED_SCAN_FAILED: $($staged.output)" }
    if ($staged.output.Trim()) {
      $amend = Invoke-Git @('commit','--amend','--no-edit')
      if ($amend.code -ne 0) { throw "PUBLISH_COMMIT_AMEND_FAILED: $($amend.output)" }
      $report.actions += 'slot_proof_changes_removed_from_local_publish_commit'
    }
  }

  $rebase = Invoke-Git @('rebase',"origin/$Branch")
  if ($rebase.code -ne 0) {
    [void](Invoke-Git @('rebase','--abort'))
    throw "NARROW_REBASE_FAILED: $($rebase.output)"
  }
  $report.actions += 'local_publish_commit_rebased'

  $conflictCheck = Invoke-Git @('diff','--name-only','--diff-filter=U','--')
  if ($conflictCheck.output.Trim()) { throw "UNMERGED_PATHS_REMAIN: $($conflictCheck.output)" }

  $localHead = (Invoke-Git @('rev-parse','HEAD')).output.Trim()
  $report.commit = $localHead
  if ($NoPush) {
    $report.push = 'SKIPPED_NO_PUSH'
    $report.state = 'REPAIRED_LOCAL_ONLY'
  } else {
    $push = Invoke-Git @('push','origin',"HEAD:$Branch")
    if ($push.code -ne 0) { throw "PUSH_FAILED: $($push.output)" }
    $report.push = 'PASS'
    $remote = Invoke-Git @('ls-remote','origin',"refs/heads/$Branch")
    $remoteHead = if ($remote.code -eq 0 -and $remote.output) { ($remote.output -split '\s+')[0] } else { '' }
    if ($remoteHead -ne $localHead) { throw "REMOTE_READBACK_MISMATCH local=$localHead remote=$remoteHead" }
    $report.remote_readback = $true
    $report.state = 'REPAIRED_PUSHED_REMOTE_READBACK_PASS'
  }
} catch {
  $report.state = 'BLOCKED'
  $report.blockers += $_.Exception.Message
}

$report.completed_at = Now-Utc
$reportPath = Write-Report $report
Write-Output ($report | ConvertTo-Json -Depth 20)
Write-Output "REPORT_PATH=$reportPath"
if ($report.state -eq 'BLOCKED') { exit 2 }
exit 0
