[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'

$repoRoot = if ($env:AAYS_REPO_ROOT) {
  [System.IO.Path]::GetFullPath($env:AAYS_REPO_ROOT)
} else {
  [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..\..\..'))
}

$guardPath = Join-Path $repoRoot 'docs\chatgpt_status\height_difference\automation\height_difference_1_ea_raster_guard_v1.py'
$injectorPath = Join-Path $repoRoot 'docs\chatgpt_status\height_difference\automation\height_difference_1_runtime_guard_injector_v1.py'
$carrierPath = Join-Path $repoRoot 'docs\chatgpt_status\height_difference\automation\height_difference_1_official_boundary_and_wcs_v1.ps1'
foreach ($required in @($guardPath, $injectorPath, $carrierPath)) {
  if (-not (Test-Path -LiteralPath $required -PathType Leaf)) { throw "HEIGHT_DIFFERENCE_1_ENTRY_FILE_MISSING: $required" }
}

$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) { $python = Get-Command py -ErrorAction SilentlyContinue }
if (-not $python) { throw 'PYTHON_EXECUTABLE_NOT_FOUND' }

function Invoke-PythonEntry {
  param([string[]]$Arguments)
  $lines = if ($python.Name -eq 'py.exe' -or $python.Name -eq 'py') {
    & $python.Source -3 @Arguments 2>&1
  } else {
    & $python.Source @Arguments 2>&1
  }
  $code = $LASTEXITCODE
  if ($null -eq $code) { $code = 1 }
  foreach ($line in @($lines)) { [Console]::Out.WriteLine([string]$line) }
  return [pscustomobject]@{ Code = [int]$code; Lines = @($lines) }
}

function Get-LastJsonReceipt {
  param([object[]]$Lines, [string]$MissingLabel)
  $jsonLine = @($Lines | Where-Object { ([string]$_).TrimStart().StartsWith('{') }) | Select-Object -Last 1
  if ($null -eq $jsonLine) { throw $MissingLabel }
  return (([string]$jsonLine) | ConvertFrom-Json)
}

$tempRoot = Join-Path ([System.IO.Path]::GetTempPath()) 'aays_height_difference_1_entry'
New-Item -ItemType Directory -Path $tempRoot -Force | Out-Null
$patchedCarrier = Join-Path $tempRoot 'height_difference_1_official_boundary_and_wcs_runtime_guarded.ps1'
$injectorReceiptPath = Join-Path $tempRoot 'height_difference_1_runtime_guard_injector_receipt.json'

try {
  $guardRun = Invoke-PythonEntry -Arguments @($guardPath, '--self-test')
  if ($guardRun.Code -ne 0) { Write-Output 'FINAL_READY=false'; exit $guardRun.Code }
  $guardReceipt = Get-LastJsonReceipt -Lines $guardRun.Lines -MissingLabel 'EA_RASTER_GUARD_JSON_MISSING'
  if ($guardReceipt.slot_id -ne 'height_difference_1' -or $guardReceipt.state -ne 'PASS') { throw 'EA_RASTER_GUARD_RECEIPT_INVALID' }
  if ([int]$guardReceipt.checks -ne 8) { throw "EA_RASTER_GUARD_CHECK_COUNT_INVALID: $($guardReceipt.checks)" }
  if ([string]$guardReceipt.script_version -ne '1.0-ea-classic-tiff-and-nodata-guard') { throw 'EA_RASTER_GUARD_VERSION_INVALID' }
  if ([double]$guardReceipt.official_nodata_sentinel -ne [double]-3.4028235e38) { throw 'EA_RASTER_GUARD_SENTINEL_INVALID' }

  $injectorSelfTest = Invoke-PythonEntry -Arguments @($injectorPath, '--self-test')
  if ($injectorSelfTest.Code -ne 0) { Write-Output 'FINAL_READY=false'; exit $injectorSelfTest.Code }
  $injectorSelfReceipt = Get-LastJsonReceipt -Lines $injectorSelfTest.Lines -MissingLabel 'RUNTIME_GUARD_INJECTOR_SELF_TEST_JSON_MISSING'
  if ($injectorSelfReceipt.slot_id -ne 'height_difference_1' -or $injectorSelfReceipt.state -ne 'PASS') { throw 'RUNTIME_GUARD_INJECTOR_SELF_TEST_INVALID' }
  if ([string]$injectorSelfReceipt.script_version -ne '1.2-runtime-raster-probe-and-hmlr-id-guard-injector') { throw 'RUNTIME_GUARD_INJECTOR_SELF_TEST_VERSION_INVALID' }
  if ([int]$injectorSelfReceipt.checks -ne 17) { throw "RUNTIME_GUARD_INJECTOR_CHECK_COUNT_INVALID: $($injectorSelfReceipt.checks)" }

  $injectorRun = Invoke-PythonEntry -Arguments @(
    $injectorPath,
    '--carrier', $carrierPath,
    '--output', $patchedCarrier,
    '--receipt', $injectorReceiptPath
  )
  if ($injectorRun.Code -ne 0) { Write-Output 'FINAL_READY=false'; exit $injectorRun.Code }
  foreach ($requiredOutput in @($patchedCarrier, $injectorReceiptPath)) {
    if (-not (Test-Path -LiteralPath $requiredOutput -PathType Leaf)) { throw "RUNTIME_GUARD_INJECTOR_OUTPUT_MISSING: $requiredOutput" }
  }

  $injectorReceipt = Get-Content -LiteralPath $injectorReceiptPath -Raw -Encoding UTF8 | ConvertFrom-Json
  if ($injectorReceipt.slot_id -ne 'height_difference_1' -or $injectorReceipt.state -ne 'COMPLETED_RUNTIME_GUARDS_INJECTED') {
    throw 'RUNTIME_GUARD_INJECTOR_RECEIPT_INVALID'
  }
  if ([string]$injectorReceipt.script_version -ne '1.2-runtime-raster-probe-and-hmlr-id-guard-injector') { throw 'RUNTIME_GUARD_INJECTOR_VERSION_INVALID' }
  if ([int]$injectorReceipt.runtime_patch_count -ne 4) { throw 'RUNTIME_GUARD_PATCH_COUNT_INVALID' }
  $requiredLabels = @('CLASSIC_TIFF_HEADER_VALIDATOR','EA_OFFICIAL_NODATA_RUNTIME_FILTER','PROBE_RASTER_CONTENT_GATE','HMLR_INSPIRE_IDENTIFIER_RECEIPT_GATE')
  foreach ($label in $requiredLabels) {
    if (@($injectorReceipt.runtime_patch_labels) -notcontains $label) { throw "RUNTIME_GUARD_PATCH_LABEL_MISSING: $label" }
  }
  $requiredProbeRequirements = @('EPSG:27700','single_band','approximately_1m_resolution','E_and_N_subset_ranges','requested_bbox_covered','finite_non_nodata_pixels')
  foreach ($requirement in $requiredProbeRequirements) {
    if (@($injectorReceipt.probe_runtime_requirements) -notcontains $requirement) { throw "PROBE_RUNTIME_REQUIREMENT_MISSING: $requirement" }
  }
  if ([double]$injectorReceipt.official_nodata_sentinel -ne [double]-3.4028235e38) { throw 'RUNTIME_GUARD_RECEIPT_SENTINEL_INVALID' }

  $receiptSourcePath = [System.IO.Path]::GetFullPath([string]$injectorReceipt.source_path)
  $receiptOutputPath = [System.IO.Path]::GetFullPath([string]$injectorReceipt.output_path)
  if ($receiptSourcePath -ne [System.IO.Path]::GetFullPath($carrierPath)) { throw 'RUNTIME_GUARD_SOURCE_PATH_MISMATCH' }
  if ($receiptOutputPath -ne [System.IO.Path]::GetFullPath($patchedCarrier)) { throw 'RUNTIME_GUARD_OUTPUT_PATH_MISMATCH' }

  $sourceInfo = Get-Item -LiteralPath $carrierPath
  $outputInfo = Get-Item -LiteralPath $patchedCarrier
  if ([int64]$injectorReceipt.source_bytes -ne [int64]$sourceInfo.Length) { throw 'RUNTIME_GUARD_SOURCE_SIZE_MISMATCH' }
  if ([int64]$injectorReceipt.output_bytes -ne [int64]$outputInfo.Length) { throw 'RUNTIME_GUARD_OUTPUT_SIZE_MISMATCH' }

  $sourceHash = (Get-FileHash -LiteralPath $carrierPath -Algorithm SHA256).Hash.ToLowerInvariant()
  $outputHash = (Get-FileHash -LiteralPath $patchedCarrier -Algorithm SHA256).Hash.ToLowerInvariant()
  if ($sourceHash -ne ([string]$injectorReceipt.source_sha256).ToLowerInvariant()) { throw 'RUNTIME_GUARD_SOURCE_HASH_MISMATCH' }
  if ($outputHash -ne ([string]$injectorReceipt.output_sha256).ToLowerInvariant()) { throw 'RUNTIME_GUARD_OUTPUT_HASH_MISMATCH' }

  Write-Output 'EA_RASTER_GUARD_PREFLIGHT=PASS'
  Write-Output 'EA_RASTER_GUARD_CHECKS=8'
  Write-Output 'RUNTIME_GUARD_INJECTOR_SELF_TEST=PASS'
  Write-Output 'RUNTIME_GUARD_INJECTOR_CHECKS=17'
  Write-Output 'RUNTIME_GUARD_PATCH_COUNT=4'
  Write-Output 'PROBE_RASTER_CONTENT_GATE=ENABLED'
  Write-Output 'HMLR_INSPIRE_IDENTIFIER_RECEIPT_GATE=ENABLED'
  Write-Output 'EA_WCS_OFFICIAL_NODATA_SENTINEL=-3.4028235e38'

  $shell = Get-Command powershell -ErrorAction SilentlyContinue
  if (-not $shell) { $shell = Get-Command pwsh -ErrorAction SilentlyContinue }
  if (-not $shell) { throw 'POWERSHELL_CHILD_EXECUTABLE_NOT_FOUND' }

  $carrierLines = & $shell.Source -NoProfile -ExecutionPolicy Bypass -File $patchedCarrier 2>&1
  $carrierExit = $LASTEXITCODE
  foreach ($line in @($carrierLines)) { [Console]::Out.WriteLine([string]$line) }
  if ($null -eq $carrierExit) { $carrierExit = 1 }
  exit [int]$carrierExit
} finally {
  Remove-Item -LiteralPath $patchedCarrier -Force -ErrorAction SilentlyContinue
  Remove-Item -LiteralPath $injectorReceiptPath -Force -ErrorAction SilentlyContinue
}
