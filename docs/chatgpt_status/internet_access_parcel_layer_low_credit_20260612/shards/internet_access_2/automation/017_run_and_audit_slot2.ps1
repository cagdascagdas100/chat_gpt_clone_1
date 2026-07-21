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
$expectedCombinedValidation = 260
$automationRoot = Join-Path $RepoRoot "docs/chatgpt_status/internet_access_parcel_layer_low_credit_20260612/shards/internet_access_2/automation"
$webRoot = Join-Path $RepoRoot "england_map_web/data/aays_18_slots/internet_access_2"
$effectiveWorkRoot = if ($WorkRoot) { $WorkRoot } else { Join-Path $RepoRoot "outputs/internet_access_2_verified_run" }
$innerRunner = Join-Path $automationRoot "009_probe_download_slice_join_publish_slot2.ps1"
$bundleVerifier = Join-Path $automationRoot "015_verify_published_runner_bundle.py"
$bundleVerifierSelftest = Join-Path $automationRoot "016_selftest_verify_published_runner_bundle.py"
$candidateVerifier = Join-Path $automationRoot "021_verify_candidate_jsonl_integrity.py"
$candidateVerifierSelftest = Join-Path $automationRoot "022_selftest_verify_candidate_jsonl_integrity.py"
$provenanceVerifier = Join-Path $automationRoot "019_verify_single_run_provenance.py"
$provenanceVerifierSelftest = Join-Path $automationRoot "020_selftest_verify_single_run_provenance.py"
$consistencyVerifier = Join-Path $automationRoot "024_validate_review_contract_consistency.py"
$consistencyVerifierSelftest = Join-Path $automationRoot "025_selftest_validate_review_contract_consistency.py"
$consistencyAuditOutput = Join-Path $webRoot "review_contract_consistency_latest.json"
$bundleAuditOutput = Join-Path $webRoot "runner_bundle_audit_latest.json"
$provenanceAuditOutput = Join-Path $webRoot "runner_provenance_audit_latest.json"
$candidateAuditOutput = Join-Path $webRoot "candidate_jsonl_integrity_latest.json"

foreach ($required in @($innerRunner,$bundleVerifier,$bundleVerifierSelftest,$candidateVerifier,$candidateVerifierSelftest,$provenanceVerifier,$provenanceVerifierSelftest,$consistencyVerifier,$consistencyVerifierSelftest)) {
    if (-not (Test-Path -LiteralPath $required -PathType Leaf)) { throw "Required file missing: $required" }
}

$consistencySelftestRaw = & $PythonExe $consistencyVerifierSelftest
if ($LASTEXITCODE -ne 0) { throw "Review contract consistency self-test failed with exit code $LASTEXITCODE" }
$consistencySelftest = $consistencySelftestRaw | ConvertFrom-Json
if ($consistencySelftest.status -ne "PASS" -or $consistencySelftest.tests_passed -ne 14 -or $consistencySelftest.tests_total -ne 14) {
    throw "Review contract consistency self-test mismatch"
}

$consistencyAuditRaw = & $PythonExe $consistencyVerifier --repo-root $RepoRoot --audit-output $consistencyAuditOutput
if ($LASTEXITCODE -ne 0) { throw "Review contract consistency audit failed with exit code $LASTEXITCODE" }
$consistencyAudit = $consistencyAuditRaw | ConvertFrom-Json
if ($consistencyAudit.status -ne "PASS_REVIEW_CONTRACT_CONSISTENCY_AUDITED_REVIEW_ONLY" -or $consistencyAudit.combined_validation_total -ne $expectedCombinedValidation) {
    throw "Review contract consistency audit readback mismatch"
}
if ($consistencyAudit.actual_business_data_rows_written -ne 0 -or $consistencyAudit.final_ready -ne $false) {
    throw "Review contract consistency audit violated review-only truth boundary"
}

$bundleSelftestRaw = & $PythonExe $bundleVerifierSelftest
if ($LASTEXITCODE -ne 0) { throw "Published bundle verifier self-test failed with exit code $LASTEXITCODE" }
$bundleSelftest = $bundleSelftestRaw | ConvertFrom-Json
if ($bundleSelftest.status -ne "PASS" -or $bundleSelftest.tests_passed -ne 23 -or $bundleSelftest.tests_total -ne 23) {
    throw "Published bundle verifier self-test contract mismatch"
}

$provenanceSelftestRaw = & $PythonExe $provenanceVerifierSelftest
if ($LASTEXITCODE -ne 0) { throw "Single-run provenance verifier self-test failed with exit code $LASTEXITCODE" }
$provenanceSelftest = $provenanceSelftestRaw | ConvertFrom-Json
if ($provenanceSelftest.status -ne "PASS" -or $provenanceSelftest.tests_passed -ne 20 -or $provenanceSelftest.tests_total -ne 20) {
    throw "Single-run provenance verifier self-test contract mismatch"
}

$candidateSelftestRaw = & $PythonExe $candidateVerifierSelftest
if ($LASTEXITCODE -ne 0) { throw "Candidate JSONL integrity self-test failed with exit code $LASTEXITCODE" }
$candidateSelftest = $candidateSelftestRaw | ConvertFrom-Json
if ($candidateSelftest.status -ne "PASS" -or $candidateSelftest.tests_passed -ne 25 -or $candidateSelftest.tests_total -ne 25) {
    throw "Candidate JSONL integrity self-test contract mismatch"
}

$innerArgs = @("-NoProfile","-ExecutionPolicy","Bypass","-File",$innerRunner,"-RepoRoot",$RepoRoot,"-PythonExe",$PythonExe,"-WorkRoot",$effectiveWorkRoot,"-DownloadRetries",$DownloadRetries)
& powershell @innerArgs
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

$candidateRows = Join-Path $effectiveWorkRoot "candidate_outputs/internet_access_2_candidates_latest.jsonl"
$candidateManifest = Join-Path $effectiveWorkRoot "candidate_outputs/internet_access_2_extraction_manifest_latest.json"
$candidateAuditRaw = & $PythonExe $candidateVerifier --rows-jsonl $candidateRows --manifest $candidateManifest --audit-output $candidateAuditOutput
if ($LASTEXITCODE -ne 0) { throw "Candidate JSONL integrity audit failed with exit code $LASTEXITCODE" }
$candidateAudit = $candidateAuditRaw | ConvertFrom-Json
if ($candidateAudit.status -ne "PASS_COMPLETE_CANDIDATE_JSONL_INTEGRITY_REVIEW_ONLY" -or $candidateAudit.canonical_rows -ne $expectedRows) {
    throw "Candidate JSONL integrity audit readback mismatch"
}
if ($candidateAudit.actual_business_data_rows_written -ne 0 -or $candidateAudit.scores_written -ne 0 -or $candidateAudit.final_ready -ne $false) {
    throw "Candidate JSONL integrity audit violated review-only truth boundary"
}

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
    schema_version = 4
    slot_id = $slotId
    status = "COMPLETE_REAL_RUN_CONSISTENCY_CANDIDATE_BUNDLE_AND_PROVENANCE_AUDITED_REVIEW_ONLY"
    canonical_rows = $provenanceAudit.canonical_rows
    visible_example_rows = $provenanceAudit.visible_example_rows
    review_contract_consistency_audit = $consistencyAuditOutput
    combined_validation_total = $consistencyAudit.combined_validation_total
    candidate_jsonl_integrity_audit = $candidateAuditOutput
    candidate_rows_jsonl_sha256 = $candidateAudit.candidate_rows_jsonl_sha256
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
