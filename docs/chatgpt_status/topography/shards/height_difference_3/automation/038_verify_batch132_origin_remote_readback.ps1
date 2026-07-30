param(
  [Parameter(Mandatory=$false)][string]$RepoRoot = $env:AAYS_REPO_ROOT,
  [Parameter(Mandatory=$false)][string]$GitExe = $env:AAYS_GIT_EXE
)
$ErrorActionPreference = "Stop"
if ([string]::IsNullOrWhiteSpace($RepoRoot)) {
  $RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..\..\..\..\..")).Path
}
if ([string]::IsNullOrWhiteSpace($GitExe)) { $GitExe = "git" }
$GitCommand = Get-Command $GitExe -ErrorAction Stop
$GitVersion = (& $GitExe --version).Trim()
if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($GitVersion)) { throw "Cannot execute pinned Git command" }

$Branch = "codex/aays-single-runner-v5-20260706"
$ExpectedTask = "height_difference_3-canonical-api-measurement-20260721-01"
$ExpectedContinuation = "6e8e709b6bad7b9807055e2b8b5de98cd4945ee3dee57825e72ba1b824eadd0f"
$ExpectedContract = "EA_DTM_POLYGON_P95_P05_OS_T50_SAME_POINT_V2"
$Manifest = Join-Path $RepoRoot "docs\chatgpt_status\topography\shards\height_difference_3\runner_outputs\031_batch132_remote_readback\batch132_publish_manifest.json"
$OutDir = Join-Path $RepoRoot "docs\chatgpt_status\topography\shards\height_difference_3\runner_outputs\031_batch132_remote_readback"
$ResultPath = Join-Path $OutDir "batch132_origin_remote_readback.json"
if (-not (Test-Path -LiteralPath $Manifest -PathType Leaf)) { throw "Missing publish manifest: $Manifest" }
$ManifestHashBefore = (Get-FileHash -Algorithm SHA256 -LiteralPath $Manifest).Hash.ToLowerInvariant()
$M = Get-Content -Raw -LiteralPath $Manifest | ConvertFrom-Json
if ([int]$M.schema_version -lt 3) { throw "Publish manifest schema is older than v3" }
if (-not [bool]$M.ready_for_serial_publisher -or -not [bool]$M.inputs_hash_stable) { throw "Publish manifest is not stable and ready" }
if (-not [bool]$M.local_acceptance_execution_bound -or -not [bool]$M.atomic_manifest_materialization) { throw "Publish manifest lacks acceptance binding or atomicity" }
if ([string]$M.canonical_branch -ne $Branch) { throw "Publish manifest branch mismatch" }
if ([string]$M.task_id -ne $ExpectedTask -or [string]$M.continuation_key -ne $ExpectedContinuation) { throw "Publish manifest task/continuation mismatch" }
if ([string]$M.measurement_contract_version -ne $ExpectedContract -or -not [bool]$M.same_point_crosscheck_required) { throw "Publish manifest same-point contract mismatch" }
$PreHead = ([string]$M.pre_publish_origin_head).Trim().ToLowerInvariant()
if ($PreHead -notmatch '^[0-9a-f]{40}$') { throw "Invalid pre-publish origin HEAD in manifest" }
if (@($M.files).Count -ne 7) { throw "Expected exactly seven manifest file records" }

function Get-BlobAtCommit([string]$Commit, [string]$Rel) {
  $Spec = "${Commit}:$Rel"
  $Value = (& $GitExe -C $RepoRoot rev-parse $Spec 2>$null)
  if ($LASTEXITCODE -ne 0 -or $null -eq $Value) { return $null }
  return ([string]$Value).Trim().ToLowerInvariant()
}
function Test-SafeRelativePath([string]$Rel) {
  if ([string]::IsNullOrWhiteSpace($Rel) -or [IO.Path]::IsPathRooted($Rel)) { return $false }
  $Parts = $Rel -split '[/\\]'
  return -not ($Parts -contains '..')
}

