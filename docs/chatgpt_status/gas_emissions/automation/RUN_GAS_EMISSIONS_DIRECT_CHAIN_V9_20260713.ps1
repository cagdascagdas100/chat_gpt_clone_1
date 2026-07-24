[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'

$repoRoot = [System.IO.Path]::GetFullPath([string]$env:AAYS_REPO_ROOT)
if (-not $repoRoot -or [string]$env:AAYS_PAGE_KEY -ne 'gas_emissions') {
  throw 'GAS_EMISSIONS_DIRECT_CHAIN_V9_WRONG_CONTEXT'
}
if ([string]$env:AAYS_TARGET_BRANCH -ne 'codex/aays-single-runner-v5-20260706') {
  throw 'GAS_EMISSIONS_DIRECT_CHAIN_V9_WRONG_BRANCH'
}

$v8Rel = 'docs\chatgpt_status\gas_emissions\automation\RUN_GAS_EMISSIONS_DIRECT_CHAIN_V8_20260713.ps1'
$v8Path = Join-Path $repoRoot $v8Rel
if (-not (Test-Path -LiteralPath $v8Path)) {
  throw 'GAS_EMISSIONS_DIRECT_CHAIN_V8_SOURCE_NOT_FOUND'
}

$source = Get-Content -LiteralPath $v8Path -Raw -Encoding UTF8
$patched = $source
$patched = $patched.Replace(
  'docs/chatgpt_status/gas_emissions/automation/RUN_GAS_EMISSIONS_PUBLISH_CURRENT_AND_BROWSER_PROOF_20260713_ASYNC_DOM_FIX.ps1',
  'docs/chatgpt_status/gas_emissions/automation/RUN_GAS_EMISSIONS_PUBLISH_CURRENT_AND_BROWSER_PROOF_20260713_ASYNC_DOM_FIX_V2.ps1'
)
$patched = $patched.Replace('179_gas_emissions_direct_chain_v8_20260713_latest.json','180_gas_emissions_direct_chain_v9_20260713_latest.json')
$patched = $patched.Replace("chain_version='v8_20260713'","chain_version='v9_20260713'")
$patched = $patched.Replace("'v8_20260713'","'v9_20260713'")
$patched = $patched.Replace('GAS_EMISSIONS_DIRECT_CHAIN_V8_WRONG_CONTEXT','GAS_EMISSIONS_DIRECT_CHAIN_V9_WRONG_CONTEXT')
$patched = $patched.Replace('GAS_EMISSIONS_DIRECT_CHAIN_V8_WRONG_BRANCH','GAS_EMISSIONS_DIRECT_CHAIN_V9_WRONG_BRANCH')
$patched = $patched.Replace('GAS_EMISSIONS_DIRECT_CHAIN_V8_NO_PATCH_APPLIED','GAS_EMISSIONS_DIRECT_CHAIN_V9_SOURCE_PATCH_FAILED')
$patched = $patched.Replace('GAS_EMISSIONS_DIRECT_CHAIN_V8_PROOF_ROUTE_MISSING','GAS_EMISSIONS_DIRECT_CHAIN_V9_OLD_PROOF_ROUTE_CHECK')
$patched = $patched.Replace('GAS_EMISSIONS_DIRECT_CHAIN_V8_REPORT_ROUTE_MISSING','GAS_EMISSIONS_DIRECT_CHAIN_V9_OLD_REPORT_ROUTE_CHECK')
$patched = $patched.Replace('gas_direct_chain_v8_','gas_direct_chain_v9_')
$patched = $patched.Replace('GAS_EMISSIONS_DIRECT_CHAIN_V8_CHILD_FAILED','GAS_EMISSIONS_DIRECT_CHAIN_V9_CHILD_FAILED')

if ($patched -eq $source) {
  throw 'GAS_EMISSIONS_DIRECT_CHAIN_V9_NO_PATCH_APPLIED'
}
if ($patched -notmatch 'ASYNC_DOM_FIX_V2') {
  throw 'GAS_EMISSIONS_DIRECT_CHAIN_V9_PROOF_ROUTE_MISSING'
}
if ($patched -notmatch '180_gas_emissions_direct_chain_v9') {
  throw 'GAS_EMISSIONS_DIRECT_CHAIN_V9_REPORT_ROUTE_MISSING'
}

$tmp = Join-Path ([System.IO.Path]::GetTempPath()) ('gas_direct_chain_v9_' + [Guid]::NewGuid().ToString('N') + '.ps1')
try {
  [System.IO.File]::WriteAllText($tmp, $patched, [System.Text.UTF8Encoding]::new($false))
  & powershell -NoProfile -ExecutionPolicy Bypass -File $tmp
  $exitCode = $LASTEXITCODE
  if ($exitCode -ne 0) {
    throw "GAS_EMISSIONS_DIRECT_CHAIN_V9_CHILD_FAILED: exit=$exitCode"
  }
} finally {
  Remove-Item -LiteralPath $tmp -Force -ErrorAction SilentlyContinue
}
