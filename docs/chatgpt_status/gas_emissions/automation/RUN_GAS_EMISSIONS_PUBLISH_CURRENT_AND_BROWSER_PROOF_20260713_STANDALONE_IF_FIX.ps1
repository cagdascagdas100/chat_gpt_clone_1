[CmdletBinding()]
param(
  [Parameter(Mandatory=$true)][int]$ExpectedRows
)

$ErrorActionPreference = 'Stop'

$repoRoot = [System.IO.Path]::GetFullPath([string]$env:AAYS_REPO_ROOT)
if (-not $repoRoot -or [string]$env:AAYS_PAGE_KEY -ne 'gas_emissions') {
  throw 'GAS_EMISSIONS_STANDALONE_IF_FIX_WRONG_CONTEXT'
}
if ([string]$env:AAYS_TARGET_BRANCH -ne 'codex/aays-single-runner-v5-20260706') {
  throw 'GAS_EMISSIONS_STANDALONE_IF_FIX_WRONG_BRANCH'
}

$sourceRel = 'docs\chatgpt_status\gas_emissions\automation\RUN_GAS_EMISSIONS_PUBLISH_CURRENT_AND_BROWSER_PROOF_20260713_STANDALONE.ps1'
$sourcePath = Join-Path $repoRoot $sourceRel
if (-not (Test-Path -LiteralPath $sourcePath)) {
  throw 'GAS_EMISSIONS_STANDALONE_SOURCE_NOT_FOUND'
}

$source = Get-Content -LiteralPath $sourcePath -Raw -Encoding UTF8
$patched = $source

$oldStatusLine = '$status | Add-Member -NotePropertyName status -NotePropertyValue (if($browserPassed){"OFFICIAL_VISIBLE_SAMPLE_ROWS_EXPANDED_$ExpectedRows"}else{"OFFICIAL_VISIBLE_SAMPLE_ROWS_EXPANDED_${ExpectedRows}_BROWSER_BLOCKED"}) -Force'
$newStatusBlock = @'
$statusLabel = if ($browserPassed) {
  "OFFICIAL_VISIBLE_SAMPLE_ROWS_EXPANDED_$ExpectedRows"
} else {
  "OFFICIAL_VISIBLE_SAMPLE_ROWS_EXPANDED_${ExpectedRows}_BROWSER_BLOCKED"
}
$status | Add-Member -NotePropertyName status -NotePropertyValue $statusLabel -Force
'@
$patched = $patched.Replace($oldStatusLine, $newStatusBlock.TrimEnd())

$payloadMarker = '$payload = [ordered]@{'
$payloadPrefix = @'
$payloadStatus = if ($browserPassed) {
  'PASS_STANDALONE_LIVE_PUBLISH_AND_BROWSER_PROOF'
} else {
  'FAIL_STANDALONE_BROWSER_PROOF'
}
$payload = [ordered]@{
'@
$patched = $patched.Replace($payloadMarker, $payloadPrefix.TrimEnd())
$patched = $patched.Replace("  status=if(`$browserPassed){'PASS_STANDALONE_LIVE_PUBLISH_AND_BROWSER_PROOF'}else{'FAIL_STANDALONE_BROWSER_PROOF'}", '  status=$payloadStatus')

if ($patched -eq $source) {
  throw 'GAS_EMISSIONS_STANDALONE_IF_FIX_NO_PATCH_APPLIED'
}
if ($patched -match '-NotePropertyValue \(if\(') {
  throw 'GAS_EMISSIONS_STANDALONE_IF_FIX_INVALID_STATUS_EXPRESSION_REMAINS'
}
if ($patched -match 'status=if\(') {
  throw 'GAS_EMISSIONS_STANDALONE_IF_FIX_INVALID_PAYLOAD_EXPRESSION_REMAINS'
}
if ($patched -notmatch '\$statusLabel = if') {
  throw 'GAS_EMISSIONS_STANDALONE_IF_FIX_STATUS_ASSIGNMENT_MISSING'
}
if ($patched -notmatch '\$payloadStatus = if') {
  throw 'GAS_EMISSIONS_STANDALONE_IF_FIX_PAYLOAD_ASSIGNMENT_MISSING'
}

$tmp = Join-Path ([System.IO.Path]::GetTempPath()) ('gas_standalone_if_fix_' + [Guid]::NewGuid().ToString('N') + '.ps1')
try {
  [System.IO.File]::WriteAllText($tmp, $patched, [System.Text.UTF8Encoding]::new($false))
  & powershell -NoProfile -ExecutionPolicy Bypass -File $tmp -ExpectedRows $ExpectedRows
  $exitCode = $LASTEXITCODE
  if ($exitCode -ne 0) {
    throw "GAS_EMISSIONS_STANDALONE_IF_FIX_CHILD_FAILED: exit=$exitCode"
  }
} finally {
  Remove-Item -LiteralPath $tmp -Force -ErrorAction SilentlyContinue
}