$SeenNames = @{}
$SeenPaths = @{}
foreach ($F in @($M.files)) {
  $Name = [string]$F.name
  $Rel = [string]$F.relative_path
  if ([string]::IsNullOrWhiteSpace($Name) -or $SeenNames.ContainsKey($Name)) { throw "Duplicate/empty manifest file name: $Name" }
  if (-not (Test-SafeRelativePath $Rel) -or $SeenPaths.ContainsKey($Rel)) { throw "Unsafe or duplicate manifest path: $Rel" }
  if ([string]$F.sha256 -notmatch '^[0-9a-fA-F]{64}$' -or [string]$F.git_blob_sha1 -notmatch '^[0-9a-fA-F]{40}$') { throw "Invalid manifest hash record: $Rel" }
  $SeenNames[$Name] = $true
  $SeenPaths[$Rel] = $true
}

$FetchSpec = "refs/heads/${Branch}:refs/remotes/origin/${Branch}"
& $GitExe -C $RepoRoot fetch --no-tags origin $FetchSpec | Out-Null
if ($LASTEXITCODE -ne 0) { throw "git fetch explicit remote-tracking ref failed with exit code $LASTEXITCODE" }
$RemoteRef = "refs/remotes/origin/$Branch"
$RemoteHead = (& $GitExe -C $RepoRoot rev-parse $RemoteRef).Trim().ToLowerInvariant()
if ($LASTEXITCODE -ne 0 -or $RemoteHead -notmatch '^[0-9a-f]{40}$') { throw "Cannot resolve freshly fetched remote branch head" }
& $GitExe -C $RepoRoot merge-base --is-ancestor $PreHead $RemoteHead | Out-Null
if ($LASTEXITCODE -ne 0) { throw "Pre-publish origin HEAD is not an ancestor of fresh remote HEAD" }

$Checks = @()
$PreHeadChecks = @()
$PreHeadAllBlobsMatch = $true
$ManifestPaths = @()
$InitialLocalHashes = @{}
foreach ($F in @($M.files)) {
  $Rel = [string]$F.relative_path
  $ManifestPaths += $Rel
  $Local = Join-Path $RepoRoot ($Rel -replace '/', '\')
  if (-not (Test-Path -LiteralPath $Local -PathType Leaf)) { throw "Missing local accepted file: $Rel" }
  $LocalSha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $Local).Hash.ToLowerInvariant()
  $InitialLocalHashes[$Rel] = $LocalSha256
  if ($LocalSha256 -ne ([string]$F.sha256).ToLowerInvariant()) { throw "Local SHA256 mismatch: $Rel" }
  $LocalBlob = (& $GitExe -C $RepoRoot hash-object --no-filters -- $Local).Trim().ToLowerInvariant()
  if ($LASTEXITCODE -ne 0) { throw "git hash-object failed: $Rel" }
  $ExpectedBlob = ([string]$F.git_blob_sha1).ToLowerInvariant()
  if ($LocalBlob -ne $ExpectedBlob) { throw "Local Git blob mismatch: $Rel" }
  $RemoteBlob = Get-BlobAtCommit $RemoteHead $Rel
  if ([string]::IsNullOrWhiteSpace($RemoteBlob) -or $RemoteBlob -ne $ExpectedBlob) { throw "Remote file missing or Git blob mismatch: $Rel" }
  $PreBlob = Get-BlobAtCommit $PreHead $Rel
  $PreMatches = (-not [string]::IsNullOrWhiteSpace($PreBlob)) -and ($PreBlob -eq $ExpectedBlob)
  if (-not $PreMatches) { $PreHeadAllBlobsMatch = $false }
  $PreHeadChecks += [ordered]@{ relative_path = $Rel; expected_git_blob_sha1 = $ExpectedBlob; pre_publish_blob_sha1 = $PreBlob; matched_at_pre_publish_head = $PreMatches }
  $Checks += [ordered]@{ relative_path = $Rel; local_sha256 = $LocalSha256; expected_git_blob_sha1 = $ExpectedBlob; local_git_blob_sha1 = $LocalBlob; remote_git_blob_sha1 = $RemoteBlob; passed = $true }
}

