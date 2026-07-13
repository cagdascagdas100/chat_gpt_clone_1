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

$oldRowCapture = '                    rows[rid] = cells[0].text.strip()'
$newRowCapture = @'
                    rows[rid] = {
                        "status_text": cells[0].text.strip(),
                        "classes": (tr.get_attribute("class") or "").split()
                    }
'@
$patched = $patched.Replace($oldRowCapture, $newRowCapture.TrimEnd())

$oldRequiredHeaders = '    required_headers = {"Hesap açıklaması","Parcel binding","Ham yerel kaynak","Visible artifact","Status yolu","Rapor yolu","Served commit","Artifact SHA"}'
$newRequiredHeaders = @'
    required_headers = {"Hesap açıklaması","Parcel binding","Ham yerel kaynak","Visible artifact","Status yolu","Rapor yolu","Served commit","Artifact SHA"}
    import unicodedata
    def norm_text(value):
        return " ".join(unicodedata.normalize("NFC", str(value)).split())
    headers_norm = {norm_text(x) for x in headers}
    required_headers_norm = {norm_text(x) for x in required_headers}
'@
$patched = $patched.Replace($oldRequiredHeaders, $newRequiredHeaders.TrimEnd())
$latestClassLine = '    new_count = sum("latest" in rows.get(rid, {}).get("classes", []) for rid in expected_ids)'
$manualClassLine = '    manual_count = sum("manual" in rows.get(rid, {}).get("classes", []) for rid in expected_ids)'
$patched = $patched.Replace('    new_count = sum("YENİ / LATEST" in rows.get(rid, "") for rid in expected_ids)', $latestClassLine)
$patched = $patched.Replace('    manual_count = sum("MANUEL İNCELEME" in rows.get(rid, "") for rid in expected_ids)', $manualClassLine)
$patched = $patched.Replace('required_headers.issubset(set(headers))', 'required_headers_norm.issubset(headers_norm)')

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
if (-not $patched.Contains('rows[rid] = {')) {
  throw 'GAS_EMISSIONS_STANDALONE_IF_FIX_ROW_CLASS_CAPTURE_MISSING'
}
if (-not $patched.Contains('required_headers_norm')) {
  throw 'GAS_EMISSIONS_STANDALONE_IF_FIX_HEADER_NORMALIZATION_MISSING'
}
if (-not $patched.Contains($latestClassLine)) {
  throw 'GAS_EMISSIONS_STANDALONE_IF_FIX_LATEST_CLASS_CHECK_MISSING'
}
if (-not $patched.Contains($manualClassLine)) {
  throw 'GAS_EMISSIONS_STANDALONE_IF_FIX_MANUAL_CLASS_CHECK_MISSING'
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
