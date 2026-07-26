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
$AcceptanceOut = Join-Path $RepoRoot "docs\chatgpt_status\topography\shards\height_difference_3\runner_outputs\029_batch131_strict12_acceptance"
$Acceptance = Join-Path $AcceptanceOut "batch131_strict12_local_acceptance.json"

foreach ($P in @($StrictAdapter,$Validator)) {
  if (-not (Test-Path -LiteralPath $P -PathType Leaf)) { throw "Missing required script: $P" }
}
New-Item -ItemType Directory -Force -Path $AcceptanceOut | Out-Null

& $PowerShellExe -NoProfile -ExecutionPolicy Bypass -File $StrictAdapter -RepoRoot $RepoRoot -PythonExe $PythonExe -PowerShellExe $PowerShellExe
if ($LASTEXITCODE -ne 0) { throw "Strict12 measurement chain failed with exit code $LASTEXITCODE" }

& $PythonExe $Validator --strict-output-dir $StrictOut --output $Acceptance
if ($LASTEXITCODE -ne 0) { throw "Strict12 local acceptance validation failed with exit code $LASTEXITCODE" }
if (-not (Test-Path -LiteralPath $Acceptance -PathType Leaf)) { throw "Missing strict12 local acceptance output" }
$A = Get-Content -Raw -LiteralPath $Acceptance | ConvertFrom-Json
if (-not [bool]$A.local_acceptance_passed) { throw "Local strict12 acceptance is false" }
if ([int]$A.checks_passed -ne [int]$A.checks_total) { throw "Local strict12 acceptance checks are incomplete" }
if ([int]$A.numeric_values_changed_by_validator -ne 0) { throw "Validator unexpectedly changed numeric values" }
if (-not [bool]$A.remote_github_readback_required) { throw "Remote GitHub readback gate unexpectedly disabled" }

$Result = @{
  schema_version = 2
  slot_id = "height_difference_3"
  same_task_resume_only = $true
  strict12_runtime_chain_completed = $true
  python_executable = $PythonExe
  powershell_executable = $PowerShellExe
  executable_identity_propagated = $true
  candidate_aware_proj_gate_required = $true
  local_acceptance_passed = $true
  local_acceptance_checks = [int]$A.checks_total
  file_sha256 = $A.file_sha256
  numeric_values_changed_by_validator = 0
  remote_github_readback_required = $true
  numeric_publish_final_acceptance = "PENDING_REMOTE_GITHUB_READBACK"
  final_ready = $false
  fake_data = $false
}
$Result | ConvertTo-Json -Depth 8 | Set-Content -Encoding UTF8 -LiteralPath (Join-Path $AcceptanceOut "batch131_strict12_acceptance_execution.json")
Write-Output ($Result | ConvertTo-Json -Compress -Depth 8)
