[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'

$repoRoot = [System.IO.Path]::GetFullPath([string]$env:AAYS_REPO_ROOT)
if (-not $repoRoot -or [string]$env:AAYS_PAGE_KEY -ne '_shared') {
  throw 'GAS_EMISSIONS_DISPATCH_V6_WRONG_CONTEXT'
}
if ([string]$env:AAYS_TARGET_BRANCH -ne 'codex/aays-single-runner-v5-20260706') {
  throw 'GAS_EMISSIONS_DISPATCH_V6_WRONG_BRANCH'
}

$v5Rel = 'docs\chatgpt_status\_shared\automation\RUN_GAS_EMISSIONS_CANONICAL_DISPATCH_V5_20260713.ps1'
$v5Path = Join-Path $repoRoot $v5Rel
if (-not (Test-Path -LiteralPath $v5Path)) {
  throw 'GAS_EMISSIONS_DISPATCH_V5_SOURCE_NOT_FOUND'
}

$source = Get-Content -LiteralPath $v5Path -Raw -Encoding UTF8
$old = 'docs/chatgpt_status/gas_emissions/automation/RUN_GAS_EMISSIONS_PUBLISH_CURRENT_AND_BROWSER_PROOF_20260713.ps1'
$new = 'docs/chatgpt_status/gas_emissions/automation/RUN_GAS_EMISSIONS_PUBLISH_CURRENT_AND_BROWSER_PROOF_20260713_DOM_READY_FIX.ps1'
$patched = $source.Replace($old, $new)
if ($patched -eq $source) {
  throw 'GAS_EMISSIONS_DISPATCH_V6_PROOF_ROUTE_PATCH_NOT_APPLIED'
}

$tmp = Join-Path ([System.IO.Path]::GetTempPath()) ('gas_dispatch_v6_' + [Guid]::NewGuid().ToString('N') + '.ps1')
try {
  [System.IO.File]::WriteAllText($tmp, $patched, [System.Text.UTF8Encoding]::new($false))
  & powershell -NoProfile -ExecutionPolicy Bypass -File $tmp
  $exitCode = $LASTEXITCODE
  if ($exitCode -ne 0) {
    throw "GAS_EMISSIONS_DISPATCH_V6_CHILD_FAILED: exit=$exitCode"
  }
} finally {
  Remove-Item -LiteralPath $tmp -Force -ErrorAction SilentlyContinue
}
