param(
  [Parameter(Mandatory=$false)][string]$RepoRoot = $env:AAYS_REPO_ROOT,
  [Parameter(Mandatory=$false)][string]$PythonExe = "python"
)

$ErrorActionPreference = "Stop"
if ([string]::IsNullOrWhiteSpace($RepoRoot)) {
  $RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..\..\..\..\..")).Path
}

$Source = Join-Path $RepoRoot "england_map_web\data\program_layer_matrix\security.geojson"
$Script = Join-Path $RepoRoot "docs\chatgpt_status\topography\shards\height_difference_3\automation\030_extract_candidate_range_61540_61779.py"
$Output = Join-Path $RepoRoot "docs\chatgpt_status\topography\shards\height_difference_3\runner_outputs\024_batch128_candidate_range_extract"

if (-not (Test-Path -LiteralPath $Source -PathType Leaf)) { throw "Missing canonical source: $Source" }
if (-not (Test-Path -LiteralPath $Script -PathType Leaf)) { throw "Missing range extractor: $Script" }
New-Item -ItemType Directory -Force -Path $Output | Out-Null

& $PythonExe $Script `
  --source-geojson $Source `
  --output-dir $Output `
  --row-start 61540 `
  --row-end 61779 `
  --preview-count 12 `
  --expected-git-blob-sha "8afd1d2bac414cf0f6b9484014e7878a4ceff877"

if ($LASTEXITCODE -ne 0) { throw "Candidate range extractor failed with exit code $LASTEXITCODE" }

$Manifest = Join-Path $Output "range_extraction_resume_manifest.json"
$Preview = Join-Path $Output "candidate_preview_61540_61779.json"
if (-not (Test-Path -LiteralPath $Manifest -PathType Leaf)) { throw "Missing range extraction manifest" }
if (-not (Test-Path -LiteralPath $Preview -PathType Leaf)) { throw "Missing candidate preview" }

$M = Get-Content -Raw -LiteralPath $Manifest | ConvertFrom-Json
if ($M.expected_rows -ne 240) { throw "Unexpected extracted row count" }
if ($M.measurement_values_written -ne 0) { throw "Numeric measurement unexpectedly written" }
if ($M.actual_source_git_blob_sha -ne "8afd1d2bac414cf0f6b9484014e7878a4ceff877") { throw "Canonical source blob mismatch" }

Write-Output (ConvertTo-Json -Compress @{
  ok = $true
  same_task_resume_only = $true
  row_start = 61540
  row_end = 61779
  expected_rows = 240
  preview_count = 12
  measurement_values_written = 0
  output_dir = $Output
})
