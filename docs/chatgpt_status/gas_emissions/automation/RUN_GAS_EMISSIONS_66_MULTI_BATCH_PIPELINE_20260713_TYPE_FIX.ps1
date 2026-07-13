[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'

$repoRoot = [System.IO.Path]::GetFullPath([string]$env:AAYS_REPO_ROOT)
if (-not $repoRoot -or [string]$env:AAYS_PAGE_KEY -ne 'gas_emissions') {
  throw 'GAS_EMISSIONS_66_TYPE_FIX_MUST_RUN_INSIDE_CANONICAL_SHARED_RUNNER'
}
if ([string]$env:AAYS_TARGET_BRANCH -ne 'codex/aays-single-runner-v5-20260706') {
  throw 'GAS_EMISSIONS_66_TYPE_FIX_WRONG_BRANCH'
}

$sourceRel = 'docs\chatgpt_status\gas_emissions\automation\RUN_GAS_EMISSIONS_66_MULTI_BATCH_PIPELINE_20260711.ps1'
$sourcePath = Join-Path $repoRoot $sourceRel
if (-not (Test-Path -LiteralPath $sourcePath)) { throw 'GAS_EMISSIONS_66_ORIGINAL_SCRIPT_NOT_FOUND' }

$source = Get-Content -LiteralPath $sourcePath -Raw -Encoding UTF8
$patched = $source

$oldTarget = '$targetIds=@($verified | ForEach-Object { [string]$_.row_id })'
$newTarget = '$verifiedArray=[object[]]@($verified | ForEach-Object { $_ })' + "`r`n" + '$targetIds=[string[]]@($verifiedArray | ForEach-Object { [string]$_.row_id })'
$patched = $patched.Replace($oldTarget, $newTarget)

$oldRows = '$visible.rows=@($oldRows)+@($verified)'
$newRows = '$visible.rows=[object[]](@($oldRows)+@($verifiedArray))'
$patched = $patched.Replace($oldRows, $newRows)

$oldExpected = 'Write-Json $tmpExpected @($targetIds)'
$newExpected = 'Write-Json -Path $tmpExpected -Value ([object[]]@($targetIds))'
$patched = $patched.Replace($oldExpected, $newExpected)

$oldUi = '($uiAudit.Values -contains $false)'
$newUi = '(@($uiAudit.GetEnumerator() | Where-Object { $_.Value -eq $false }).Count -gt 0)'
$patched = $patched.Replace($oldUi, $newUi)

if ($patched -eq $source) { throw 'GAS_EMISSIONS_66_TYPE_FIX_NO_REPLACEMENTS_APPLIED' }
if ($patched -notmatch [regex]::Escape('$verifiedArray=[object[]]')) { throw 'GAS_EMISSIONS_66_VERIFIED_ARRAY_PATCH_MISSING' }
if ($patched -notmatch [regex]::Escape('$visible.rows=[object[]]')) { throw 'GAS_EMISSIONS_66_COMBINED_ROWS_PATCH_MISSING' }

$tmp = Join-Path ([System.IO.Path]::GetTempPath()) ('gas66_type_fix_' + [Guid]::NewGuid().ToString('N') + '.ps1')
try {
  [System.IO.File]::WriteAllText($tmp, $patched, [System.Text.UTF8Encoding]::new($false))
  & powershell -NoProfile -ExecutionPolicy Bypass -File $tmp
  $exitCode = $LASTEXITCODE
  if ($exitCode -ne 0) { throw "GAS_EMISSIONS_66_TYPE_FIX_CHILD_FAILED: exit=$exitCode" }
} finally {
  Remove-Item -LiteralPath $tmp -Force -ErrorAction SilentlyContinue
}
