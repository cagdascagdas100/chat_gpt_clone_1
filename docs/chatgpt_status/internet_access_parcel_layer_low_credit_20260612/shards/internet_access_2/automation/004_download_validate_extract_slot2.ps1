[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$RepoRoot,
    [string]$PythonExe = "python"
)

$ErrorActionPreference = "Stop"
$slotId = "internet_access_2"
$officialZipUrl = "https://www.ofcom.org.uk/siteassets/resources/documents/research-and-data/multi-sector/infrastructure-research/connected-nations-spring-2026/202601_fixed_broadband_coverage_and_full_fibre_take-up-r1.zip?v=422620"
$expectedR2Count = 121
$expectedRows = 30761
$canonicalPath = Join-Path $RepoRoot "england_map_web/data/program_layer_matrix/security.geojson"
$legacyPath = Join-Path $RepoRoot "england_map_web/data/program_layer_matrix/internet.geojson"
$automationRoot = Join-Path $RepoRoot "docs/chatgpt_status/internet_access_parcel_layer_low_credit_20260612/shards/internet_access_2/automation"
$extractorPath = Join-Path $automationRoot "002_extract_slot2_ofcom_2026_candidates.py"
$selftestPath = Join-Path $automationRoot "003_selftest_slot2_extractor.py"
$runtimeRoot = Join-Path $RepoRoot "docs/chatgpt_status/internet_access_parcel_layer_low_credit_20260612/shards/internet_access_2/runtime/ofcom_202601_r2"
$downloadPath = Join-Path $runtimeRoot "202601_fixed_broadband_coverage_and_full_fibre_take-up-r1.zip"
$extractRoot = Join-Path $runtimeRoot "extracted"
$outputRoot = Join-Path $runtimeRoot "candidate_output"
$proofPath = Join-Path $runtimeRoot "download_and_extract_proof_latest.json"

foreach ($required in @($canonicalPath, $legacyPath, $extractorPath, $selftestPath)) {
    if (-not (Test-Path -LiteralPath $required -PathType Leaf)) {
        throw "Required file not found: $required"
    }
}

$selftestOutput = & $PythonExe $selftestPath
if ($LASTEXITCODE -ne 0) { throw "Extractor self-test failed with exit code $LASTEXITCODE" }
$selftest = $selftestOutput | ConvertFrom-Json
if ($selftest.status -ne "PASS" -or $selftest.tests_passed -ne 12) {
    throw "Extractor self-test contract did not pass 12/12"
}

New-Item -ItemType Directory -Path $runtimeRoot -Force | Out-Null
if (-not (Test-Path -LiteralPath $downloadPath -PathType Leaf)) {
    Invoke-WebRequest -Uri $officialZipUrl -OutFile $downloadPath -UseBasicParsing
}
$zipHash = (Get-FileHash -LiteralPath $downloadPath -Algorithm SHA256).Hash.ToLowerInvariant()

if (Test-Path -LiteralPath $extractRoot) { Remove-Item -LiteralPath $extractRoot -Recurse -Force }
New-Item -ItemType Directory -Path $extractRoot -Force | Out-Null
Expand-Archive -LiteralPath $downloadPath -DestinationPath $extractRoot -Force

$r1Files = @(Get-ChildItem -LiteralPath $extractRoot -Recurse -File -Filter "202601_fixed_postcode_coverage_r1_*.csv")
$r2Files = @(Get-ChildItem -LiteralPath $extractRoot -Recurse -File -Filter "202601_fixed_postcode_coverage_r2_*.csv")
if ($r1Files.Count -ne 0) { throw "Superseded all-premises r1 postcode files found: $($r1Files.Count)" }
if ($r2Files.Count -ne $expectedR2Count) { throw "Expected $expectedR2Count corrected r2 postcode files; found $($r2Files.Count)" }

if (Test-Path -LiteralPath $outputRoot) { Remove-Item -LiteralPath $outputRoot -Recurse -Force }
New-Item -ItemType Directory -Path $outputRoot -Force | Out-Null
& $PythonExe $extractorPath `
    --canonical $canonicalPath `
    --legacy-internet-geojson $legacyPath `
    --ofcom-postcode-dir $extractRoot `
    --output-dir $outputRoot
if ($LASTEXITCODE -ne 0) { throw "Extractor failed with exit code $LASTEXITCODE" }

$manifestPath = Join-Path $outputRoot "internet_access_2_extraction_manifest_latest.json"
$manifest = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
if ($manifest.canonical_rows -ne $expectedRows) { throw "Expected $expectedRows slot rows; got $($manifest.canonical_rows)" }
$counted = $manifest.direct_current_r2_matches + $manifest.legacy_current_r2_matches_pending_spatial_qa + $manifest.no_data_rows
if ($counted -ne $expectedRows) { throw "Status counts do not sum to $expectedRows; got $counted" }
if ($manifest.actual_business_data_rows_written -ne 0) { throw "Business rows were unexpectedly written" }

$proof = [ordered]@{
    schema_version = 3
    slot_id = $slotId
    status = "OFFICIAL_ZIP_HASHED_R2_VALIDATED_SLOT2_EXTRACTED_REVIEW_ONLY"
    official_zip_url = $officialZipUrl
    downloaded_zip = $downloadPath
    downloaded_zip_sha256 = $zipHash
    corrected_r2_file_count = $r2Files.Count
    superseded_r1_file_count = $r1Files.Count
    selftest_passed = $selftest.tests_passed
    canonical_source = $canonicalPath
    legacy_internet_source = $legacyPath
    output_root = $outputRoot
    canonical_rows = $manifest.canonical_rows
    direct_current_r2_matches = $manifest.direct_current_r2_matches
    legacy_current_r2_matches_pending_spatial_qa = $manifest.legacy_current_r2_matches_pending_spatial_qa
    no_data_rows = $manifest.no_data_rows
    scores_written = 0
    actual_business_data_rows_written = 0
    db_write = $false
    migration = $false
    production_deploy = $false
    direct_push = $false
    final_ready = $false
}
$proof | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $proofPath -Encoding utf8
$proof | ConvertTo-Json -Depth 8
