[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'

$repoRoot = if ($env:AAYS_REPO_ROOT) {
  [System.IO.Path]::GetFullPath($env:AAYS_REPO_ROOT)
} else {
  [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..\..\..'))
}

$guardPath = Join-Path $repoRoot 'docs\chatgpt_status\height_difference\automation\height_difference_1_ea_raster_guard_v1.py'
$carrierPath = Join-Path $repoRoot 'docs\chatgpt_status\height_difference\automation\height_difference_1_official_boundary_and_wcs_v1.ps1'
foreach ($required in @($guardPath, $carrierPath)) {
  if (-not (Test-Path -LiteralPath $required -PathType Leaf)) { throw "HEIGHT_DIFFERENCE_1_ENTRY_FILE_MISSING: $required" }
}

$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) { $python = Get-Command py -ErrorAction SilentlyContinue }
if (-not $python) { throw 'PYTHON_EXECUTABLE_NOT_FOUND' }

$guardLines = if ($python.Name -eq 'py.exe' -or $python.Name -eq 'py') {
  & $python.Source -3 $guardPath '--self-test' 2>&1
} else {
  & $python.Source $guardPath '--self-test' 2>&1
}
$guardExit = $LASTEXITCODE
foreach ($line in @($guardLines)) { [Console]::Out.WriteLine([string]$line) }
if ($null -eq $guardExit -or $guardExit -ne 0) {
  Write-Output 'FINAL_READY=false'
  exit $(if ($null -eq $guardExit) { 1 } else { $guardExit })
}

$guardJsonLine = @($guardLines | Where-Object { ([string]$_).TrimStart().StartsWith('{') }) | Select-Object -Last 1
if ($null -eq $guardJsonLine) { throw 'EA_RASTER_GUARD_JSON_MISSING' }
$guardReceipt = ([string]$guardJsonLine) | ConvertFrom-Json
if ($guardReceipt.slot_id -ne 'height_difference_1' -or $guardReceipt.state -ne 'PASS') { throw 'EA_RASTER_GUARD_RECEIPT_INVALID' }
if ([int]$guardReceipt.checks -ne 8) { throw "EA_RASTER_GUARD_CHECK_COUNT_INVALID: $($guardReceipt.checks)" }
if ([string]$guardReceipt.script_version -ne '1.0-ea-classic-tiff-and-nodata-guard') { throw 'EA_RASTER_GUARD_VERSION_INVALID' }
if ([double]$guardReceipt.official_nodata_sentinel -ne [double]-3.4028235e38) { throw 'EA_RASTER_GUARD_SENTINEL_INVALID' }

Write-Output 'EA_RASTER_GUARD_PREFLIGHT=PASS'
Write-Output 'EA_RASTER_GUARD_CHECKS=8'
Write-Output 'EA_WCS_OFFICIAL_NODATA_SENTINEL=-3.4028235e38'

$shell = Get-Command powershell -ErrorAction SilentlyContinue
if (-not $shell) { $shell = Get-Command pwsh -ErrorAction SilentlyContinue }
if (-not $shell) { throw 'POWERSHELL_CHILD_EXECUTABLE_NOT_FOUND' }

$carrierLines = & $shell.Source -NoProfile -ExecutionPolicy Bypass -File $carrierPath 2>&1
$carrierExit = $LASTEXITCODE
foreach ($line in @($carrierLines)) { [Console]::Out.WriteLine([string]$line) }
if ($null -eq $carrierExit) { $carrierExit = 1 }
exit [int]$carrierExit
