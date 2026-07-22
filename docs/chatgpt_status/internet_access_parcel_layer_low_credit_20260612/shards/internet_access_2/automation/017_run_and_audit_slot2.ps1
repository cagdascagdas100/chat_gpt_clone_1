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
$expectedCombinedValidation = 415
$automationRoot = Join-Path $RepoRoot "docs/chatgpt_status/internet_access_parcel_layer_low_credit_20260612/shards/internet_access_2/automation"
$webRoot = Join-Path $RepoRoot "england_map_web/data/aays_18_slots/internet_access_2"
$effectiveWorkRoot = if ($WorkRoot) { $WorkRoot } else { Join-Path $RepoRoot "outputs/internet_access_2_verified_run" }

$innerRunner = Join-Path $automationRoot "036_run_coverage_aware_inner_carrier.ps1"
$innerRunnerSelftest = Join-Path $automationRoot "037_selftest_run_coverage_aware_inner_carrier_contract.py"
$coverageExtractorSelftest = Join-Path $automationRoot "031_selftest_extract_slot2_coverage_aware_candidates.py"
$coverageResolutionVerifier = Join-Path $automationRoot "032_validate_coverage_aware_postcode_resolution.py"
$coverageResolutionSelftest = Join-Path $automationRoot "033_selftest_validate_coverage_aware_postcode_resolution.py"
$basePostcodeResolutionSelftest = Join-Path $automationRoot "029_selftest_validate_candidate_postcode_resolution.py"
$bundleVerifier = Join-Path $automationRoot "015_verify_published_runner_bundle.py"
$bundleVerifierSelftest = Join-Path $automationRoot "016_selftest_verify_published_runner_bundle.py"
$candidateVerifier = Join-Path $automationRoot "021_verify_candidate_jsonl_integrity.py"
$candidateVerifierSelftest = Join-Path $automationRoot "022_selftest_verify_candidate_jsonl_integrity.py"
$baseProvenanceSelftest = Join-Path $automationRoot "020_selftest_verify_single_run_provenance.py"
$extendedProvenanceVerifier = Join-Path $automationRoot "034_verify_extended_single_run_provenance.py"
$extendedProvenanceSelftest = Join-Path $automationRoot "035_selftest_verify_extended_single_run_provenance.py"
$consistencyVerifier = Join-Path $automationRoot "024_validate_review_contract_consistency.py"
$consistencyVerifierSelftest = Join-Path $automationRoot "025_selftest_validate_review_contract_consistency.py"

$consistencyAuditOutput = Join-Path $webRoot "review_contract_consistency_latest.json"
$bundleAuditOutput = Join-Path $webRoot "runner_bundle_audit_latest.json"
$provenanceAuditOutput = Join-Path $webRoot "runner_provenance_audit_latest.json"
$candidateAuditOutput = Join-Path $webRoot "candidate_jsonl_integrity_latest.json"
$postcodeResolutionAuditOutput = Join-Path $webRoot "candidate_postcode_resolution_latest.json"

foreach ($required in @(
    $innerRunner,$innerRunnerSelftest,$coverageExtractorSelftest,$coverageResolutionVerifier,$coverageResolutionSelftest,
    $basePostcodeResolutionSelftest,$bundleVerifier,$bundleVerifierSelftest,$candidateVerifier,$candidateVerifierSelftest,
    $baseProvenanceSelftest,$extendedProvenanceVerifier,$extendedProvenanceSelftest,
    $consistencyVerifier,$consistencyVerifierSelftest
)) {
    if (-not (Test-Path -LiteralPath $required -PathType Leaf)) { throw "Required file missing: $required" }
}

function Run-JsonSelftest([string]$Path, [int]$Expected, [string]$Label) {
    $raw = & $PythonExe $Path
    if ($LASTEXITCODE -ne 0) { throw "$Label self-test failed with exit code $LASTEXITCODE" }
    $result = $raw | ConvertFrom-Json
    if ($result.status -ne "PASS" -or $result.tests_passed -ne $Expected -or $result.tests_total -ne $Expected) {
        throw "$Label self-test contract mismatch"
    }
    return $result
}

