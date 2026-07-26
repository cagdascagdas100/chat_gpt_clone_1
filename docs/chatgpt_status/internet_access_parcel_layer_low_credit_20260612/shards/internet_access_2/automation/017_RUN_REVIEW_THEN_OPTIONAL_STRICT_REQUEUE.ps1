param(
    [string]$PortableRoot = $env:AAYS_PORTABLE_ROOT,
    [string]$RepoRoot = $env:AAYS_REPO_ROOT,
    [string]$ArchivePath = "",
    [string]$OfficialArchiveUrl = "https://www.ofcom.org.uk/siteassets/resources/documents/research-and-data/multi-sector/infrastructure-research/connected-nations-spring-2026/202601_fixed_broadband_coverage_and_full_fibre_take-up-r1.zip?v=422620",
    [switch]$SkipDownload,
    [switch]$StartRunner
)

$ErrorActionPreference = "Stop"
$SlotId = "internet_access_2"
$ReviewWrapperRel = "docs\chatgpt_status\internet_access_parcel_layer_low_credit_20260612\shards\internet_access_2\automation\016_RUN_AND_PUBLISH_TERMINATED_IDENTITY_REVIEW.ps1"
$ZipWrapperRel = "docs\chatgpt_status\internet_access_parcel_layer_low_credit_20260612\shards\internet_access_2\automation\014_RUN_006_STRICT_REQUEUE_AFTER_OFCom_ZIP.ps1"
$DownloadWrapperRel = "docs\chatgpt_status\internet_access_parcel_layer_low_credit_20260612\shards\internet_access_2\automation\018_FETCH_OFFICIAL_OFCom_SPRING_2026_ZIP.ps1"
$ReviewOutputRel = "england_map_web\data\aays_21_slots\internet_access_2\006_existing_11013_identity_review_rows.json"
$ReviewAuditRel = "docs\chatgpt_status\internet_access_parcel_layer_low_credit_20260612\shards\internet_access_2\recovery\014_006_terminated_identity_review_export.json"

if ([string]::IsNullOrWhiteSpace($PortableRoot)) { throw "AAYS_PORTABLE_ROOT_REQUIRED" }
$PortableRoot = [System.IO.Path]::GetFullPath($PortableRoot)
if ([string]::IsNullOrWhiteSpace($RepoRoot)) {
    $RepoRoot = Join-Path $PortableRoot "runner_system\AAYS_WT\AAYS_RUNNER_HEALTHY_20260707"
}
$RepoRoot = [System.IO.Path]::GetFullPath($RepoRoot)
if (-not (Test-Path -LiteralPath $RepoRoot -PathType Container)) { throw "REPO_ROOT_NOT_FOUND:$RepoRoot" }
if ([string]::IsNullOrWhiteSpace($ArchivePath)) {
    $ArchivePath = Join-Path $PortableRoot "state\source_cache\ofcom_spring_2026\ofcom_fixed_coverage_202601_v2.zip"
}
$ArchivePath = [System.IO.Path]::GetFullPath($ArchivePath)

$ReviewWrapper = Join-Path $RepoRoot $ReviewWrapperRel
$ZipWrapper = Join-Path $RepoRoot $ZipWrapperRel
$DownloadWrapper = Join-Path $RepoRoot $DownloadWrapperRel
$ReviewOutputPath = Join-Path $RepoRoot $ReviewOutputRel
$ReviewAuditPath = Join-Path $RepoRoot $ReviewAuditRel
foreach ($Required in @($ReviewWrapper, $ZipWrapper, $DownloadWrapper)) {
    if (-not (Test-Path -LiteralPath $Required -PathType Leaf)) { throw "WRAPPER_NOT_FOUND:$Required" }
}

function Assert-ReviewOutput {
    param([string]$OutputPath, [string]$AuditPath)
    $OutputExists = Test-Path -LiteralPath $OutputPath -PathType Leaf
    $AuditExists = Test-Path -LiteralPath $AuditPath -PathType Leaf
    if ($OutputExists -xor $AuditExists) { throw "PARTIAL_REVIEW_PUBLICATION_STATE" }
    if (-not $OutputExists) { return $false }

    $Output = Get-Content -LiteralPath $OutputPath -Raw -Encoding UTF8 | ConvertFrom-Json
    $Audit = Get-Content -LiteralPath $AuditPath -Raw -Encoding UTF8 | ConvertFrom-Json
    if ($Output.state -ne "EXACT_TWO_TERMINATED_ONSPD_IDENTITIES_EXPORTED_FOR_REVIEW") { throw "EXISTING_REVIEW_OUTPUT_STATE_MISMATCH" }
    if ([int]$Output.source_total_rows -ne 11013) { throw "EXISTING_REVIEW_SOURCE_COUNT_MISMATCH" }
    if ([int]$Output.review_row_count -ne 2 -or @($Output.rows).Count -ne 2) { throw "EXISTING_REVIEW_ROW_COUNT_MISMATCH" }
    if ($Output.internet_accuracy -ne "1/4_TERMINATED_POSTCODE_REVIEW_REQUIRED") { throw "EXISTING_REVIEW_ACCURACY_MISMATCH" }
    if ([int]$Output.official_coverage_verified -ne 0) { throw "EXISTING_REVIEW_FALSE_COVERAGE" }
    foreach ($Row in @($Output.rows)) {
        if ($Row.internet_accuracy -ne "1/4") { throw "EXISTING_REVIEW_ROW_ACCURACY_MISMATCH" }
        if ([bool]$Row.official_coverage_verified) { throw "EXISTING_REVIEW_ROW_FALSE_COVERAGE" }
        if ($Row.candidate_status -ne "ONSPD_TERMINATED_REVIEW_REQUIRED") { throw "EXISTING_REVIEW_ROW_STATUS_MISMATCH" }
    }
    if ($Audit.state -ne "TERMINATED_IDENTITY_REVIEW_EXPORT_PASS") { throw "EXISTING_REVIEW_AUDIT_STATE_MISMATCH" }
    if ([int]$Audit.observed_review_rows -ne 2) { throw "EXISTING_REVIEW_AUDIT_COUNT_MISMATCH" }
    return $true
}

