[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$RepoRoot,
    [string]$PythonExe = "python",
    [string]$WorkRoot = "",
    [int]$DownloadRetries = 4
)

$ErrorActionPreference = "Stop"
$slotId = "internet_access_2"
$automationRoot = Join-Path $RepoRoot "docs/chatgpt_status/internet_access_parcel_layer_low_credit_20260612/shards/internet_access_2/automation"
$baseRunner = Join-Path $automationRoot "009_probe_download_slice_join_publish_slot2.ps1"
$coverageExtractor = Join-Path $automationRoot "030_extract_slot2_coverage_aware_candidates.py"
$coverageSelftest = Join-Path $automationRoot "031_selftest_extract_slot2_coverage_aware_candidates.py"
$effectiveWorkRoot = if ($WorkRoot) { $WorkRoot } else { Join-Path $RepoRoot "outputs/internet_access_2_verified_run" }
$runtimeScript = Join-Path $effectiveWorkRoot "internet_access_2_coverage_aware_inner_runtime.ps1"
$carrierOutput = Join-Path $effectiveWorkRoot "internet_access_2_coverage_aware_carrier_latest.json"

foreach ($required in @($baseRunner,$coverageExtractor,$coverageSelftest)) {
    if (-not (Test-Path -LiteralPath $required -PathType Leaf)) { throw "Required coverage-aware carrier file missing: $required" }
}
New-Item -ItemType Directory -Force -Path $effectiveWorkRoot | Out-Null

$selftestRaw = & $PythonExe $coverageSelftest
if ($LASTEXITCODE -ne 0) { throw "Coverage-aware extractor self-test failed with exit code $LASTEXITCODE" }
$selftest = $selftestRaw | ConvertFrom-Json
if ($selftest.status -ne "PASS" -or $selftest.tests_passed -ne 20 -or $selftest.tests_total -ne 20) {
    throw "Coverage-aware extractor self-test contract mismatch"
}

$baseText = Get-Content -Raw -LiteralPath $baseRunner
$needle = '$extractor = Join-Path $automationRoot "002_extract_slot2_ofcom_2026_candidates.py"'
$replacement = '$extractor = Join-Path $automationRoot "030_extract_slot2_coverage_aware_candidates.py"'
$replacementCount = ([regex]::Matches($baseText, [regex]::Escape($needle))).Count
if ($replacementCount -ne 1) { throw "Coverage-aware carrier expected exactly one extractor replacement, found $replacementCount" }
$runtimeText = $baseText.Replace($needle, $replacement)
if ($runtimeText -eq $baseText -or $runtimeText.Contains($needle) -or -not $runtimeText.Contains($replacement)) {
    throw "Coverage-aware carrier replacement verification failed"
}
Set-Content -LiteralPath $runtimeScript -Value $runtimeText -Encoding UTF8

$baseSha = (Get-FileHash -Algorithm SHA256 -LiteralPath $baseRunner).Hash.ToLowerInvariant()
$runtimeSha = (Get-FileHash -Algorithm SHA256 -LiteralPath $runtimeScript).Hash.ToLowerInvariant()
$innerArgs = @("-NoProfile","-ExecutionPolicy","Bypass","-File",$runtimeScript,"-RepoRoot",$RepoRoot,"-PythonExe",$PythonExe,"-WorkRoot",$effectiveWorkRoot,"-DownloadRetries",$DownloadRetries)
& powershell @innerArgs
$innerExitCode = $LASTEXITCODE

$status = if ($innerExitCode -eq 0) { "PASS_COVERAGE_AWARE_INNER_CARRIER_COMPLETED_REVIEW_ONLY" } else { "BLOCKED_COVERAGE_AWARE_INNER_CARRIER_EXECUTION" }
[ordered]@{
    schema_version = 1
    slot_id = $slotId
    status = $status
    base_runner = $baseRunner
    base_runner_sha256 = $baseSha
    runtime_carrier = $runtimeScript
    runtime_carrier_sha256 = $runtimeSha
    coverage_aware_extractor = $coverageExtractor
    extractor_replacement_count = $replacementCount
    coverage_aware_extractor_selftest = [ordered]@{ passed = $selftest.tests_passed; total = $selftest.tests_total }
    inner_exit_code = $innerExitCode
    actual_business_data_rows_written = 0
    scores_written = 0
    db_write = $false
    migration = $false
    production_deploy = $false
    final_ready = $false
} | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $carrierOutput -Encoding UTF8

if ($innerExitCode -ne 0) { exit $innerExitCode }
Get-Content -Raw -LiteralPath $carrierOutput
