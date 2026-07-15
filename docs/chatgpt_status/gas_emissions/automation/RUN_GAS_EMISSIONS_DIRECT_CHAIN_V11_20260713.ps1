[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'

$repoRoot = [System.IO.Path]::GetFullPath([string]$env:AAYS_REPO_ROOT)
if (-not $repoRoot -or [string]$env:AAYS_PAGE_KEY -ne 'gas_emissions') {
  throw 'GAS_EMISSIONS_DIRECT_CHAIN_V11_WRONG_CONTEXT'
}
if ([string]$env:AAYS_TARGET_BRANCH -ne 'codex/aays-single-runner-v5-20260706') {
  throw 'GAS_EMISSIONS_DIRECT_CHAIN_V11_WRONG_BRANCH'
}

$v7Rel = 'docs\chatgpt_status\gas_emissions\automation\RUN_GAS_EMISSIONS_DIRECT_CHAIN_V7_20260713.ps1'
$v7Path = Join-Path $repoRoot $v7Rel
$repairPath = Join-Path $repoRoot 'docs\chatgpt_status\gas_emissions\automation\REPAIR_GAS_EMISSIONS_8012_PUBLISH_ROOT_20260715.ps1'
$rowsPath = Join-Path $repoRoot 'england_map_web\data\program_layer_matrix\gas_emissions_visible_rows_latest.json'
if (-not (Test-Path -LiteralPath $v7Path)) {
  throw 'GAS_EMISSIONS_DIRECT_CHAIN_V7_SOURCE_NOT_FOUND'
}
if (-not (Test-Path -LiteralPath $repairPath)) {
  throw 'GAS_EMISSIONS_8012_REPAIR_NOT_FOUND'
}

if (Test-Path -LiteralPath $rowsPath) {
  $currentRowsObject = Get-Content -LiteralPath $rowsPath -Raw -Encoding UTF8 | ConvertFrom-Json
  $currentRows = @($currentRowsObject.rows).Count
  if ($currentRows -in @(100,151,233,316)) {
    & powershell -NoProfile -ExecutionPolicy Bypass -File $repairPath -ExpectedRows $currentRows
    if ($LASTEXITCODE -ne 0) {
      throw "GAS_EMISSIONS_V11_LIVE_ROOT_PREFLIGHT_FAILED: rows=$currentRows"
    }
  }
}

$source = Get-Content -LiteralPath $v7Path -Raw -Encoding UTF8
$patched = $source
$patched = $patched.Replace(
  'docs/chatgpt_status/gas_emissions/automation/RUN_GAS_EMISSIONS_PUBLISH_CURRENT_AND_BROWSER_PROOF_20260713_DOM_READY_FIX.ps1',
  'docs/chatgpt_status/gas_emissions/automation/RUN_GAS_EMISSIONS_PUBLISH_CURRENT_AND_BROWSER_PROOF_20260713_STANDALONE_IF_FIX.ps1'
)
$patched = $patched.Replace('178_gas_emissions_direct_chain_v7_20260713_latest.json','183_gas_emissions_direct_chain_v11_20260713_latest.json')
$patched = $patched.Replace("chain_version='v7_20260713'","chain_version='v11_20260713'")
$patched = $patched.Replace("'v7_20260713'","'v11_20260713'")
$patched = $patched.Replace('GAS_EMISSIONS_DIRECT_CHAIN_V7_WRONG_CONTEXT','GAS_EMISSIONS_DIRECT_CHAIN_V11_WRONG_CONTEXT')
$patched = $patched.Replace('GAS_EMISSIONS_DIRECT_CHAIN_V7_WRONG_BRANCH','GAS_EMISSIONS_DIRECT_CHAIN_V11_WRONG_BRANCH')

if ($patched -eq $source) {
  throw 'GAS_EMISSIONS_DIRECT_CHAIN_V11_NO_PATCH_APPLIED'
}
if ($patched -notmatch 'STANDALONE_IF_FIX') {
  throw 'GAS_EMISSIONS_DIRECT_CHAIN_V11_PROOF_ROUTE_MISSING'
}
if ($patched -notmatch '183_gas_emissions_direct_chain_v11') {
  throw 'GAS_EMISSIONS_DIRECT_CHAIN_V11_REPORT_ROUTE_MISSING'
}

$tmp = Join-Path ([System.IO.Path]::GetTempPath()) ('gas_direct_chain_v11_' + [Guid]::NewGuid().ToString('N') + '.ps1')
try {
  [System.IO.File]::WriteAllText($tmp, $patched, [System.Text.UTF8Encoding]::new($false))
  & powershell -NoProfile -ExecutionPolicy Bypass -File $tmp
  $exitCode = $LASTEXITCODE
  if ($exitCode -ne 0) {
    [Console]::Error.WriteLine("GAS_EMISSIONS_DIRECT_CHAIN_V11_CHILD_FAILED: exit=$exitCode")
    exit $exitCode
  }
} finally {
  Remove-Item -LiteralPath $tmp -Force -ErrorAction SilentlyContinue
}
exit 0
