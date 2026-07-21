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
$effectiveWorkRoot = if ($WorkRoot) { $WorkRoot } else { Join-Path $RepoRoot "outputs/internet_access_2_verified_run" }
$innerRunner = Join-Path $automationRoot "009_probe_download_slice_join_publish_slot2.ps1"
$bundleVerifier = Join-Path $automationRoot "015_verify_published_runner_bundle.py"
$bundleVerifierSelftest = Join-Path $automationRoot "016_selftest_verify_published_runner_bundle.py"
$provenanceVerifier = Join-Path $automationRoot "019_verify_single_run_provenance.py"
$provenanceVerifierSelftest = Join-Path $automationRoot "020_selftest_verify_single_run_provenance.py"
$bundleAuditOutput = Join-Path $webRoot "runner_bundle_audit_latest.json"
$provenanceAuditOutput = Join-Path $webRoot "runner_provenance_audit_latest.json"

foreach ($required in @($innerRunner,$bundleVerifier,$bundleVerifierSelftest,$provenanceVerifier,$provenanceVerifierSelftest)) {
    if (-not (Test-Path -LiteralPath $required -PathType Leaf)) { throw "Required file missing: $required" }
}

$bundleSelftestRaw = & $PythonExe $bundleVerifierSelftest
if ($LASTEXITCODE -ne 0) { throw "Published bundle verifier self-test failed with exit code $LASTEXITCODE" }
$bundleSelftest = $bundleSelftestRaw | ConvertFrom-Json
if ($bundleSelftest.status -ne "PASS" -or $bundleSelftest.tests_passed -ne 18 -or $bundleSelftest.tests_total -ne 18) {
    throw "Published bundle verifier self-test contract mismatch"
}

$provenanceSelftestRaw = & $PythonExe $provenanceVerifierSelftest
if ($LASTEXITCODE -ne 0) { throw "Single-run provenance verifier self-test failed with exit code $LASTEXITCODE" }
$provenanceSelftest = $provenanceSelftestRaw | ConvertFrom-Json
if ($provenanceSelftest.status -ne "PASS" -or $provenanceSelftest.tests_passed -ne 20 -or $provenanceSelftest.tests_total -ne 20) {
    throw "Single-run provenance verifier self-test contract mismatch"
}

$innerArgs = @("-NoProfile","-ExecutionPolicy","Bypass","-File",$innerRunner,"-RepoRoot",$RepoRoot,"-PythonExe",$PythonExe,"-WorkRoot",$effectiveWorkRoot,"-DownloadRetries",$DownloadRetries)
& powershell @innerArgs
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

$bundleAuditRaw = & $PythonExe $bundleVerifier --output-root $webRoot --audit-output $bundleAuditOutput
if ($LASTEXITCODE -ne 0) { throw "Published runner bundle audit failed with exit code $LASTEXITCODE" }
$bundleAudit = $bundleAuditRaw | ConvertFrom-Json
if ($bundleAudit.status -ne "PASS_REAL_RUN_WEB_BUNDLE_AUDITED_REVIEW_ONLY" -or $bundleAudit.canonical_rows -ne $expectedRows) {
    throw "Published runner bundle audit readback mismatch"
}
if ($bundleAudit.actual_business_data_rows_written -ne 0 -or $bundleAudit.scores_written -ne 0 -or $bundleAudit.final_ready -ne $false) {
    throw "Published runner bundle audit violated review-only truth boundary"
}

$provenanceAuditRaw = & $PythonExe $provenanceVerifier --work-root $effectiveWorkRoot --web-root $webRoot --audit-output $provenanceAuditOutput
if ($LASTEXITCODE -ne 0) { throw "Single-run provenance audit failed with exit code $LASTEXITCODE" }
$provenanceAudit = $provenanceAuditRaw | ConvertFrom-Json
if ($provenanceAudit.status -ne "PASS_SINGLE_RUN_PROVENANCE_CHAIN_AUDITED_REVIEW_ONLY" -or $provenanceAudit.canonical_rows -ne $expectedRows) {
    throw "Single-run provenance audit readback mismatch"
}
if ($provenanceAudit.actual_business_data_rows_written -ne 0 -or $provenanceAudit.scores_written -ne 0 -or $provenanceAudit.final_ready -ne $false) {
    throw "Single-run provenance audit violated review-only truth boundary"
}

[ordered]@{
    schema_version = 2
    slot_id = $slotId
    status = "COMPLETE_REAL_RUN_WEB_BUNDLE_AND_PROVENANCE_AUDITED_REVIEW_ONLY"
    canonical_rows = $provenanceAudit.canonical_rows
    visible_example_rows = $provenanceAudit.visible_example_rows
    runner_bundle_audit = $bundleAuditOutput
    runner_provenance_audit = $provenanceAuditOutput
    provenance_chain_sha256 = $provenanceAudit.provenance_chain_sha256
    actual_business_data_rows_written = 0
    scores_written = 0
    db_write = $false
    migration = $false
    production_deploy = $false
    final_ready = $false
} | ConvertTo-Json -Depth 8
