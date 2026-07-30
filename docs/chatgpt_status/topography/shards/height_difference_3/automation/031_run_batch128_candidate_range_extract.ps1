param(
  [Parameter(Mandatory=$false)][string]$RepoRoot = $env:AAYS_REPO_ROOT,
  [Parameter(Mandatory=$false)][string]$PythonExe = "python",
  [Parameter(Mandatory=$false)][string]$GitExe = $env:AAYS_GIT_EXE
)
$ErrorActionPreference = "Stop"
if ([string]::IsNullOrWhiteSpace($RepoRoot)) {
  $RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..\..\..\..\..")).Path
}
if ([string]::IsNullOrWhiteSpace($GitExe)) { $GitExe = "git" }

$SourceRel = "england_map_web/data/program_layer_matrix/security.geojson"
$ScriptRel = "docs/chatgpt_status/topography/shards/height_difference_3/automation/030_extract_candidate_range_61540_61779.py"
$BaseRel = "docs/chatgpt_status/topography/shards/height_difference_3/automation/020_stream_extract_security_canonical.py"
$Source = Join-Path $RepoRoot ($SourceRel -replace '/', '\')
$Script = Join-Path $RepoRoot ($ScriptRel -replace '/', '\')
$BaseExtractor = Join-Path $RepoRoot ($BaseRel -replace '/', '\')
$Output = Join-Path $RepoRoot "docs\chatgpt_status\topography\shards\height_difference_3\runner_outputs\024_batch128_candidate_range_extract"
$ExpectedSourceBlob = "8afd1d2bac414cf0f6b9484014e7878a4ceff877"
$ExpectedScriptBlob = "112b200fa76e55b5226774177a4336a5975d01fd"
$ExpectedBaseBlob = "30931b747120d69fcec219a8160ddf1498c423a8"

foreach ($P in @($Source,$Script,$BaseExtractor)) {
  if (-not (Test-Path -LiteralPath $P -PathType Leaf)) { throw "Missing required input: $P" }
}
$GitCommand = Get-Command $GitExe -ErrorAction Stop
$ScriptBlob = (& $GitExe -C $RepoRoot rev-parse "HEAD:$ScriptRel").Trim().ToLowerInvariant()
$BaseBlob = (& $GitExe -C $RepoRoot rev-parse "HEAD:$BaseRel").Trim().ToLowerInvariant()
if ($LASTEXITCODE -ne 0 -or $ScriptBlob -ne $ExpectedScriptBlob) { throw "Range extractor tracked blob mismatch: $ScriptBlob" }
if ($BaseBlob -ne $ExpectedBaseBlob) { throw "Base extractor tracked blob mismatch: $BaseBlob" }
New-Item -ItemType Directory -Force -Path $Output | Out-Null

& $PythonExe $Script `
  --source-geojson $Source `
  --output-dir $Output `
  --base-extractor $BaseExtractor `
  --row-start 61540 `
  --row-end 61779 `
  --preview-count 12 `
  --expected-source-git-blob-sha $ExpectedSourceBlob `
  --expected-base-extractor-git-blob-sha $ExpectedBaseBlob
if ($LASTEXITCODE -ne 0) { throw "Candidate range extractor failed with exit code $LASTEXITCODE" }

$Shard = Join-Path $Output "canonical_shard_61540_61779.jsonl"
$Manifest = Join-Path $Output "range_extraction_resume_manifest.json"
$Preview = Join-Path $Output "candidate_preview_61540_61779.json"
foreach ($P in @($Shard,$Manifest,$Preview)) {
  if (-not (Test-Path -LiteralPath $P -PathType Leaf)) { throw "Missing range output: $P" }
}
$M = Get-Content -Raw -LiteralPath $Manifest | ConvertFrom-Json
$Pj = Get-Content -Raw -LiteralPath $Preview | ConvertFrom-Json
if ([int]$M.schema_version -lt 2 -or -not [bool]$M.transactional_output_bundle) { throw "Range manifest lacks transactional v2 contract" }
if (-not [bool]$M.previous_valid_outputs_preserved_on_failure -or -not [bool]$M.source_stability_verified) { throw "Range preservation/source stability proof missing" }
if ([int]$M.row_start -ne 61540 -or [int]$M.row_end -ne 61779 -or [int]$M.expected_rows -ne 240) { throw "Unexpected range contract" }
if ([int]$M.preview_count -ne 12 -or [int]$M.measurement_values_written -ne 0) { throw "Unexpected preview or numeric count" }
if ([string]$M.actual_source_git_blob_sha -ne $ExpectedSourceBlob) { throw "Canonical source blob mismatch" }
if ([string]$M.actual_base_extractor_git_blob_sha -ne $ExpectedBaseBlob) { throw "Base extractor blob mismatch" }
$ShardSha = (Get-FileHash -Algorithm SHA256 -LiteralPath $Shard).Hash.ToLowerInvariant()
$PreviewSha = (Get-FileHash -Algorithm SHA256 -LiteralPath $Preview).Hash.ToLowerInvariant()
if ($ShardSha -ne ([string]$M.export_sha256).ToLowerInvariant()) { throw "Range JSONL SHA256 mismatch" }
if ($PreviewSha -ne ([string]$M.preview_sha256).ToLowerInvariant()) { throw "Range preview SHA256 mismatch" }
if ([int]$Pj.schema_version -lt 2 -or [int]$Pj.candidate_count -ne 12) { throw "Candidate preview schema/count mismatch" }
if ([string]$Pj.canonical_export_sha256 -ne $ShardSha) { throw "Candidate preview is not bound to range JSONL" }
$PreviewRows = @($Pj.candidates | ForEach-Object { [int]$_.row_no })
if (($PreviewRows -join ',') -ne ((61540..61551) -join ',')) { throw "Candidate preview rows are not exactly 61540..61551" }
foreach ($C in @($Pj.candidates)) {
  if ($null -ne $C.existing_verified_height_value) { throw "Candidate preview unexpectedly contains a height value" }
}

Write-Output (ConvertTo-Json -Compress @{
  ok = $true
  same_task_resume_only = $true
  git_executable = $GitCommand.Source
  range_extractor_blob = $ScriptBlob
  base_extractor_blob = $BaseBlob
  row_start = 61540
  row_end = 61779
  expected_rows = 240
  preview_rows = $PreviewRows
  export_sha256 = $ShardSha
  preview_sha256 = $PreviewSha
  measurement_values_written = 0
  output_dir = $Output
})
