[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$repoRoot = [System.IO.Path]::GetFullPath([string]$env:AAYS_REPO_ROOT)
if (-not $repoRoot -or [string]$env:AAYS_PAGE_KEY -ne 'gas_emissions') { throw 'GAS_EMISSIONS_YEAR_FIX_WRONG_CONTEXT' }
if ([string]$env:AAYS_TARGET_BRANCH -ne 'codex/aays-single-runner-v5-20260706') { throw 'GAS_EMISSIONS_YEAR_FIX_WRONG_BRANCH' }
if (-not [string]$env:AAYS_CONTROLLER_REPO_ROOT) { throw 'AAYS_CONTROLLER_REPO_ROOT_MISSING' }

$sourcePath = Join-Path $repoRoot 'docs\chatgpt_status\gas_emissions\automation\RUN_GAS_EMISSIONS_YEAR_SELECTOR_EXPANSION_20260711.ps1'
if (-not (Test-Path -LiteralPath $sourcePath)) { throw 'GAS_EMISSIONS_YEAR_SOURCE_NOT_FOUND' }
$source = Get-Content -LiteralPath $sourcePath -Raw -Encoding UTF8
$patched = $source

$oldServed = '$servedRepoRoot = ''F:\TerraYield_AAYS_Portable\runner_system\AAYS_WT\AAYS_RUNNER_HEALTHY_20260707'''
$newServed = '$servedRepoRoot = [string]$env:AAYS_CONTROLLER_REPO_ROOT; if (-not $servedRepoRoot) { throw ''AAYS_CONTROLLER_REPO_ROOT_MISSING'' }'
$patched = $patched.Replace($oldServed,$newServed)

$oldIds = '$ids = @($verified | ForEach-Object { [string]$_.row_id })'
$newIds = '$verifiedArray = [object[]]@($verified | ForEach-Object { $_ })' + "`r`n" + '$ids = [string[]]@($verifiedArray | ForEach-Object { [string]$_.row_id })'
$patched = $patched.Replace($oldIds,$newIds)

$oldRows = '$visible.rows = @($oldRows) + @($verified)'
$newRows = '$visible.rows = [object[]](@($oldRows) + @($verifiedArray))'
$patched = $patched.Replace($oldRows,$newRows)

$patched = $patched.Replace('Write-Json $expectedIdsPath $ids','Write-Json -Path $expectedIdsPath -Value ([object[]]@($ids))')
$patched = $patched.Replace('($uiAudit.Values -contains $false)','(@($uiAudit.GetEnumerator() | Where-Object { $_.Value -eq $false }).Count -gt 0)')

if ($patched -eq $source) { throw 'GAS_EMISSIONS_YEAR_FIX_NOT_APPLIED' }
if ($patched -notmatch [regex]::Escape('$env:AAYS_CONTROLLER_REPO_ROOT')) { throw 'GAS_EMISSIONS_YEAR_CONTROLLER_PATCH_MISSING' }
if ($patched -notmatch [regex]::Escape('$verifiedArray')) { throw 'GAS_EMISSIONS_YEAR_ARRAY_PATCH_MISSING' }

$tmp = Join-Path ([System.IO.Path]::GetTempPath()) ('gas_year_fix_' + [Guid]::NewGuid().ToString('N') + '.ps1')
try {
  [System.IO.File]::WriteAllText($tmp,$patched,[System.Text.UTF8Encoding]::new($false))
  & powershell -NoProfile -ExecutionPolicy Bypass -File $tmp
  if ($LASTEXITCODE -ne 0) { throw "GAS_EMISSIONS_YEAR_FIX_CHILD_FAILED: exit=$LASTEXITCODE" }
} finally {
  Remove-Item -LiteralPath $tmp -Force -ErrorAction SilentlyContinue
}
