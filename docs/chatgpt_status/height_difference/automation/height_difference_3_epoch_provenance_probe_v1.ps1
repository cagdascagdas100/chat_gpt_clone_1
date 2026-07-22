[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$rawRoot = [string]$env:AAYS_REPO_ROOT
if ([string]::IsNullOrWhiteSpace($rawRoot)) { throw 'AAYS_REPO_ROOT_REQUIRED' }
$root = [System.IO.Path]::GetFullPath($rawRoot)
$script = Join-Path $root 'docs\chatgpt_status\height_difference\automation\height_difference_3_epoch_provenance_probe_v1.py'
if (-not (Test-Path -LiteralPath $script -PathType Leaf)) { throw 'EPOCH_PROVENANCE_PROBE_SCRIPT_NOT_FOUND' }

$python = $null
$prefix = @()
$cmd = Get-Command python -ErrorAction SilentlyContinue
if ($cmd) { $python = $cmd.Source }
if (-not $python) {
  $cmd = Get-Command py -ErrorAction SilentlyContinue
  if ($cmd) { $python = $cmd.Source; $prefix = @('-3') }
}
if (-not $python) {
  $cmd = Get-Command python3 -ErrorAction SilentlyContinue
  if ($cmd) { $python = $cmd.Source }
}
if (-not $python) { throw 'PYTHON_NOT_AVAILABLE' }

Push-Location -LiteralPath $root
try {
  & $python @prefix $script
  $code = $LASTEXITCODE
  Write-Host "HEIGHT_DIFFERENCE_3_EPOCH_PROVENANCE_PROBE_EXIT_CODE=$code"
  Write-Host 'FINAL_READY=false'
  exit $code
}
finally {
  Pop-Location
}