$HistoryMode = $null
$MaterializationCommit = $null
$HistoryCommitCount = 0
if ($PreHeadAllBlobsMatch) {
  $HistoryMode = "ALREADY_PRESENT_AT_PREPUBLISH_HEAD_NO_REPLAY_REQUIRED"
  $MaterializationCommit = $PreHead
} else {
  $HistoryCommits = @(& $GitExe -C $RepoRoot rev-list --reverse "$PreHead..$RemoteHead")
  if ($LASTEXITCODE -ne 0) { throw "Cannot enumerate remote history after pre-publish HEAD" }
  $HistoryCommitCount = @($HistoryCommits).Count
  if ($HistoryCommitCount -lt 1) { throw "Remote HEAD did not advance and accepted blobs were not already present" }
  foreach ($Commit in $HistoryCommits) {
    $Candidate = ([string]$Commit).Trim().ToLowerInvariant()
    if ($Candidate -notmatch '^[0-9a-f]{40}$') { continue }
    $AllAtCandidate = $true
    foreach ($F in @($M.files)) {
      $CandidateBlob = Get-BlobAtCommit $Candidate ([string]$F.relative_path)
      if ([string]::IsNullOrWhiteSpace($CandidateBlob) -or $CandidateBlob -ne ([string]$F.git_blob_sha1).ToLowerInvariant()) { $AllAtCandidate = $false; break }
    }
    if ($AllAtCandidate) { $MaterializationCommit = $Candidate; break }
  }
  if ([string]::IsNullOrWhiteSpace($MaterializationCommit)) { throw "No descendant commit materializes all seven accepted blobs" }
  $HistoryMode = "FIRST_FULL_BLOB_MATERIALIZATION_COMMIT_FOUND"
}
& $GitExe -C $RepoRoot merge-base --is-ancestor $MaterializationCommit $RemoteHead | Out-Null
if ($LASTEXITCODE -ne 0) { throw "Materialization commit is not an ancestor of fresh remote HEAD" }

$MaterializationChangedPaths = @()
$MissingManifestPathsFromCommitDelta = @()
$MaterializationCommitChangesAllManifestPaths = $true
$CommitDeltaGateMode = "ALREADY_PRESENT_NO_REPLAY_DELTA_NOT_REQUIRED"
$PublisherCommitCandidate = $null
if ($HistoryMode -eq "FIRST_FULL_BLOB_MATERIALIZATION_COMMIT_FOUND") {
  $MaterializationChangedPaths = @(& $GitExe -C $RepoRoot diff-tree --no-commit-id --name-only -r $MaterializationCommit)
  if ($LASTEXITCODE -ne 0) { throw "Cannot read materialization commit path delta" }
  $ChangedLookup = @{}
  foreach ($P in @($MaterializationChangedPaths)) {
    $Token = ([string]$P).Trim()
    if (-not [string]::IsNullOrWhiteSpace($Token)) { $ChangedLookup[$Token] = $true }
  }
  foreach ($Rel in @($ManifestPaths)) {
    if (-not $ChangedLookup.ContainsKey([string]$Rel)) { $MissingManifestPathsFromCommitDelta += [string]$Rel }
  }
  if (@($MissingManifestPathsFromCommitDelta).Count -gt 0) {
    $MaterializationCommitChangesAllManifestPaths = $false
    throw "First full materialization commit did not change every manifest path: $($MissingManifestPathsFromCommitDelta -join ',')"
  }
  $CommitDeltaGateMode = "ALL_SEVEN_MANIFEST_PATHS_CHANGED_IN_MATERIALIZATION_COMMIT"
  $PublisherCommitCandidate = $MaterializationCommit
}

