[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$repoRoot = [System.IO.Path]::GetFullPath([string]$env:AAYS_REPO_ROOT)
if (-not $repoRoot -or [string]$env:AAYS_PAGE_KEY -ne 'gas_emissions') {
  throw 'GAS_EMISSIONS_37_FIX_WRAPPER_MUST_RUN_INSIDE_CANONICAL_SHARED_RUNNER'
}
$source = Join-Path $repoRoot 'docs\chatgpt_status\gas_emissions\automation\RUN_GAS_EMISSIONS_37_MULTI_STAGE_PIPELINE_20260711.ps1'
if (-not (Test-Path -LiteralPath $source)) { throw 'GAS_EMISSIONS_37_SOURCE_SCRIPT_MISSING' }
$text = Get-Content -LiteralPath $source -Raw -Encoding UTF8
$bad = '$actualTerritorial = [double]$_ = [double]$m.''Territorial emissions (kt CO2e)'''
$good = '$actualTerritorial = [double]$m.''Territorial emissions (kt CO2e)'''
if (-not $text.Contains($bad)) { throw 'EXPECTED_FIX_TARGET_NOT_FOUND' }
$fixed = $text.Replace($bad, $good)
$tmp = Join-Path ([System.IO.Path]::GetTempPath()) ('gas_emissions_37_fixed_' + [Guid]::NewGuid().ToString('N') + '.ps1')
[System.IO.File]::WriteAllText($tmp, $fixed, [System.Text.UTF8Encoding]::new($false))
try {
  & powershell -NoProfile -ExecutionPolicy Bypass -File $tmp
  $code = $LASTEXITCODE
  if ($code -ne 0) { throw "GAS_EMISSIONS_37_FIXED_PIPELINE_EXIT_$code" }
} finally {
  Remove-Item -LiteralPath $tmp -Force -ErrorAction SilentlyContinue
}