$ReviewWasAlreadyPublished = Assert-ReviewOutput -OutputPath $ReviewOutputPath -AuditPath $ReviewAuditPath
if (-not $ReviewWasAlreadyPublished) {
    & $ReviewWrapper -PortableRoot $PortableRoot -RepoRoot $RepoRoot
    if ($LASTEXITCODE -ne 0) { throw "REVIEW_WRAPPER_FAILED:$LASTEXITCODE" }
    if (-not (Assert-ReviewOutput -OutputPath $ReviewOutputPath -AuditPath $ReviewAuditPath)) {
        throw "REVIEW_PUBLICATION_READBACK_FAILED"
    }
}

$DownloadAttempted = $false
$DownloadSucceeded = $false
$DownloadError = $null
$DownloadResult = $null
$ArchiveAvailable = Test-Path -LiteralPath $ArchivePath -PathType Leaf
if (-not $ArchiveAvailable -and -not $SkipDownload) {
    $DownloadAttempted = $true
    try {
        $DownloadResult = (& $DownloadWrapper -PortableRoot $PortableRoot -ArchivePath $ArchivePath -SourceUrl $OfficialArchiveUrl | Out-String).Trim()
        $ArchiveAvailable = Test-Path -LiteralPath $ArchivePath -PathType Leaf
        $DownloadSucceeded = [bool]$ArchiveAvailable
        if (-not $ArchiveAvailable) { $DownloadError = "DOWNLOAD_WRAPPER_RETURNED_WITHOUT_ARCHIVE" }
    }
    catch {
        $DownloadError = $_.Exception.Message
        $ArchiveAvailable = Test-Path -LiteralPath $ArchivePath -PathType Leaf
        $DownloadSucceeded = [bool]$ArchiveAvailable
    }
}

if (-not $ArchiveAvailable) {
    [ordered]@{
        state = "TERMINATED_REVIEW_READY_OFFICIAL_ZIP_PENDING"
        slot_id = $SlotId
        review_already_published = [bool]$ReviewWasAlreadyPublished
        review_rows = 2
        review_accuracy = "1/4_ONLY"
        official_coverage_verified = 0
        archive_path = $ArchivePath
        archive_available = $false
        official_archive_url_configured = -not [string]::IsNullOrWhiteSpace($OfficialArchiveUrl)
        download_skipped = [bool]$SkipDownload
        download_attempted = [bool]$DownloadAttempted
        download_succeeded = [bool]$DownloadSucceeded
        download_error = $DownloadError
        download_result = $DownloadResult
        existing_task_requeued = $false
        runner_started = $false
        duplicate_task_created = $false
        second_runner_started = $false
        final_ready = $false
    } | ConvertTo-Json -Depth 7
    return
}

if ($StartRunner) {
    & $ZipWrapper -PortableRoot $PortableRoot -RepoRoot $RepoRoot -ArchivePath $ArchivePath -StartRunner
} else {
    & $ZipWrapper -PortableRoot $PortableRoot -RepoRoot $RepoRoot -ArchivePath $ArchivePath
}
if ($LASTEXITCODE -ne 0) { throw "STRICT_REQUEUE_WRAPPER_FAILED:$LASTEXITCODE" }

[ordered]@{
    state = "TERMINATED_REVIEW_READY_AND_STRICT_006_REQUEUE_COMPLETE"
    slot_id = $SlotId
    review_already_published = [bool]$ReviewWasAlreadyPublished
    review_rows = 2
    review_accuracy = "1/4_ONLY"
    archive_path = $ArchivePath
    archive_available = $true
    download_attempted = [bool]$DownloadAttempted
    download_succeeded = [bool]$DownloadSucceeded
    strict_archive_preflight_required = $true
    existing_task_requeued = $true
    runner_start_requested = [bool]$StartRunner
    duplicate_task_created = $false
    second_runner_started = $false
    final_ready = $false
} | ConvertTo-Json -Depth 6