$ExpectedRows = @(61540..61551)
$ManifestRows = @($M.expected_rows | ForEach-Object { [int]$_ })
if (($ManifestRows -join ',') -ne ($ExpectedRows -join ',') -or [int]$M.expected_verified_count -ne 12) { throw "Manifest row/count mismatch" }
foreach ($F in @($M.files)) {
  $Rel = [string]$F.relative_path
  $Local = Join-Path $RepoRoot ($Rel -replace '/', '\')
  $Current = (Get-FileHash -Algorithm SHA256 -LiteralPath $Local).Hash.ToLowerInvariant()
  if ($Current -ne $InitialLocalHashes[$Rel]) { throw "Accepted local file changed during remote readback: $Rel" }
}
$ManifestHashAfter = (Get-FileHash -Algorithm SHA256 -LiteralPath $Manifest).Hash.ToLowerInvariant()
if ($ManifestHashBefore -ne $ManifestHashAfter) { throw "Publish manifest changed during remote readback" }

$Result = [ordered]@{
  schema_version = 4
  slot_id = "height_difference_3"
  task_id = [string]$M.task_id
  continuation_key = [string]$M.continuation_key
  canonical_branch = $Branch
  git_executable = $GitCommand.Source
  git_version = $GitVersion
  explicit_fetch_refspec = $FetchSpec
  publish_manifest_sha256 = $ManifestHashAfter
  publish_manifest_hash_stable = $true
  local_input_hashes_stable = $true
  measurement_contract_version = $ExpectedContract
  same_point_crosscheck_required = $true
  pre_publish_origin_head = $PreHead
  remote_head = $RemoteHead
  pre_publish_head_is_ancestor_of_remote_head = $true
  pre_publish_head_all_blobs_match = $PreHeadAllBlobsMatch
  history_mode = $HistoryMode
  history_commit_count_after_pre_publish_head = $HistoryCommitCount
  first_full_blob_materialization_commit = $MaterializationCommit
  materialization_commit_is_ancestor_of_remote_head = $true
  materialization_commit_changed_paths = @($MaterializationChangedPaths)
  materialization_commit_changed_path_count = @($MaterializationChangedPaths).Count
  materialization_commit_changes_all_manifest_paths = $MaterializationCommitChangesAllManifestPaths
  missing_manifest_paths_from_materialization_commit_delta = @($MissingManifestPathsFromCommitDelta)
  materialization_commit_delta_gate_mode = $CommitDeltaGateMode
  publisher_commit_candidate = $PublisherCommitCandidate
  remote_history_binding_passed = $true
  remote_history_and_commit_delta_binding_passed = $true
  pre_publish_file_checks = $PreHeadChecks
  expected_rows = $ExpectedRows
  file_count = @($Checks).Count
  files = $Checks
  all_remote_blobs_match = $true
  origin_fetch_performed = $true
  remote_tracking_ref_freshly_updated = $true
  atomic_result_materialization = $true
  child_direct_push_performed = $false
  numeric_values_changed = 0
  numeric_publish_acceptance_for_12_rows = $true
  final_ready = $false
  fake_data = $false
}
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
$Temp = Join-Path $OutDir (".batch132_readback_" + [Guid]::NewGuid().ToString("N") + ".tmp")
try {
  $Json = $Result | ConvertTo-Json -Depth 14
  [IO.File]::WriteAllText($Temp, $Json + [Environment]::NewLine, (New-Object Text.UTF8Encoding($false)))
  if ((Get-Item -LiteralPath $Temp).Length -le 0) { throw "Staged remote readback result is empty" }
  Move-Item -Force -LiteralPath $Temp -Destination $ResultPath
} finally {
  Remove-Item -Force -ErrorAction SilentlyContinue -LiteralPath $Temp
}
Write-Output ($Result | ConvertTo-Json -Compress -Depth 14)