$consistencySelftest = Run-JsonSelftest $consistencyVerifierSelftest 15 "Review contract consistency"
$consistencyAuditRaw = & $PythonExe $consistencyVerifier --repo-root $RepoRoot --audit-output $consistencyAuditOutput
if ($LASTEXITCODE -ne 0) { throw "Review contract consistency audit failed with exit code $LASTEXITCODE" }
$consistencyAudit = $consistencyAuditRaw | ConvertFrom-Json
if ($consistencyAudit.status -ne "PASS_REVIEW_CONTRACT_CONSISTENCY_AUDITED_REVIEW_ONLY" -or $consistencyAudit.combined_validation_total -ne $expectedCombinedValidation -or $consistencyAudit.provenance_chain_artifact_count -ne 20) {
    throw "Review contract consistency audit readback mismatch"
}
if ($consistencyAudit.actual_business_data_rows_written -ne 0 -or $consistencyAudit.final_ready -ne $false) {
    throw "Review contract consistency audit violated review-only truth boundary"
}

$bundleSelftest = Run-JsonSelftest $bundleVerifierSelftest 23 "Published bundle verifier"
$candidateSelftest = Run-JsonSelftest $candidateVerifierSelftest 25 "Candidate JSONL integrity"
$basePostcodeResolutionSelftestResult = Run-JsonSelftest $basePostcodeResolutionSelftest 18 "Base postcode resolution"
$coverageExtractorSelftestResult = Run-JsonSelftest $coverageExtractorSelftest 20 "Coverage-aware extractor"
$coverageResolutionSelftestResult = Run-JsonSelftest $coverageResolutionSelftest 24 "Coverage-aware postcode resolution"
$baseProvenanceSelftestResult = Run-JsonSelftest $baseProvenanceSelftest 24 "Base single-run provenance"
$extendedProvenanceSelftestResult = Run-JsonSelftest $extendedProvenanceSelftest 24 "Extended single-run provenance and execution-code identity"
$innerRunnerSelftestResult = Run-JsonSelftest $innerRunnerSelftest 16 "Coverage-aware inner carrier"

$innerArgs = @("-NoProfile","-ExecutionPolicy","Bypass","-File",$innerRunner,"-RepoRoot",$RepoRoot,"-PythonExe",$PythonExe,"-WorkRoot",$effectiveWorkRoot,"-DownloadRetries",$DownloadRetries)
& powershell @innerArgs
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

$candidateRows = Join-Path $effectiveWorkRoot "candidate_outputs/internet_access_2_candidates_latest.jsonl"
$candidateManifest = Join-Path $effectiveWorkRoot "candidate_outputs/internet_access_2_extraction_manifest_latest.json"
$carrierOutput = Join-Path $effectiveWorkRoot "internet_access_2_coverage_aware_carrier_latest.json"
foreach ($requiredOutput in @($candidateRows,$candidateManifest,$carrierOutput)) {
    if (-not (Test-Path -LiteralPath $requiredOutput -PathType Leaf)) { throw "Required real-run output missing: $requiredOutput" }
}

$postcodeResolutionAuditRaw = & $PythonExe $coverageResolutionVerifier --rows-jsonl $candidateRows --audit-output $postcodeResolutionAuditOutput
if ($LASTEXITCODE -ne 0) { throw "Coverage-aware postcode resolution audit failed with exit code $LASTEXITCODE" }
$postcodeResolutionAudit = $postcodeResolutionAuditRaw | ConvertFrom-Json
if ($postcodeResolutionAudit.status -ne "PASS_COVERAGE_AWARE_POSTCODE_RESOLUTION_AUDITED_REVIEW_ONLY" -or $postcodeResolutionAudit.canonical_rows -ne $expectedRows) { throw "Coverage-aware postcode resolution audit readback mismatch" }
if ($postcodeResolutionAudit.actual_business_data_rows_written -ne 0 -or $postcodeResolutionAudit.scores_written -ne 0 -or $postcodeResolutionAudit.final_ready -ne $false) { throw "Coverage-aware postcode resolution audit violated review-only truth boundary" }

$candidateAuditRaw = & $PythonExe $candidateVerifier --rows-jsonl $candidateRows --manifest $candidateManifest --audit-output $candidateAuditOutput
if ($LASTEXITCODE -ne 0) { throw "Candidate JSONL integrity audit failed with exit code $LASTEXITCODE" }
$candidateAudit = $candidateAuditRaw | ConvertFrom-Json
if ($candidateAudit.status -ne "PASS_COMPLETE_CANDIDATE_JSONL_INTEGRITY_REVIEW_ONLY" -or $candidateAudit.canonical_rows -ne $expectedRows) { throw "Candidate JSONL integrity audit readback mismatch" }
if ($candidateAudit.actual_business_data_rows_written -ne 0 -or $candidateAudit.scores_written -ne 0 -or $candidateAudit.final_ready -ne $false) { throw "Candidate JSONL integrity audit violated review-only truth boundary" }

