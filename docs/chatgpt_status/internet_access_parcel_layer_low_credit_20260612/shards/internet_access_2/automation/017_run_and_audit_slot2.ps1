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
$expectedRows = 30761
$automationRoot = Join-Path $RepoRoot "docs/chatgpt_status/internet_access_parcel_layer_low_credit_20260612/shards/internet_access_2/automation"
$webRoot = Join-Path $RepoRoot "england_map_web/data/aays_18_slots/internet_access_2"
$innerRunner = Join-Path $automationRoot "009_probe_download_slice_join_publish_slot2.ps1"
$bundleVerifier = Join-Path $automationRoot "015_verify_published_runner_bundle.py"
$bundleVerifierSelftest = Join-Path $automationRoot "016_selftest_verify_published_runner_bundle.py"
$auditOutput = Join-Path $webRoot "runner_bundle_audit_latest.json"

foreach ($required in @($innerRunner,$bundleVerifier,$bundleVerifierSelftest)) {
    if (-not (Test-Path -LiteralPath $required -PathType Leaf)) { throw "Required file missing: $required" }
}

$selftestRaw = & $PythonExe $bundleVerifierSelftest
if ($LASTEXITCODE -ne 0) { throw "Published bundle verifier self-test failed with exit code $LASTEXITCODE" }
$selftest = $selftestRaw | ConvertFrom-Json
if ($selftest.status -ne "PASS" -or $selftest.tests_passed -ne 18 -or $selftest.tests_total -ne 18) {
    throw "Published bundle verifier self-test contract mismatch"
}

$innerArgs = @("-NoProfile","-ExecutionPolicy","Bypass","-File",$innerRunner,"-RepoRoot",$RepoRoot,"-PythonExe",$PythonExe,"-DownloadRetries",$DownloadRetries)
if ($WorkRoot) { $innerArgs += @("-WorkRoot",$WorkRoot) }
& powershell @innerArgs
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

$auditRaw = & $PythonExe $bundleVerifier --output-root $webRoot --audit-output $auditOutput
if ($LASTEXITCODE -ne 0) { throw "Published runner bundle audit failed with exit code $LASTEXITCODE" }
$audit = $auditRaw | ConvertFrom-Json
if ($audit.status -ne "PASS_REAL_RUN_WEB_BUNDLE_AUDITED_REVIEW_ONLY" -or $audit.canonical_rows -ne $expectedRows) {
    throw "Published runner bundle audit readback mismatch"
}
if ($audit.actual_business_data_rows_written -ne 0 -or $audit.scores_written -ne 0 -or $audit.final_ready -ne $false) {
    throw "Published runner bundle audit violated review-only truth boundary"
}

[ordered]@{
    schema_version = 1
    slot_id = $slotId
    status = "COMPLETE_REAL_RUN_AND_WEB_BUNDLE_AUDITED_REVIEW_ONLY"
    canonical_rows = $audit.canonical_rows
    visible_example_rows = $audit.visible_example_rows
    runner_bundle_audit = $auditOutput
    actual_business_data_rows_written = 0
    scores_written = 0
    db_write = $false
    migration = $false
    production_deploy = $false
    final_ready = $false
} | ConvertTo-Json -Depth 8
