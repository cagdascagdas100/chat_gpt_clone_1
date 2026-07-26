[CmdletBinding()]
param(
  [int]$Timeout = 120
)

$ErrorActionPreference = 'Stop'
$rawRoot = [string]$env:AAYS_REPO_ROOT
if ([string]::IsNullOrWhiteSpace($rawRoot)) {
  $rawRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..\..\..\..')).Path
}
$repoRoot = [System.IO.Path]::GetFullPath($rawRoot).TrimEnd('\')
if (-not (Test-Path -LiteralPath $repoRoot -PathType Container)) { throw 'AAYS_REPO_ROOT_NOT_FOUND' }

$entry = Join-Path $repoRoot 'docs\chatgpt_status\topography\shards\height_difference_3\automation\028_execute_batch116_strict_proj_and_four_candidate_chain.py'
$candidates = Join-Path $repoRoot 'docs\chatgpt_status\topography\shards\height_difference_3\runner_inputs\059_candidate_manifest_61536_61539_batch_115.json'
$outputDir = Join-Path $repoRoot 'docs\chatgpt_status\topography\shards\height_difference_3\runner_outputs\012_strict_four_candidate_full_chain_batch_116'
foreach ($path in @($entry,$candidates)) {
  if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { throw ('REQUIRED_FILE_MISSING:' + $path) }
}

$python = Get-Command python -ErrorAction SilentlyContinue | Select-Object -First 1
$args = @()
if ($null -eq $python) {
  $python = Get-Command py -ErrorAction SilentlyContinue | Select-Object -First 1
  if ($null -eq $python) { throw 'PYTHON_COMMAND_NOT_AVAILABLE' }
  $args += '-3'
}
$args += @($entry,'--candidate-manifest',$candidates,'--output-dir',$outputDir,'--timeout',[string]$Timeout)

& $python.Source @args
$code = $LASTEXITCODE
Write-Host ('HEIGHT_DIFFERENCE_3_BATCH116_STRICT_CHAIN_EXIT_CODE=' + $code)
Write-Host 'SINGLE_SHARED_RUNNER_ONLY=true'
Write-Host 'NEW_RUNNER=false'
Write-Host 'PARALLEL_RUNNER=false'
Write-Host 'FINAL_READY=false'
exit $code