$bundleAuditRaw = & $PythonExe $bundleVerifier --output-root $webRoot --audit-output $bundleAuditOutput
if ($LASTEXITCODE -ne 0) { throw "Published runner bundle audit failed with exit code $LASTEXITCODE" }
$bundleAudit = $bundleAuditRaw | ConvertFrom-Json
if ($bundleAudit.status -ne "PASS_REAL_RUN_WEB_BUNDLE_AUDITED_REVIEW_ONLY" -or $bundleAudit.canonical_rows -ne $expectedRows) { throw "Published runner bundle audit readback mismatch" }
if ($bundleAudit.actual_business_data_rows_written -ne 0 -or $bundleAudit.scores_written -ne 0 -or $bundleAudit.final_ready -ne $false) { throw "Published runner bundle audit violated review-only truth boundary" }

$provenanceAuditRaw = & $PythonExe $extendedProvenanceVerifier --work-root $effectiveWorkRoot --web-root $webRoot --audit-output $provenanceAuditOutput
if ($LASTEXITCODE -ne 0) { throw "Extended single-run provenance audit failed with exit code $LASTEXITCODE" }
$provenanceAudit = $provenanceAuditRaw | ConvertFrom-Json
if (
    $provenanceAudit.status -ne "PASS_EXTENDED_SINGLE_RUN_PROVENANCE_CHAIN_AUDITED_REVIEW_ONLY" -or
    $provenanceAudit.canonical_rows -ne $expectedRows -or
    $provenanceAudit.provenance_artifact_count -ne 20 -or
    $provenanceAudit.execution_code_artifact_count -ne 4 -or
    $provenanceAudit.runtime_exact_extractor_substitution_verified -ne $true -or
    $provenanceAudit.combined_validation_total -ne $expectedCombinedValidation
) { throw "Extended single-run provenance audit readback mismatch" }
if ($provenanceAudit.actual_business_data_rows_written -ne 0 -or $provenanceAudit.scores_written -ne 0 -or $provenanceAudit.final_ready -ne $false) { throw "Extended single-run provenance audit violated review-only truth boundary" }

[ordered]@{
    schema_version = 8
    slot_id = $slotId
    status = "COMPLETE_REAL_RUN_COVERAGE_AWARE_POSTCODE_CANDIDATE_BUNDLE_EXECUTION_CODE_AND_EXTENDED_PROVENANCE_AUDITED_REVIEW_ONLY"
    canonical_rows = $provenanceAudit.canonical_rows
    visible_example_rows = $provenanceAudit.visible_example_rows
    review_contract_consistency_audit = $consistencyAuditOutput
    combined_validation_total = $consistencyAudit.combined_validation_total
    coverage_aware_inner_carrier = $carrierOutput
    candidate_postcode_resolution_audit = $postcodeResolutionAuditOutput
    legacy_current_r2_rows = $postcodeResolutionAudit.legacy_current_r2_rows
    coverage_fallback_from_canonical_rows = $postcodeResolutionAudit.coverage_fallback_from_canonical_rows
    canonical_legacy_conflict_rows = $postcodeResolutionAudit.canonical_legacy_conflict_rows
    invalid_postcode_candidate_rows = $postcodeResolutionAudit.invalid_postcode_candidate_rows
    selected_postcode_not_in_current_r2_rows = $postcodeResolutionAudit.selected_postcode_not_in_current_r2_rows
    candidate_jsonl_integrity_audit = $candidateAuditOutput
    candidate_rows_jsonl_sha256 = $candidateAudit.candidate_rows_jsonl_sha256
    runner_bundle_audit = $bundleAuditOutput
    runner_provenance_audit = $provenanceAuditOutput
    provenance_artifact_count = $provenanceAudit.provenance_artifact_count
    execution_code_artifact_count = $provenanceAudit.execution_code_artifact_count
    base_runner_code_sha256 = $provenanceAudit.base_runner_code_sha256
    runtime_runner_code_sha256 = $provenanceAudit.runtime_runner_code_sha256
    coverage_aware_extractor_code_sha256 = $provenanceAudit.coverage_aware_extractor_code_sha256
    coverage_aware_carrier_code_sha256 = $provenanceAudit.coverage_aware_carrier_code_sha256
    runtime_exact_extractor_substitution_verified = $provenanceAudit.runtime_exact_extractor_substitution_verified
    zip_container_audit_sha256 = $provenanceAudit.zip_container_audit_sha256
    provenance_chain_sha256 = $provenanceAudit.provenance_chain_sha256
    actual_business_data_rows_written = 0
    scores_written = 0
    db_write = $false
    migration = $false
    production_deploy = $false
    final_ready = $false
} | ConvertTo-Json -Depth 8
