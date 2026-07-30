param(
  [Parameter(Mandatory=$false)][string]$RepoRoot = $env:AAYS_REPO_ROOT,
  [Parameter(Mandatory=$false)][string]$PythonExe = "python",
  [Parameter(Mandatory=$false)][string]$PowerShellExe = $env:AAYS_POWERSHELL_EXE
)
$ErrorActionPreference = "Stop"
if ([string]::IsNullOrWhiteSpace($RepoRoot)) {
  $RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..\..\..\..\..")).Path
}
if ([string]::IsNullOrWhiteSpace($PowerShellExe)) { $PowerShellExe = "powershell" }

$RangeAdapter = Join-Path $RepoRoot "docs\chatgpt_status\topography\shards\height_difference_3\automation\031_run_batch128_candidate_range_extract.ps1"
$QueryPreparer = Join-Path $RepoRoot "docs\chatgpt_status\topography\shards\height_difference_3\automation\004_prepare_three_real_sample_queries.py"
$RangeOut = Join-Path $RepoRoot "docs\chatgpt_status\topography\shards\height_difference_3\runner_outputs\024_batch128_candidate_range_extract"
$RangeJsonl = Join-Path $RangeOut "canonical_shard_61540_61779.jsonl"
$RangeManifest = Join-Path $RangeOut "range_extraction_resume_manifest.json"
$RangePreview = Join-Path $RangeOut "candidate_preview_61540_61779.json"
$QueryOut = Join-Path $RepoRoot "docs\chatgpt_status\topography\shards\height_difference_3\runner_outputs\025_batch129_prepare12_queries"

foreach ($P in @($RangeAdapter,$QueryPreparer)) {
  if (-not (Test-Path -LiteralPath $P -PathType Leaf)) { throw "Missing required script: $P" }
}
& $PowerShellExe -NoProfile -ExecutionPolicy Bypass -File $RangeAdapter -RepoRoot $RepoRoot -PythonExe $PythonExe -PowerShellExe $PowerShellExe
if ($LASTEXITCODE -ne 0) { throw "Range extraction adapter failed with exit code $LASTEXITCODE" }
foreach ($P in @($RangeJsonl,$RangeManifest,$RangePreview)) {
  if (-not (Test-Path -LiteralPath $P -PathType Leaf)) { throw "Missing range evidence: $P" }
}
$R = Get-Content -Raw -LiteralPath $RangeManifest | ConvertFrom-Json
if ([int]$R.schema_version -lt 2 -or -not [bool]$R.transactional_output_bundle) { throw "Range manifest is not transactional v2+" }
if ([int]$R.row_start -ne 61540 -or [int]$R.row_end -ne 61779 -or [int]$R.expected_rows -ne 240) { throw "Range manifest identity mismatch" }
$RangeSha = (Get-FileHash -Algorithm SHA256 -LiteralPath $RangeJsonl).Hash.ToLowerInvariant()
$PreviewSha = (Get-FileHash -Algorithm SHA256 -LiteralPath $RangePreview).Hash.ToLowerInvariant()
if ($RangeSha -ne ([string]$R.export_sha256).ToLowerInvariant()) { throw "Range JSONL hash mismatch" }
if ($PreviewSha -ne ([string]$R.preview_sha256).ToLowerInvariant()) { throw "Range preview hash mismatch" }

