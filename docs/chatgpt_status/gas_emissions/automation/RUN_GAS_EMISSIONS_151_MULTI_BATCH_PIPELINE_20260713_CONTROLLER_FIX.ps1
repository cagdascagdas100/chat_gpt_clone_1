[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$repoRoot = [System.IO.Path]::GetFullPath([string]$env:AAYS_REPO_ROOT)
if (-not $repoRoot -or [string]$env:AAYS_PAGE_KEY -ne 'gas_emissions') { throw 'GAS_EMISSIONS_151_FIX_WRONG_CONTEXT' }
if ([string]$env:AAYS_TARGET_BRANCH -ne 'codex/aays-single-runner-v5-20260706') { throw 'GAS_EMISSIONS_151_FIX_WRONG_BRANCH' }
$controllerRoot = [string]$env:AAYS_CONTROLLER_REPO_ROOT
if (-not $controllerRoot) { throw 'AAYS_CONTROLLER_REPO_ROOT_MISSING' }

$sourcePath = Join-Path $repoRoot 'docs\chatgpt_status\gas_emissions\automation\run_gas_emissions_151_pipeline_20260711.py'
$repairPath = Join-Path $repoRoot 'docs\chatgpt_status\gas_emissions\automation\REPAIR_GAS_EMISSIONS_8012_PUBLISH_ROOT_20260715.ps1'
if (-not (Test-Path -LiteralPath $sourcePath)) { throw 'GAS_EMISSIONS_151_PYTHON_SOURCE_NOT_FOUND' }
if (-not (Test-Path -LiteralPath $repairPath)) { throw 'GAS_EMISSIONS_8012_REPAIR_NOT_FOUND' }
$source = Get-Content -LiteralPath $sourcePath -Raw -Encoding UTF8
$old = 'SERVED_ROOT = Path(r"F:\TerraYield_AAYS_Portable\runner_system\AAYS_WT\AAYS_RUNNER_HEALTHY_20260707")'
$new = 'SERVED_ROOT = Path(os.environ["AAYS_CONTROLLER_REPO_ROOT"])'
$patched = $source.Replace($old,$new)
if ($patched -eq $source) { throw 'GAS_EMISSIONS_151_CONTROLLER_PATCH_NOT_APPLIED' }

$tmp = Join-Path ([System.IO.Path]::GetTempPath()) ('gas151_fix_' + [Guid]::NewGuid().ToString('N') + '.py')
try {
  [System.IO.File]::WriteAllText($tmp,$patched,[System.Text.UTF8Encoding]::new($false))
  $python = Get-Command python -ErrorAction SilentlyContinue
  if ($python) {
    $childOutput = @(& $python.Source $tmp 2>&1)
  } else {
    $py = Get-Command py -ErrorAction Stop
    $childOutput = @(& $py.Source -3 $tmp 2>&1)
  }
  $childExit = $LASTEXITCODE

  if ($childExit -ne 0 -and (($childOutput | Out-String) -match 'HTTP_8012_ROW_COUNT_NOT_151')) {
    & powershell -NoProfile -ExecutionPolicy Bypass -File $repairPath -ExpectedRows 151
    if ($LASTEXITCODE -ne 0) { throw 'GAS_EMISSIONS_151_8012_REPAIR_FAILED' }
    if ($python) {
      $childOutput = @(& $python.Source $tmp 2>&1)
    } else {
      $childOutput = @(& $py.Source -3 $tmp 2>&1)
    }
    $childExit = $LASTEXITCODE
  }

  $childOutput | ForEach-Object { Write-Output $_ }
  if ($childExit -ne 0) { throw "GAS_EMISSIONS_151_FIX_CHILD_FAILED: exit=$childExit" }
} finally {
  Remove-Item -LiteralPath $tmp -Force -ErrorAction SilentlyContinue
}
