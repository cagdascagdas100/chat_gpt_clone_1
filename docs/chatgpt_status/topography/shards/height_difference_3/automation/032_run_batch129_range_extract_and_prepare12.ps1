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
$QueryOut = Join-Path $RepoRoot "docs\chatgpt_status\topography\shards\height_difference_3\runner_outputs\025_batch129_prepare12_queries"

if (-not (Test-Path -LiteralPath $RangeAdapter -PathType Leaf)) { throw "Missing range adapter: $RangeAdapter" }
if (-not (Test-Path -LiteralPath $QueryPreparer -PathType Leaf)) { throw "Missing query preparer: $QueryPreparer" }

& $PowerShellExe -NoProfile -ExecutionPolicy Bypass -File $RangeAdapter -RepoRoot $RepoRoot -PythonExe $PythonExe
if ($LASTEXITCODE -ne 0) { throw "Range extraction adapter failed with exit code $LASTEXITCODE" }
if (-not (Test-Path -LiteralPath $RangeJsonl -PathType Leaf)) { throw "Missing extracted range JSONL" }
New-Item -ItemType Directory -Force -Path $QueryOut | Out-Null

& $PythonExe $QueryPreparer `
  --input $RangeJsonl `
  --output-dir $QueryOut `
  --sample-size 12 `
  --allow-explicit-missing `
  --timeout 60
if ($LASTEXITCODE -ne 0) { throw "12-candidate query preparer failed with exit code $LASTEXITCODE" }

$Starter = Join-Path $QueryOut "starter_three_query_manifest.json"
$Summary = Join-Path $QueryOut "operation_summary.json"
if (-not (Test-Path -LiteralPath $Starter -PathType Leaf)) { throw "Missing starter query manifest" }
if (-not (Test-Path -LiteralPath $Summary -PathType Leaf)) { throw "Missing query operation summary" }
$M = Get-Content -Raw -LiteralPath $Starter | ConvertFrom-Json
$S = Get-Content -Raw -LiteralPath $Summary | ConvertFrom-Json
if ($M.starter_candidate_count -ne 12) { throw "Expected 12 prepared candidates" }
if (-not $M.network_queries_enabled) { throw "EA network query preparation unexpectedly disabled" }
$Expected = 61540..61551
$Actual = @($M.candidates | ForEach-Object { [int]$_.row_no })
if (($Actual -join ',') -ne ($Expected -join ',')) { throw "Prepared candidate rows are not exactly 61540..61551" }
foreach ($C in $M.candidates) {
  if ([string]::IsNullOrWhiteSpace([string]$C.hmlr_inspire_id)) { throw "Prepared candidate lacks HMLR INSPIRE ID" }
  if ([string]::IsNullOrWhiteSpace([string]$C.ea_tile_inventory_query_url)) { throw "Prepared candidate lacks EA tile query URL" }
  if ($C.measured_value_promoted) { throw "Numeric promotion unexpectedly enabled" }
}
if ($S.numeric_samples_written -ne 0) { throw "Numeric samples unexpectedly written" }

Write-Output (ConvertTo-Json -Compress @{
  ok = $true
  same_task_resume_only = $true
  python_executable = $PythonExe
  powershell_executable = $PowerShellExe
  executable_identity_propagated = $true
  range_rows = 240
  prepared_candidate_rows = $Actual
  prepared_candidate_count = 12
  network_queries_enabled = $true
  numeric_samples_written = 0
  numeric_height_difference_publish_allowed = $false
  query_output_dir = $QueryOut
})
