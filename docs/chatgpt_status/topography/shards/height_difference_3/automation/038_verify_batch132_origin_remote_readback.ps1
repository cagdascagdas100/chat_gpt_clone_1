param(
  [Parameter(Mandatory=$false)][string]$RepoRoot = $env:AAYS_REPO_ROOT,
  [Parameter(Mandatory=$false)][string]$GitExe = "git"
)
$ErrorActionPreference = "Stop"
if ([string]::IsNullOrWhiteSpace($RepoRoot)) {
  $RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..\..\..\..\..")).Path
}
$Branch = "codex/aays-single-runner-v5-20260706"
$Manifest = Join-Path $RepoRoot "docs\chatgpt_status\topography\shards\height_difference_3\runner_outputs\031_batch132_remote_readback\batch132_publish_manifest.json"
$OutDir = Join-Path $RepoRoot "docs\chatgpt_status\topography\shards\height_difference_3\runner_outputs\031_batch132_remote_readback"
$ResultPath = Join-Path $OutDir "batch132_origin_remote_readback.json"
if (-not (Test-Path -LiteralPath $Manifest -PathType Leaf)) { throw "Missing publish manifest: $Manifest" }
$M = Get-Content -Raw -LiteralPath $Manifest | ConvertFrom-Json
if (-not [bool]$M.ready_for_serial_publisher) { throw "Publish manifest is not ready" }
if ($M.canonical_branch -ne $Branch) { throw "Publish manifest branch mismatch" }
if ($M.task_id -ne "height_difference_3-canonical-api-measurement-20260721-01") { throw "Publish manifest task mismatch" }

$FetchSpec = "refs/heads/${Branch}:refs/remotes/origin/${Branch}"
& $GitExe -C $RepoRoot fetch --no-tags origin $FetchSpec | Out-Null
if ($LASTEXITCODE -ne 0) { throw "git fetch explicit remote-tracking ref failed with exit code $LASTEXITCODE" }
$RemoteRef = "refs/remotes/origin/$Branch"
$RemoteHead = (& $GitExe -C $RepoRoot rev-parse $RemoteRef).Trim()
if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($RemoteHead)) { throw "Cannot resolve freshly fetched remote branch head" }

$Checks = @()
foreach ($F in @($M.files)) {
  $Rel = [string]$F.relative_path
  $Local = Join-Path $RepoRoot ($Rel -replace '/', '\')
  if (-not (Test-Path -LiteralPath $Local -PathType Leaf)) { throw "Missing local accepted file: $Rel" }
  $LocalSha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $Local).Hash.ToLowerInvariant()
  if ($LocalSha256 -ne ([string]$F.sha256).ToLowerInvariant()) { throw "Local SHA256 mismatch: $Rel" }
  $LocalBlob = (& $GitExe -C $RepoRoot hash-object --no-filters -- $Local).Trim().ToLowerInvariant()
  if ($LASTEXITCODE -ne 0) { throw "git hash-object failed: $Rel" }
  $ExpectedBlob = ([string]$F.git_blob_sha1).ToLowerInvariant()
  if ($LocalBlob -ne $ExpectedBlob) { throw "Local Git blob mismatch: $Rel" }
  $Spec = "${RemoteHead}:$Rel"
  $RemoteBlob = (& $GitExe -C $RepoRoot rev-parse $Spec).Trim().ToLowerInvariant()
  if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($RemoteBlob)) { throw "Remote file missing: $Rel" }
  if ($RemoteBlob -ne $ExpectedBlob) { throw "Remote Git blob mismatch: $Rel" }
  $Checks += [ordered]@{
    relative_path = $Rel
    local_sha256 = $LocalSha256
    expected_git_blob_sha1 = $ExpectedBlob
    local_git_blob_sha1 = $LocalBlob
    remote_git_blob_sha1 = $RemoteBlob
    passed = $true
  }
}

$ExpectedRows = @(61540..61551)
$ManifestRows = @($M.expected_rows | ForEach-Object { [int]$_ })
if (($ManifestRows -join ',') -ne ($ExpectedRows -join ',')) { throw "Manifest row set mismatch" }
if ([int]$M.expected_verified_count -ne 12) { throw "Manifest verified count mismatch" }

$Result = [ordered]@{
  schema_version = 1
  slot_id = "height_difference_3"
  task_id = [string]$M.task_id
  continuation_key = [string]$M.continuation_key
  canonical_branch = $Branch
  explicit_fetch_refspec = $FetchSpec
  remote_head = $RemoteHead
  expected_rows = $ExpectedRows
  file_count = @($Checks).Count
  files = $Checks
  all_remote_blobs_match = $true
  origin_fetch_performed = $true
  remote_tracking_ref_freshly_updated = $true
  child_direct_push_performed = $false
  numeric_values_changed = 0
  numeric_publish_acceptance_for_12_rows = $true
  final_ready = $false
  fake_data = $false
}
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
$Result | ConvertTo-Json -Depth 10 | Set-Content -Encoding UTF8 -LiteralPath $ResultPath
Write-Output ($Result | ConvertTo-Json -Compress -Depth 10)
