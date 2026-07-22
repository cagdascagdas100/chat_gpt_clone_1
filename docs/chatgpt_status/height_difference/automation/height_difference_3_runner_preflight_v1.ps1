[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$rawRoot = [string]$env:AAYS_REPO_ROOT
if ([string]::IsNullOrWhiteSpace($rawRoot)) { throw 'AAYS_REPO_ROOT_REQUIRED' }
$root = [System.IO.Path]::GetFullPath($rawRoot)
if (-not (Test-Path -LiteralPath $root -PathType Container)) { throw 'AAYS_REPO_ROOT_NOT_FOUND' }
if ([string]$env:AAYS_TASK_ID -ne 'height-difference-3-canonical-point-extract-v1-1-20260722') { throw 'AAYS_TASK_ID_MISMATCH' }

$script = Join-Path $root 'docs\chatgpt_status\height_difference\automation\height_difference_3_runner_preflight_v1.py'
$manifest = Join-Path $root 'docs\chatgpt_status\height_difference\recovery\height_difference_3_runner_preflight_v1_manifest.json'
$output = Join-Path $root 'docs\chatgpt_status\height_difference\runner_outputs\height_difference_3_runner_preflight_latest.json'
$website = Join-Path $root 'england_map_web\data\height_difference\height_difference_3_runner_preflight_latest.json'
foreach ($path in @($script,$manifest)) {
  if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { throw ('REQUIRED_FILE_MISSING:' + $path) }
}

$python = Get-Command python -ErrorAction SilentlyContinue | Select-Object -First 1
$args = @()
if ($null -eq $python) {
  $python = Get-Command py -ErrorAction SilentlyContinue | Select-Object -First 1
  if ($null -eq $python) {
    $python = Get-Command python3 -ErrorAction SilentlyContinue | Select-Object -First 1
  } else {
    $args += '-3'
  }
}
if ($null -eq $python) { throw 'PYTHON_COMMAND_NOT_AVAILABLE' }
$args += @($script,'--repo-root',$root,'--manifest',$manifest,'--output',$output,'--website-output',$website)
& $python.Source @args
$code = $LASTEXITCODE
Write-Host ('HEIGHT_DIFFERENCE_3_PREFLIGHT_EXIT_CODE=' + $code)
Write-Host 'FINAL_READY=false'
exit $code
