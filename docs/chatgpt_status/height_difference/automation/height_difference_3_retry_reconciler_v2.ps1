[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$rawRoot = [string]$env:AAYS_REPO_ROOT
if ([string]::IsNullOrWhiteSpace($rawRoot)) { throw 'AAYS_REPO_ROOT_REQUIRED' }
$root = [System.IO.Path]::GetFullPath($rawRoot)
if (-not (Test-Path -LiteralPath $root -PathType Container)) { throw 'AAYS_REPO_ROOT_NOT_FOUND' }
$taskId = [string]$env:AAYS_TASK_ID
if ([string]::IsNullOrWhiteSpace($taskId)) { throw 'AAYS_TASK_ID_REQUIRED' }

$manifest = Join-Path $root 'docs\chatgpt_status\height_difference\recovery\height_difference_3_retry_reconciler_v2_manifest.json'
$validator = Join-Path $root 'docs\chatgpt_status\height_difference\automation\height_difference_3_checkpoint_validator_v2.py'
$reconciler = Join-Path $root 'docs\chatgpt_status\height_difference\automation\height_difference_3_retry_reconciler_v2.py'
foreach ($path in @($manifest,$validator,$reconciler)) {
  if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { throw ('REQUIRED_FILE_MISSING:' + $path) }
}

$python = Get-Command python -ErrorAction SilentlyContinue | Select-Object -First 1
$args = @()
if ($null -eq $python) {
  $python = Get-Command py -ErrorAction SilentlyContinue | Select-Object -First 1
  if ($null -eq $python) { throw 'PYTHON_COMMAND_NOT_AVAILABLE' }
  $args += '-3'
}
$args += @($reconciler,'--repo-root',$root,'--manifest',$manifest,'--validator',$validator,'--current-task-id',$taskId)
& $python.Source @args
$code = $LASTEXITCODE
Write-Host ('HEIGHT_DIFFERENCE_3_RECONCILER_V2_EXIT_CODE=' + $code)
Write-Host 'FINAL_READY=false'
exit $code
