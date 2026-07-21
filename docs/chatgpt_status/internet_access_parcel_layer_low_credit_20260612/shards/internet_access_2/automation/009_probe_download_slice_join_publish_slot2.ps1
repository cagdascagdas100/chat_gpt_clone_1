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
$officialZipUrl = "https://www.ofcom.org.uk/siteassets/resources/documents/research-and-data/multi-sector/infrastructure-research/connected-nations-spring-2026/202601_fixed_broadband_coverage_and_full_fibre_take-up-r1.zip?v=422620"
$officialV2Date = "2026-07-07"
$expectedRows = 30761
$expectedR2Count = 121
if (-not $WorkRoot) { $WorkRoot = Join-Path $RepoRoot "outputs/internet_access_2_verified_run" }

$canonicalSource = Join-Path $RepoRoot "england_map_web/data/program_layer_matrix/security.geojson"
$legacySource = Join-Path $RepoRoot "england_map_web/data/program_layer_matrix/internet.geojson"
$webRoot = Join-Path $RepoRoot "england_map_web/data/aays_18_slots/internet_access_2"
$automationRoot = Join-Path $RepoRoot "docs/chatgpt_status/internet_access_parcel_layer_low_credit_20260612/shards/internet_access_2/automation"
$extractor = Join-Path $automationRoot "002_extract_slot2_ofcom_2026_candidates.py"
$extractorSelftest = Join-Path $automationRoot "003_selftest_slot2_extractor.py"
$publisher = Join-Path $automationRoot "005_publish_slot2_readback.py"
$publisherSelftest = Join-Path $automationRoot "006_selftest_publish_slot2_readback.py"
$streamer = Join-Path $automationRoot "007_stream_extract_slot2_inputs.py"
$streamerSelftest = Join-Path $automationRoot "008_selftest_stream_extract_slot2_inputs.py"
$v2Validator = Join-Path $automationRoot "013_validate_ofcom_v2_corrections.py"
$v2ValidatorSelftest = Join-Path $automationRoot "014_selftest_validate_ofcom_v2_corrections.py"

$stageRoot = Join-Path $WorkRoot "stage"
$extractRoot = Join-Path $WorkRoot "ofcom_extract"
$sliceRoot = Join-Path $WorkRoot "slot_inputs"
$outputRoot = Join-Path $WorkRoot "candidate_outputs"
$zipPath = Join-Path $stageRoot "202601_fixed_broadband_coverage_and_full_fibre_take-up-r1.zip"
$partialZip = "$zipPath.part"
$diagnosticsPath = Join-Path $WorkRoot "internet_access_2_network_and_execution_diagnostics_latest.json"
$v2ValidationPath = Join-Path $WorkRoot "internet_access_2_ofcom_v2_validation_latest.json"

New-Item -ItemType Directory -Force -Path $WorkRoot,$stageRoot,$sliceRoot,$outputRoot,$webRoot | Out-Null
$diagnostics = [ordered]@{
    schema_version = 6
    slot_id = $slotId
    started_at = (Get-Date).ToUniversalTime().ToString("o")
    official_zip_url = $officialZipUrl
    official_outer_zip_filename = "202601_fixed_broadband_coverage_and_full_fibre_take-up-r1.zip"
    outer_zip_r1_name_is_transport_container_only = $true
    official_v2_correction_date = $officialV2Date
    official_page_display_size_mb_observations = @(32.2,32.3)
    official_page_display_size_consistency = "CONFLICTING_READBACK_METADATA_ONLY"
    official_checksum_published = $false
    package_integrity_basis = "RUNTIME_BYTE_COUNT_ZIP_SIGNATURE_SHA256_AND_INTERNAL_V2_VALIDATION"
    canonical_source = $canonicalSource
    legacy_source = $legacySource
    allowed_web_output_root = $webRoot
    dns_state = "NOT_CHECKED"
    download_state = "NOT_STARTED"
    download_attempts = @()
    zip_sha256 = $null
    zip_bytes = 0
    r2_file_count = 0
    r1_file_count = 0
    extractor_selftest = $null
    streamer_selftest = $null
    publisher_selftest = $null
    v2_validator_selftest = $null
    v2_validation_report = $null
    postcode_files_directory_validated = $false
    postcode_premise_count_fields_present = $null
    all_percentage_columns_range_validated = $false
    canonical_slice_rows = $null
    legacy_slice_rows = $null
    candidate_manifest = $null
    runner_readback = $null
    actual_business_data_rows_written = 0
    scores_written = 0
    db_write = $false
    migration = $false
    production_deploy = $false
    direct_push = $false
    final_ready = $false
}

function Save-Diagnostics([string]$state, [string]$message) {
    $diagnostics["state"] = $state
    $diagnostics["message"] = $message
    $diagnostics["updated_at"] = (Get-Date).ToUniversalTime().ToString("o")
    $diagnostics | ConvertTo-Json -Depth 14 | Set-Content -LiteralPath $diagnosticsPath -Encoding UTF8
}

