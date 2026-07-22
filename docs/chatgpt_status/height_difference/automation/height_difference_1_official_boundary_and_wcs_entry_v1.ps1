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
$identityInjectorPath = Join-Path $repoRoot 'docs\chatgpt_status\height_difference\automation\height_difference_1_measurement_identity_injector_v1.py'
$boundaryInjectorPath = Join-Path $repoRoot 'docs\chatgpt_status\height_difference\automation\height_difference_1_boundary_binding_injector_v1.py'
$stageInjectorPath = Join-Path $repoRoot 'docs\chatgpt_status\height_difference\automation\height_difference_1_python_stage_watchdog_injector_v1.py'
$carrierPath = Join-Path $repoRoot 'docs\chatgpt_status\height_difference\automation\height_difference_1_official_boundary_and_wcs_v1.ps1'
foreach ($required in @($guardPath,$injectorPath,$identityInjectorPath,$boundaryInjectorPath,$stageInjectorPath,$carrierPath)) {
  if (-not (Test-Path -LiteralPath $required -PathType Leaf)) { throw "HEIGHT_DIFFERENCE_1_ENTRY_FILE_MISSING: $required" }
}

$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) { $python = Get-Command py -ErrorAction SilentlyContinue }
if (-not $python) { throw 'PYTHON_EXECUTABLE_NOT_FOUND' }

