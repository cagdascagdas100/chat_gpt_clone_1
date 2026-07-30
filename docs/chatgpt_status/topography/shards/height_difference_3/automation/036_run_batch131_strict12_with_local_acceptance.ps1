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

$StrictAdapter = Join-Path $RepoRoot "docs\chatgpt_status\topography\shards\height_difference_3\automation\033_run_batch130_prepare12_strict_measurement_chain.ps1"
$Validator = Join-Path $RepoRoot "docs\chatgpt_status\topography\shards\height_difference_3\automation\035_validate_batch130_strict12_outputs.py"
$StrictOut = Join-Path $RepoRoot "docs\chatgpt_status\topography\shards\height_difference_3\runner_outputs\027_batch130_prepare12_strict_chain"
$StrictContract = Join-Path $StrictOut "batch130_strict12_acceptance.json"
$AcceptanceOut = Join-Path $RepoRoot "docs\chatgpt_status\topography\shards\height_difference_3\runner_outputs\029_batch131_strict12_acceptance"
$Acceptance = Join-Path $AcceptanceOut "batch131_strict12_local_acceptance.json"
$Execution = Join-Path $AcceptanceOut "batch131_strict12_acceptance_execution.json"
$ExpectedContract = "EA_DTM_POLYGON_P95_P05_OS_T50_SAME_POINT_V2"

foreach ($P in @($StrictAdapter,$Validator)) {
  if (-not (Test-Path -LiteralPath $P -PathType Leaf)) { throw "Missing required script: $P" }
}
New-Item -ItemType Directory -Force -Path $AcceptanceOut | Out-Null
& $PowerShellExe -NoProfile -ExecutionPolicy Bypass -File $StrictAdapter -RepoRoot $RepoRoot -PythonExe $PythonExe -PowerShellExe $PowerShellExe
if ($LASTEXITCODE -ne 0) { throw "Strict12 measurement chain failed with exit code $LASTEXITCODE" }
if (-not (Test-Path -LiteralPath $StrictContract -PathType Leaf)) { throw "Missing strict12 contract output" }
$S = Get-Content -Raw -LiteralPath $StrictContract | ConvertFrom-Json
foreach ($Field in @("exact_hmlr_official_id_gate","exact_hmlr_gate_runs_before_elevation_sampling","candidate_hmlr_inspire_id_value_required","hmlr_exact_authority_source_gate","ea_official_host_and_axis_metadata_gate","ea_row_bound_single_raster_gate","terrain50_official_catalog_archive_hash_gate","nearest_fill_forbidden")) {
  if (-not [bool]$S.$Field) { throw "Strict12 contract gate missing: $Field" }
}

& $PythonExe $Validator --strict-output-dir $StrictOut --output $Acceptance
if ($LASTEXITCODE -ne 0) { throw "Strict12 local acceptance validation failed with exit code $LASTEXITCODE" }
if (-not (Test-Path -LiteralPath $Acceptance -PathType Leaf)) { throw "Missing strict12 local acceptance output" }
$AcceptanceHashBefore = (Get-FileHash -Algorithm SHA256 -LiteralPath $Acceptance).Hash.ToLowerInvariant()
$A = Get-Content -Raw -LiteralPath $Acceptance | ConvertFrom-Json
$AcceptanceHashAfter = (Get-FileHash -Algorithm SHA256 -LiteralPath $Acceptance).Hash.ToLowerInvariant()
if ($AcceptanceHashBefore -ne $AcceptanceHashAfter) { throw "Local acceptance changed while being read" }
if ([int]$A.schema_version -lt 3) { throw "Local acceptance schema is older than v3" }
if (-not [bool]$A.local_acceptance_passed -or [int]$A.checks_passed -ne [int]$A.checks_total) { throw "Local strict12 acceptance is incomplete" }
if (-not [bool]$A.inputs_hash_stable -or -not [bool]$A.atomic_acceptance_materialization) { throw "Local acceptance hash stability/atomicity proof missing" }
if ([string]$A.measurement_contract_version -ne $ExpectedContract -or -not [bool]$A.same_point_crosscheck_required) { throw "Local acceptance same-point contract mismatch" }
if (-not [bool]$A.exact_hmlr_official_id_required -or -not [bool]$A.nearest_fill_forbidden) { throw "Local acceptance identity/fill gate missing" }
if ([int]$A.numeric_values_changed_by_validator -ne 0) { throw "Validator unexpectedly changed numeric values" }
if (-not [bool]$A.remote_github_readback_required) { throw "Remote GitHub readback gate unexpectedly disabled" }
$StrictHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $StrictContract).Hash.ToLowerInvariant()
if ([string]$A.file_sha256.strict_acceptance -ne $StrictHash) { throw "Strict contract is not hash-bound by local acceptance" }

$Result = [ordered]@{
  schema_version = 6
  slot_id = "height_difference_3"
  same_task_resume_only = $true
  strict12_runtime_chain_completed = $true
  python_executable = $PythonExe
  powershell_executable = $PowerShellExe
  executable_identity_propagated = $true
  candidate_aware_proj_gate_required = $true
  exact_hmlr_official_id_required = $true
  exact_hmlr_gate_runs_before_elevation_sampling = $true
  candidate_hmlr_inspire_id_value_required = $true
  hmlr_exact_authority_source_gate_required = $true
  ea_official_host_and_axis_metadata_gate_required = $true
  ea_row_bound_single_raster_gate_required = $true
  terrain50_official_catalog_archive_hash_gate_required = $true
  nearest_fill_forbidden = $true
  same_point_crosscheck_required = $true
  measurement_contract_version = $ExpectedContract
  local_acceptance_passed = $true
  local_acceptance_checks = [int]$A.checks_total
  local_acceptance_sha256 = $AcceptanceHashAfter
  local_acceptance_inputs_hash_stable = $true
  local_acceptance_atomic_materialization = $true
  file_sha256 = $A.file_sha256
  strict_contract_sha256 = $StrictHash
  numeric_values_changed_by_validator = 0
  remote_github_readback_required = $true
  atomic_execution_materialization = $true
  numeric_publish_final_acceptance = "PENDING_REMOTE_GITHUB_READBACK"
  final_ready = $false
  fake_data = $false
}
$Temp = Join-Path $AcceptanceOut (".batch131_execution_" + [Guid]::NewGuid().ToString("N") + ".tmp")
try {
  $Json = $Result | ConvertTo-Json -Depth 10
  [IO.File]::WriteAllText($Temp, $Json + [Environment]::NewLine, (New-Object Text.UTF8Encoding($false)))
  if ((Get-Item -LiteralPath $Temp).Length -le 0) { throw "Staged acceptance execution is empty" }
  Move-Item -Force -LiteralPath $Temp -Destination $Execution
} finally {
  Remove-Item -Force -ErrorAction SilentlyContinue -LiteralPath $Temp
}
$ExecutionHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $Execution).Hash.ToLowerInvariant()
Write-Output (ConvertTo-Json -Compress @{
  ok = $true
  local_acceptance_sha256 = $AcceptanceHashAfter
  strict_contract_sha256 = $StrictHash
  acceptance_execution_sha256 = $ExecutionHash
  same_point_crosscheck_required = $true
  remote_github_readback_required = $true
})