function Run-JsonSelftest([string]$path, [int]$expected) {
    $raw = & $PythonExe $path
    if ($LASTEXITCODE -ne 0) { throw "Self-test failed: $path (exit $LASTEXITCODE)" }
    $result = $raw | ConvertFrom-Json
    if ($result.status -ne "PASS" -or $result.tests_passed -ne $expected -or $result.tests_total -ne $expected) {
        throw "Self-test contract mismatch: $path"
    }
    return $result
}

try {
    foreach ($required in @($canonicalSource,$legacySource,$extractor,$extractorSelftest,$publisher,$publisherSelftest,$streamer,$streamerSelftest,$v2Validator,$v2ValidatorSelftest)) {
        if (-not (Test-Path -LiteralPath $required -PathType Leaf)) { throw "Required file missing: $required" }
    }

    $diagnostics.extractor_selftest = Run-JsonSelftest $extractorSelftest 12
    $diagnostics.streamer_selftest = Run-JsonSelftest $streamerSelftest 12
    $diagnostics.publisher_selftest = Run-JsonSelftest $publisherSelftest 10
    $diagnostics.v2_validator_selftest = Run-JsonSelftest $v2ValidatorSelftest 43

    try {
        $dns = Resolve-DnsName -Name "www.ofcom.org.uk" -Type A -ErrorAction Stop
        $diagnostics.dns_state = "PASS"
        $diagnostics.dns_addresses = @($dns | Where-Object {$_.IPAddress} | ForEach-Object {$_.IPAddress})
    } catch {
        $diagnostics.dns_state = "FAIL"
        $diagnostics.dns_error = $_.Exception.Message
        Save-Diagnostics "BLOCKED_DNS" "Official source host could not be resolved. No source bytes or business data were written."
        exit 2
    }

    if (Test-Path -LiteralPath $partialZip) { Remove-Item -Force -LiteralPath $partialZip }
    $downloaded = $false
    for ($attempt = 1; $attempt -le $DownloadRetries; $attempt++) {
        $entry = [ordered]@{ attempt=$attempt; started_at=(Get-Date).ToUniversalTime().ToString("o"); state="STARTED" }
        try {
            Invoke-WebRequest -Uri $officialZipUrl -OutFile $partialZip -UseBasicParsing -TimeoutSec 600 -MaximumRedirection 8 -Headers @{"User-Agent"="AAYS-internet_access_2-verifier/8"}
            $length = (Get-Item -LiteralPath $partialZip).Length
            if ($length -lt 30000000) { throw "Downloaded ZIP is unexpectedly small: $length bytes" }
            $stream = [System.IO.File]::OpenRead($partialZip)
            try { $first = $stream.ReadByte(); $second = $stream.ReadByte() } finally { $stream.Dispose() }
            if ($first -ne 0x50 -or $second -ne 0x4B) { throw "Downloaded file does not have a ZIP signature" }
            Move-Item -Force -LiteralPath $partialZip -Destination $zipPath
            $entry.state = "PASS"; $entry.bytes = $length
            $diagnostics.download_attempts += $entry
            $downloaded = $true
            break
        } catch {
            $entry.state = "FAIL"; $entry.error = $_.Exception.Message
            $diagnostics.download_attempts += $entry
            if (Test-Path -LiteralPath $partialZip) { Remove-Item -Force -LiteralPath $partialZip }
            if ($attempt -lt $DownloadRetries) { Start-Sleep -Seconds ([Math]::Min(30, [Math]::Pow(2,$attempt))) }
        }
    }
    if (-not $downloaded) { throw "Official ZIP download failed after $DownloadRetries attempts" }

    $diagnostics.download_state = "PASS"
    $diagnostics.zip_bytes = (Get-Item -LiteralPath $zipPath).Length
    $diagnostics.zip_sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $zipPath).Hash.ToLowerInvariant()

    if (Test-Path -LiteralPath $extractRoot) { Remove-Item -Recurse -Force -LiteralPath $extractRoot }
    Expand-Archive -LiteralPath $zipPath -DestinationPath $extractRoot -Force
    $r1 = @(Get-ChildItem -Path $extractRoot -Recurse -File -Filter "202601_fixed_postcode_coverage_r1_*.csv")
    $r2 = @(Get-ChildItem -Path $extractRoot -Recurse -File -Filter "202601_fixed_postcode_coverage_r2_*.csv")
    $diagnostics.r1_file_count = $r1.Count
    $diagnostics.r2_file_count = $r2.Count
    if ($r1.Count -ne 0) { throw "Superseded all-premises r1 postcode files found: $($r1.Count)" }
    if ($r2.Count -ne $expectedR2Count) { throw "Expected $expectedR2Count corrected r2 postcode files, found $($r2.Count)" }

    $v2Raw = & $PythonExe $v2Validator --ofcom-postcode-dir $extractRoot --output $v2ValidationPath
    if ($LASTEXITCODE -ne 0) { throw "Official V2 correction and semantics validation failed with exit code $LASTEXITCODE" }
    $v2Result = $v2Raw | ConvertFrom-Json
    if (
        $v2Result.status -ne "PASS_OFFICIAL_V2_R2_CORRECTION_AND_SEMANTICS_VALIDATED" -or
        -not $v2Result.cw_not_cv_duplicate -or
        -not $v2Result.mk_not_me_duplicate -or
        -not $v2Result.postcode_files_directory_validated -or
        $v2Result.postcode_premise_count_fields_present -or
        -not $v2Result.all_percentage_columns_range_validated -or
        -not $v2Result.coverage_speed_threshold_order_validated
    ) {
        throw "Official V2 correction and semantics readback contract mismatch"
    }
    $diagnostics.v2_validation_report = $v2ValidationPath
    $diagnostics.v2_validation_status = $v2Result.status
    $diagnostics.cw_not_cv_duplicate = $v2Result.cw_not_cv_duplicate
    $diagnostics.mk_not_me_duplicate = $v2Result.mk_not_me_duplicate
    $diagnostics.postcode_files_directory_validated = $v2Result.postcode_files_directory_validated
    $diagnostics.postcode_premise_count_fields_present = $v2Result.postcode_premise_count_fields_present
    $diagnostics.all_percentage_columns_range_validated = $v2Result.all_percentage_columns_range_validated
    $diagnostics.coverage_speed_threshold_order_validated = $v2Result.coverage_speed_threshold_order_validated

    & $PythonExe $streamer --canonical $canonicalSource --legacy-internet $legacySource --output-dir $sliceRoot
    if ($LASTEXITCODE -ne 0) { throw "Streaming bounded input extraction failed with exit code $LASTEXITCODE" }
    $sliceManifestPath = Join-Path $sliceRoot "internet_access_2_stream_slice_manifest_latest.json"
    $sliceManifest = Get-Content -Raw -LiteralPath $sliceManifestPath | ConvertFrom-Json
    $diagnostics.canonical_slice_rows = $sliceManifest.canonical.rows
    $diagnostics.legacy_slice_rows = $sliceManifest.legacy_internet.rows
    if ($diagnostics.canonical_slice_rows -ne $expectedRows) { throw "Canonical bounded slice row count mismatch: $($diagnostics.canonical_slice_rows)" }

    if (Test-Path -LiteralPath $outputRoot) { Remove-Item -Recurse -Force -LiteralPath $outputRoot; New-Item -ItemType Directory -Force -Path $outputRoot | Out-Null }
    & $PythonExe $extractor --canonical (Join-Path $sliceRoot "internet_access_2_canonical_slice_latest.geojson") --legacy-internet-geojson (Join-Path $sliceRoot "internet_access_2_legacy_slice_latest.geojson") --ofcom-postcode-dir $extractRoot --output-dir $outputRoot
    if ($LASTEXITCODE -ne 0) { throw "Official r2 join failed with exit code $LASTEXITCODE" }

    $manifestPath = Join-Path $outputRoot "internet_access_2_extraction_manifest_latest.json"
    $rowsPath = Join-Path $outputRoot "internet_access_2_candidates_latest.jsonl"
    $manifest = Get-Content -Raw -LiteralPath $manifestPath | ConvertFrom-Json
    $total = $manifest.direct_current_r2_matches + $manifest.legacy_current_r2_matches_pending_spatial_qa + $manifest.no_data_rows
    if ($manifest.canonical_rows -ne $expectedRows -or $total -ne $expectedRows) { throw "Candidate manifest exact-row/status-total gate failed" }
    if ($manifest.actual_business_data_rows_written -ne 0 -or $manifest.scores_written -ne 0) { throw "Review-only output unexpectedly wrote business rows or scores" }

    $publisherRaw = & $PythonExe $publisher --manifest $manifestPath --rows-jsonl $rowsPath --output-root $webRoot
    if ($LASTEXITCODE -ne 0) { throw "Strict web readback publisher failed with exit code $LASTEXITCODE" }
    $publisherResult = $publisherRaw | ConvertFrom-Json

    $diagnostics.candidate_manifest = $manifestPath
    $diagnostics.runner_readback = Join-Path $webRoot "runner_readback_latest.json"
    $diagnostics.direct_current_r2_matches = $manifest.direct_current_r2_matches
    $diagnostics.legacy_current_r2_matches_pending_spatial_qa = $manifest.legacy_current_r2_matches_pending_spatial_qa
    $diagnostics.no_data_rows = $manifest.no_data_rows
    $diagnostics.visible_example_rows = $publisherResult.visible_example_rows
    Save-Diagnostics "COMPLETE_REVIEW_OUTPUT_READY" "Official bytes, runtime SHA-256, internal V2 payload corrections, postcode folder/level schema, percentage ranges, threshold semantics, bounded inputs, exact r2 join and strict web readback completed. The outer r1 ZIP name and conflicting displayed size labels were treated as metadata only. No migration or business write occurred."
    exit 0
} catch {
    $diagnostics.error = $_.Exception.Message
    Save-Diagnostics "BLOCKED_EXECUTION" "Execution stopped at a verified gate. No migration or business write occurred."
    exit 2
}