New-Item -ItemType Directory -Force -Path $QueryOut | Out-Null
& $PythonExe $QueryPreparer `
  --input $RangeJsonl `
  --output-dir $QueryOut `
  --sample-size 12 `
  --allow-explicit-missing `
  --expected-row-start 61540 `
  --expected-row-end 61779 `
  --timeout 60
if ($LASTEXITCODE -ne 0) { throw "12-candidate query preparer failed with exit code $LASTEXITCODE" }

$Starter = Join-Path $QueryOut "starter_three_query_manifest.json"
$Summary = Join-Path $QueryOut "operation_summary.json"
foreach ($P in @($Starter,$Summary)) {
  if (-not (Test-Path -LiteralPath $P -PathType Leaf)) { throw "Missing query output: $P" }
}
$M = Get-Content -Raw -LiteralPath $Starter | ConvertFrom-Json
$S = Get-Content -Raw -LiteralPath $Summary | ConvertFrom-Json
if ([int]$M.schema_version -lt 3 -or [int]$S.schema_version -lt 3) { throw "Query outputs require schema v3+" }
if ([string]$M.status -ne "QUERY_PREPARED_OFFICIAL_DISCOVERY_VERIFIED") { throw "Query preparation did not verify official discovery" }
if (-not [bool]$M.transactional_output_bundle -or -not [bool]$M.previous_valid_outputs_preserved_on_failure) { throw "Query bundle transaction proof missing" }
if (-not [bool]$M.canonical_registry_contiguous -or -not [bool]$M.official_ea_host_only) { throw "Query registry/host gate missing" }
if ([string]$M.canonical_export_sha256 -ne $RangeSha -or [string]$S.canonical_export_sha256 -ne $RangeSha) { throw "Query outputs are not bound to range JSONL" }
if ([int]$M.input_range.start -ne 61540 -or [int]$M.input_range.end -ne 61779 -or [int]$M.input_range.count -ne 240) { throw "Query input range mismatch" }
if ([int]$S.input_range.start -ne 61540 -or [int]$S.input_range.end -ne 61779 -or [int]$S.input_range.count -ne 240) { throw "Query summary input range mismatch" }
if ([int]$M.canonical_rows_validated -ne 240 -or [int]$S.validated_rows -ne 240) { throw "Query validated row count mismatch" }
if ([int]$M.starter_candidate_count -ne 12 -or [int]$S.selected_candidates -ne 12) { throw "Expected exactly 12 prepared candidates" }
if (-not [bool]$M.network_queries_enabled) { throw "EA network query preparation unexpectedly disabled" }
if (@($M.ea_wcs_coverage_ids).Count -lt 1) { throw "EA WCS coverage identifiers are missing" }
if ([string]::IsNullOrWhiteSpace([string]$M.ea_wcs_provenance.sha256) -or ([string]$M.ea_wcs_provenance.sha256).Length -ne 64) { throw "EA WCS provenance SHA256 is missing" }
$Expected = 61540..61551
$Actual = @($M.candidates | ForEach-Object { [int]$_.row_no })
if (($Actual -join ',') -ne ($Expected -join ',')) { throw "Prepared candidate rows are not exactly 61540..61551" }
if (($S.selected_row_numbers -join ',') -ne ($Expected -join ',')) { throw "Query summary rows mismatch" }
foreach ($C in @($M.candidates)) {
  if ([string]::IsNullOrWhiteSpace([string]$C.hmlr_inspire_id)) { throw "Prepared candidate lacks HMLR INSPIRE ID" }
  if (@($C.candidate_official_ids).Count -lt 1) { throw "Prepared candidate lacks normalized official IDs" }
  if ([int]$C.ea_tile_match_count -lt 1) { throw "Prepared candidate has no EA tile match" }
  if ([string]::IsNullOrWhiteSpace([string]$C.ea_tile_query_provenance.sha256) -or ([string]$C.ea_tile_query_provenance.sha256).Length -ne 64) { throw "Prepared candidate lacks EA query provenance SHA256" }
  $Resolved = [Uri]([string]$C.ea_tile_query_provenance.resolved_url)
  if ($Resolved.Scheme -ne "https" -or $Resolved.Host -ne "environment.data.gov.uk") { throw "EA query provenance resolved off official host" }
  if ([bool]$C.measured_value_promoted) { throw "Numeric promotion unexpectedly enabled" }
}
if ([int]$S.numeric_samples_written -ne 0 -or -not [bool]$S.transactional_output_bundle) { throw "Query summary numeric/transaction gate mismatch" }

Write-Output (ConvertTo-Json -Compress @{
  ok = $true
  same_task_resume_only = $true
  python_executable = $PythonExe
  powershell_executable = $PowerShellExe
  executable_identity_propagated = $true
  range_rows = 240
  range_sha256 = $RangeSha
  prepared_candidate_rows = $Actual
  prepared_candidate_count = 12
  official_ea_discovery_verified = $true
  network_queries_enabled = $true
  numeric_samples_written = 0
  numeric_height_difference_publish_allowed = $false
  query_output_dir = $QueryOut
})