function Invoke-PythonEntry {
  param([string[]]$Arguments)
  $lines = if ($python.Name -in @('py.exe','py')) {
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
  param([object[]]$Lines,[string]$MissingLabel)
  $jsonLine = @($Lines | Where-Object { ([string]$_).TrimStart().StartsWith('{') }) | Select-Object -Last 1
  if ($null -eq $jsonLine) { throw $MissingLabel }
  return (([string]$jsonLine | ConvertFrom-Json))
}

function Assert-PathSizeHashReceipt {
  param([object]$Receipt,[string]$ExpectedSource,[string]$ExpectedOutput,[string]$Label)
  $sourceFull = [System.IO.Path]::GetFullPath($ExpectedSource)
  $outputFull = [System.IO.Path]::GetFullPath($ExpectedOutput)
  if ([System.IO.Path]::GetFullPath([string]$Receipt.source_path) -ne $sourceFull) { throw "${Label}_SOURCE_PATH_MISMATCH" }
  if ([System.IO.Path]::GetFullPath([string]$Receipt.output_path) -ne $outputFull) { throw "${Label}_OUTPUT_PATH_MISMATCH" }
  $sourceInfo = Get-Item -LiteralPath $sourceFull
  $outputInfo = Get-Item -LiteralPath $outputFull
  if ([int64]$Receipt.source_bytes -ne [int64]$sourceInfo.Length) { throw "${Label}_SOURCE_SIZE_MISMATCH" }
  if ([int64]$Receipt.output_bytes -ne [int64]$outputInfo.Length) { throw "${Label}_OUTPUT_SIZE_MISMATCH" }
  $sourceHash = (Get-FileHash -LiteralPath $sourceFull -Algorithm SHA256).Hash.ToLowerInvariant()
  $outputHash = (Get-FileHash -LiteralPath $outputFull -Algorithm SHA256).Hash.ToLowerInvariant()
  if ($sourceHash -ne ([string]$Receipt.source_sha256).ToLowerInvariant()) { throw "${Label}_SOURCE_HASH_MISMATCH" }
  if ($outputHash -ne ([string]$Receipt.output_sha256).ToLowerInvariant()) { throw "${Label}_OUTPUT_HASH_MISMATCH" }
}

function Assert-Labels {
  param([object]$Receipt,[string[]]$Labels,[string]$Prefix)
  foreach ($label in $Labels) {
    if (@($Receipt.runtime_patch_labels) -notcontains $label) { throw "${Prefix}_PATCH_LABEL_MISSING: $label" }
  }
}

$tempRoot = Join-Path ([System.IO.Path]::GetTempPath()) 'aays_height_difference_1_entry'
New-Item -ItemType Directory -Path $tempRoot -Force | Out-Null
$guardedCarrier = Join-Path $tempRoot 'height_difference_1_runtime_guarded.ps1'
$guardReceiptPath = Join-Path $tempRoot 'height_difference_1_runtime_guard_receipt.json'
$identityCarrier = Join-Path $tempRoot 'height_difference_1_identity_native_bng.ps1'
$identityReceiptPath = Join-Path $tempRoot 'height_difference_1_identity_native_bng_receipt.json'
$strictCarrier = Join-Path $tempRoot 'height_difference_1_strict_interior.ps1'
$boundaryReceiptPath = Join-Path $tempRoot 'height_difference_1_boundary_receipt.json'
$stageCarrier = Join-Path $tempRoot 'height_difference_1_python_stage_watchdog.ps1'
$stageReceiptPath = Join-Path $tempRoot 'height_difference_1_python_stage_watchdog_receipt.json'

try {
  $guardRun = Invoke-PythonEntry -Arguments @($guardPath,'--self-test')
  if ($guardRun.Code -ne 0) { throw "EA_RASTER_GUARD_SELF_TEST_EXIT_$($guardRun.Code)" }
  $guard = Get-LastJsonReceipt -Lines $guardRun.Lines -MissingLabel 'EA_RASTER_GUARD_JSON_MISSING'
  if ($guard.slot_id -ne 'height_difference_1' -or $guard.state -ne 'PASS' -or [int]$guard.checks -ne 8) { throw 'EA_RASTER_GUARD_RECEIPT_INVALID' }
  if ([string]$guard.script_version -ne '1.0-ea-classic-tiff-and-nodata-guard') { throw 'EA_RASTER_GUARD_VERSION_INVALID' }
  if ([double]$guard.official_nodata_sentinel -ne [double]-3.4028235e38) { throw 'EA_RASTER_GUARD_SENTINEL_INVALID' }

  $firstTestRun = Invoke-PythonEntry -Arguments @($injectorPath,'--self-test')
  if ($firstTestRun.Code -ne 0) { throw "RUNTIME_GUARD_SELF_TEST_EXIT_$($firstTestRun.Code)" }
  $firstTest = Get-LastJsonReceipt -Lines $firstTestRun.Lines -MissingLabel 'RUNTIME_GUARD_SELF_TEST_JSON_MISSING'
  if ($firstTest.slot_id -ne 'height_difference_1' -or $firstTest.state -ne 'PASS' -or [int]$firstTest.checks -ne 17) { throw 'RUNTIME_GUARD_SELF_TEST_INVALID' }
  if ([string]$firstTest.script_version -ne '1.2-runtime-raster-probe-and-hmlr-id-guard-injector') { throw 'RUNTIME_GUARD_SELF_TEST_VERSION_INVALID' }

  $firstRun = Invoke-PythonEntry -Arguments @($injectorPath,'--carrier',$carrierPath,'--output',$guardedCarrier,'--receipt',$guardReceiptPath)
  if ($firstRun.Code -ne 0) { throw "RUNTIME_GUARD_INJECTOR_EXIT_$($firstRun.Code)" }
  $first = Get-Content -LiteralPath $guardReceiptPath -Raw -Encoding UTF8 | ConvertFrom-Json
  if ($first.state -ne 'COMPLETED_RUNTIME_GUARDS_INJECTED' -or [int]$first.runtime_patch_count -ne 4) { throw 'RUNTIME_GUARD_RECEIPT_INVALID' }
  if ([string]$first.script_version -ne '1.2-runtime-raster-probe-and-hmlr-id-guard-injector') { throw 'RUNTIME_GUARD_VERSION_INVALID' }
  Assert-Labels -Receipt $first -Prefix 'RUNTIME_GUARD' -Labels @('CLASSIC_TIFF_HEADER_VALIDATOR','EA_OFFICIAL_NODATA_RUNTIME_FILTER','PROBE_RASTER_CONTENT_GATE','HMLR_INSPIRE_IDENTIFIER_RECEIPT_GATE')
  foreach ($requirement in @('EPSG:27700','single_band','approximately_1m_resolution','E_and_N_subset_ranges','requested_bbox_covered','finite_non_nodata_pixels')) {
    if (@($first.probe_runtime_requirements) -notcontains $requirement) { throw "PROBE_RUNTIME_REQUIREMENT_MISSING: $requirement" }
  }
  if ([double]$first.official_nodata_sentinel -ne [double]-3.4028235e38) { throw 'RUNTIME_GUARD_SENTINEL_INVALID' }
  Assert-PathSizeHashReceipt -Receipt $first -ExpectedSource $carrierPath -ExpectedOutput $guardedCarrier -Label 'RUNTIME_GUARD'

  $identityTestRun = Invoke-PythonEntry -Arguments @($identityInjectorPath,'--self-test')
  if ($identityTestRun.Code -ne 0) { throw "MEASUREMENT_IDENTITY_SELF_TEST_EXIT_$($identityTestRun.Code)" }
  $identityTest = Get-LastJsonReceipt -Lines $identityTestRun.Lines -MissingLabel 'MEASUREMENT_IDENTITY_SELF_TEST_JSON_MISSING'
  if ($identityTest.slot_id -ne 'height_difference_1' -or $identityTest.state -ne 'PASS' -or [int]$identityTest.checks -ne 15) { throw 'MEASUREMENT_IDENTITY_SELF_TEST_INVALID' }
  if ([string]$identityTest.script_version -ne '1.1-measurement-inspire-identity-and-native-bng-binding-injector') { throw 'MEASUREMENT_IDENTITY_SELF_TEST_VERSION_INVALID' }

  $identityRun = Invoke-PythonEntry -Arguments @($identityInjectorPath,'--carrier',$guardedCarrier,'--output',$identityCarrier,'--receipt',$identityReceiptPath)
  if ($identityRun.Code -ne 0) { throw "MEASUREMENT_IDENTITY_INJECTOR_EXIT_$($identityRun.Code)" }
  $identity = Get-Content -LiteralPath $identityReceiptPath -Raw -Encoding UTF8 | ConvertFrom-Json
  if ($identity.state -ne 'COMPLETED_MEASUREMENT_IDENTITY_BINDING_INJECTED' -or [int]$identity.runtime_patch_count -ne 5) { throw 'MEASUREMENT_IDENTITY_RECEIPT_INVALID' }
  if ([string]$identity.script_version -ne '1.1-measurement-inspire-identity-and-native-bng-binding-injector') { throw 'MEASUREMENT_IDENTITY_VERSION_INVALID' }
  Assert-Labels -Receipt $identity -Prefix 'MEASUREMENT_IDENTITY' -Labels @('HMLR_IDENTIFIER_ENV_HANDOFF','MEASUREMENT_NATIVE_BNG_CRS_GATE','MEASUREMENT_INSPIRE_COLUMN_BINDING_GATE','CANDIDATE_INSPIRE_IDENTITY_PROVENANCE','BUSINESS_ROW_INSPIRE_IDENTITY_PROVENANCE_GATE')
  if ([string]$identity.identifier_column_env -ne 'HMLR_VERIFIED_IDENTIFIER_COLUMN') { throw 'MEASUREMENT_IDENTITY_COLUMN_ENV_INVALID' }
  if ([string]$identity.identifier_set_hash_env -ne 'HMLR_VERIFIED_IDENTIFIER_SET_SHA256') { throw 'MEASUREMENT_IDENTITY_HASH_ENV_INVALID' }
  if ([string]$identity.native_crs_required -ne 'EPSG:27700') { throw 'MEASUREMENT_NATIVE_CRS_RECEIPT_INVALID' }
  foreach ($nullLike in @('','nan','none','null','<na>','nat')) {
    if (@($identity.null_like_polygon_identifiers_rejected) -notcontains $nullLike) { throw "MEASUREMENT_NULL_LIKE_IDENTIFIER_RULE_MISSING: $nullLike" }
  }
  Assert-PathSizeHashReceipt -Receipt $identity -ExpectedSource $guardedCarrier -ExpectedOutput $identityCarrier -Label 'MEASUREMENT_IDENTITY'
  if (([string]$identity.source_sha256).ToLowerInvariant() -ne ([string]$first.output_sha256).ToLowerInvariant()) { throw 'TWO_STAGE_INJECTOR_HASH_CHAIN_MISMATCH' }

  $boundaryTestRun = Invoke-PythonEntry -Arguments @($boundaryInjectorPath,'--self-test')
  if ($boundaryTestRun.Code -ne 0) { throw "BOUNDARY_BINDING_SELF_TEST_EXIT_$($boundaryTestRun.Code)" }
  $boundaryTest = Get-LastJsonReceipt -Lines $boundaryTestRun.Lines -MissingLabel 'BOUNDARY_BINDING_SELF_TEST_JSON_MISSING'
  if ($boundaryTest.slot_id -ne 'height_difference_1' -or $boundaryTest.state -ne 'PASS' -or [int]$boundaryTest.checks -ne 10) { throw 'BOUNDARY_BINDING_SELF_TEST_INVALID' }
  if ([string]$boundaryTest.script_version -ne '1.0-strict-interior-boundary-touch-rejection-injector') { throw 'BOUNDARY_BINDING_SELF_TEST_VERSION_INVALID' }

  $boundaryRun = Invoke-PythonEntry -Arguments @($boundaryInjectorPath,'--carrier',$identityCarrier,'--output',$strictCarrier,'--receipt',$boundaryReceiptPath)
  if ($boundaryRun.Code -ne 0) { throw "BOUNDARY_BINDING_INJECTOR_EXIT_$($boundaryRun.Code)" }
  $boundary = Get-Content -LiteralPath $boundaryReceiptPath -Raw -Encoding UTF8 | ConvertFrom-Json
  if ($boundary.state -ne 'COMPLETED_STRICT_INTERIOR_BOUNDARY_GUARD_INJECTED' -or [int]$boundary.runtime_patch_count -ne 2) { throw 'BOUNDARY_BINDING_RECEIPT_INVALID' }
  if ([string]$boundary.script_version -ne '1.0-strict-interior-boundary-touch-rejection-injector') { throw 'BOUNDARY_BINDING_VERSION_INVALID' }
  Assert-Labels -Receipt $boundary -Prefix 'BOUNDARY_BINDING' -Labels @('STRICT_INTERIOR_POLYGON_MATCHER','BOUNDARY_TOUCH_REJECTION_GATE')
  if ([string]$boundary.binding_semantics -ne 'strict_polygon_interior_only') { throw 'BOUNDARY_BINDING_SEMANTICS_INVALID' }
  if ([string]$boundary.boundary_touch_policy -ne 'reject_canonical_binding') { throw 'BOUNDARY_TOUCH_POLICY_INVALID' }
  Assert-PathSizeHashReceipt -Receipt $boundary -ExpectedSource $identityCarrier -ExpectedOutput $strictCarrier -Label 'BOUNDARY_BINDING'
  if (([string]$boundary.source_sha256).ToLowerInvariant() -ne ([string]$identity.output_sha256).ToLowerInvariant()) { throw 'THREE_STAGE_INJECTOR_HASH_CHAIN_MISMATCH' }

  $stageTestRun = Invoke-PythonEntry -Arguments @($stageInjectorPath,'--self-test')
  if ($stageTestRun.Code -ne 0) { throw "PYTHON_STAGE_WATCHDOG_SELF_TEST_EXIT_$($stageTestRun.Code)" }
  $stageTest = Get-LastJsonReceipt -Lines $stageTestRun.Lines -MissingLabel 'PYTHON_STAGE_WATCHDOG_SELF_TEST_JSON_MISSING'
  if ($stageTest.slot_id -ne 'height_difference_1' -or $stageTest.state -ne 'PASS' -or [int]$stageTest.checks -ne 12) { throw 'PYTHON_STAGE_WATCHDOG_SELF_TEST_INVALID' }
  if ([string]$stageTest.script_version -ne '1.0-carrier-python-stage-watchdog-injector') { throw 'PYTHON_STAGE_WATCHDOG_SELF_TEST_VERSION_INVALID' }

  $stageRun = Invoke-PythonEntry -Arguments @($stageInjectorPath,'--carrier',$strictCarrier,'--output',$stageCarrier,'--receipt',$stageReceiptPath)
  if ($stageRun.Code -ne 0) { throw "PYTHON_STAGE_WATCHDOG_INJECTOR_EXIT_$($stageRun.Code)" }
  $stage = Get-Content -LiteralPath $stageReceiptPath -Raw -Encoding UTF8 | ConvertFrom-Json
  if ($stage.state -ne 'COMPLETED_PYTHON_STAGE_WATCHDOG_INJECTED' -or [int]$stage.runtime_patch_count -ne 1) { throw 'PYTHON_STAGE_WATCHDOG_RECEIPT_INVALID' }
  if ([string]$stage.script_version -ne '1.0-carrier-python-stage-watchdog-injector') { throw 'PYTHON_STAGE_WATCHDOG_VERSION_INVALID' }
  Assert-Labels -Receipt $stage -Prefix 'PYTHON_STAGE_WATCHDOG' -Labels @('PYTHON_STAGE_REALTIME_WATCHDOG')
  if ([int]$stage.stage_max_seconds -ne 1650 -or [int]$stage.stage_heartbeat_seconds -ne 30 -or [int]$stage.stage_poll_seconds -ne 5) { throw 'PYTHON_STAGE_WATCHDOG_LIMITS_INVALID' }
  if ($stage.realtime_stdout_stderr -ne $true -or $stage.independent_output_offsets -ne $true -or $stage.process_tree_cleanup -ne $true) { throw 'PYTHON_STAGE_WATCHDOG_SEMANTICS_INVALID' }
  Assert-PathSizeHashReceipt -Receipt $stage -ExpectedSource $strictCarrier -ExpectedOutput $stageCarrier -Label 'PYTHON_STAGE_WATCHDOG'
  if (([string]$stage.source_sha256).ToLowerInvariant() -ne ([string]$boundary.output_sha256).ToLowerInvariant()) { throw 'FOUR_STAGE_INJECTOR_HASH_CHAIN_MISMATCH' }

  Write-Output 'EA_RASTER_GUARD_PREFLIGHT=PASS'
  Write-Output 'RUNTIME_GUARD_INJECTOR_CHECKS=17'
  Write-Output 'RUNTIME_GUARD_PATCH_COUNT=4'
  Write-Output 'MEASUREMENT_IDENTITY_INJECTOR_CHECKS=15'
  Write-Output 'MEASUREMENT_IDENTITY_PATCH_COUNT=5'
  Write-Output 'BOUNDARY_BINDING_INJECTOR_CHECKS=10'
  Write-Output 'BOUNDARY_BINDING_PATCH_COUNT=2'
  Write-Output 'PYTHON_STAGE_WATCHDOG_INJECTOR_CHECKS=12'
  Write-Output 'PYTHON_STAGE_WATCHDOG_PATCH_COUNT=1'
  Write-Output 'FOUR_STAGE_INJECTOR_HASH_CHAIN=VERIFIED'
  Write-Output 'PYTHON_STAGE_REALTIME_OUTPUT=ENABLED'
  Write-Output 'PYTHON_STAGE_MAX_SECONDS=1650'
  Write-Output 'STRICT_POLYGON_INTERIOR_ONLY=ENABLED'
  Write-Output 'FINAL_READY=false'

  $shell = Get-Command powershell -ErrorAction SilentlyContinue
  if (-not $shell) { $shell = Get-Command pwsh -ErrorAction SilentlyContinue }
  if (-not $shell) { throw 'POWERSHELL_CHILD_EXECUTABLE_NOT_FOUND' }
  & $shell.Source -NoProfile -ExecutionPolicy Bypass -File $stageCarrier
  $carrierExit = $LASTEXITCODE
  if ($null -eq $carrierExit) { $carrierExit = 1 }
  exit [int]$carrierExit
} catch {
  [Console]::Error.WriteLine([string]$_)
  Write-Output 'FINAL_READY=false'
  exit 2
} finally {
  foreach ($temp in @(
    $guardedCarrier,$guardReceiptPath,
    $identityCarrier,$identityReceiptPath,
    $strictCarrier,$boundaryReceiptPath,
    $stageCarrier,$stageReceiptPath
  )) {
    Remove-Item -LiteralPath $temp -Force -ErrorAction SilentlyContinue
  }
}
