param(
    [string]$PortableRoot = $env:AAYS_PORTABLE_ROOT,
    [string]$ArchivePath = "",
    [string]$SourceUrl = "https://www.ofcom.org.uk/siteassets/resources/documents/research-and-data/multi-sector/infrastructure-research/connected-nations-spring-2026/202601_fixed_broadband_coverage_and_full_fibre_take-up-r1.zip?v=422620",
    [int64]$MinimumBytes = 30000000,
    [int64]$MaximumBytes = 100000000,
    [int]$RetryCount = 3
)

$ErrorActionPreference = "Stop"
$SlotId = "internet_access_2"
$ExpectedOuterFile = "202601_fixed_broadband_coverage_and_full_fibre_take-up-r1.zip"
$RequiredInnerRevision = "r2"

if ([string]::IsNullOrWhiteSpace($PortableRoot)) { throw "AAYS_PORTABLE_ROOT_REQUIRED" }
$PortableRoot = [System.IO.Path]::GetFullPath($PortableRoot)
if ([string]::IsNullOrWhiteSpace($ArchivePath)) {
    $ArchivePath = Join-Path $PortableRoot "state\source_cache\ofcom_spring_2026\ofcom_fixed_coverage_202601_v2.zip"
}
$ArchivePath = [System.IO.Path]::GetFullPath($ArchivePath)
$ArchiveDirectory = Split-Path -Parent $ArchivePath
if (-not (Test-Path -LiteralPath $ArchiveDirectory -PathType Container)) {
    New-Item -ItemType Directory -Path $ArchiveDirectory -Force | Out-Null
}

Add-Type -AssemblyName System.IO.Compression.FileSystem
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

function Test-ZipEnvelope {
    param([Parameter(Mandatory=$true)][string]$Path)
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { return $null }
    $Item = Get-Item -LiteralPath $Path
    if ($Item.Length -lt $MinimumBytes) { throw "ARCHIVE_TOO_SMALL:$($Item.Length)" }
    if ($Item.Length -gt $MaximumBytes) { throw "ARCHIVE_TOO_LARGE:$($Item.Length)" }
    $Zip = $null
    try {
        $Zip = [System.IO.Compression.ZipFile]::OpenRead($Path)
        $EntryCount = @($Zip.Entries).Count
        if ($EntryCount -lt 1) { throw "ARCHIVE_HAS_NO_ENTRIES" }
        $R2EntryCount = @($Zip.Entries | Where-Object { $_.FullName -match '(?i)(^|[/\\_-])r2([/\\_.-]|$)' }).Count
        return [ordered]@{
            bytes = [int64]$Item.Length
            entry_count = [int]$EntryCount
            r2_named_entry_count = [int]$R2EntryCount
            sha256 = (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
        }
    }
    finally {
        if ($Zip) { $Zip.Dispose() }
    }
}

$ExistingValidation = $null
if (Test-Path -LiteralPath $ArchivePath -PathType Leaf) {
    try {
        $ExistingValidation = Test-ZipEnvelope -Path $ArchivePath
    }
    catch {
        $Stamp = (Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssZ')
        $QuarantinePath = "$ArchivePath.invalid.$Stamp"
        Move-Item -LiteralPath $ArchivePath -Destination $QuarantinePath -Force
        $ExistingValidation = $null
    }
}

if ($ExistingValidation) {
    [ordered]@{
        state = "OFFICIAL_ARCHIVE_ALREADY_PRESENT_ENVELOPE_PASS"
        slot_id = $SlotId
        source_url = $SourceUrl
        expected_outer_filename = $ExpectedOuterFile
        archive_path = $ArchivePath
        archive_available = $true
        download_performed = $false
        bytes = $ExistingValidation.bytes
        entry_count = $ExistingValidation.entry_count
        r2_named_entry_count = $ExistingValidation.r2_named_entry_count
        sha256 = $ExistingValidation.sha256
        required_inner_revision = $RequiredInnerRevision
        strict_inner_validation_deferred_to_014 = $true
        final_ready = $false
    } | ConvertTo-Json -Depth 5
    return
}

$TempPath = "$ArchivePath.partial.$([guid]::NewGuid().ToString('N'))"
$DownloadErrors = New-Object System.Collections.Generic.List[string]
$Downloaded = $false

for ($Attempt = 1; $Attempt -le [Math]::Max(1, $RetryCount); $Attempt++) {
    try {
        Invoke-WebRequest -Uri $SourceUrl -OutFile $TempPath -UseBasicParsing -TimeoutSec 300 -Headers @{ 'User-Agent' = 'AAYS-Ofcom-Strict-Fetch/1.0' }
        $Downloaded = $true
        break
    }
    catch {
        $DownloadErrors.Add("InvokeWebRequest attempt $Attempt: $($_.Exception.Message)")
        if (Test-Path -LiteralPath $TempPath -PathType Leaf) { Remove-Item -LiteralPath $TempPath -Force }
        if ($Attempt -lt $RetryCount) { Start-Sleep -Seconds ([Math]::Min(8, [Math]::Pow(2, $Attempt))) }
    }
}

if (-not $Downloaded) {
    $Bits = Get-Command Start-BitsTransfer -ErrorAction SilentlyContinue
    if ($Bits) {
        try {
            Start-BitsTransfer -Source $SourceUrl -Destination $TempPath -TransferType Download -Priority Foreground -ErrorAction Stop
            $Downloaded = $true
        }
        catch {
            $DownloadErrors.Add("BITS: $($_.Exception.Message)")
            if (Test-Path -LiteralPath $TempPath -PathType Leaf) { Remove-Item -LiteralPath $TempPath -Force }
        }
    }
}

if (-not $Downloaded -or -not (Test-Path -LiteralPath $TempPath -PathType Leaf)) {
    $Failure = [ordered]@{
        state = "OFFICIAL_ARCHIVE_DOWNLOAD_BLOCKED"
        slot_id = $SlotId
        source_url = $SourceUrl
        expected_outer_filename = $ExpectedOuterFile
        archive_path = $ArchivePath
        archive_available = $false
        download_performed = $false
        download_errors = @($DownloadErrors)
        required_inner_revision = $RequiredInnerRevision
        duplicate_task_created = $false
        second_runner_started = $false
        final_ready = $false
    }
    $Failure | ConvertTo-Json -Depth 6
    throw "OFFICIAL_ARCHIVE_DOWNLOAD_BLOCKED:$([string]::Join(' | ', @($DownloadErrors)))"
}

$Validation = $null
try {
    $Validation = Test-ZipEnvelope -Path $TempPath
    if (Test-Path -LiteralPath $ArchivePath -PathType Leaf) { throw "ARCHIVE_TARGET_RACE_DETECTED" }
    [System.IO.File]::Move($TempPath, $ArchivePath)
}
catch {
    if (Test-Path -LiteralPath $TempPath -PathType Leaf) {
        $Stamp = (Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssZ')
        Move-Item -LiteralPath $TempPath -Destination "$TempPath.failed.$Stamp" -Force
    }
    throw
}

$AuditPath = "$ArchivePath.download.json"
$Audit = [ordered]@{
    schema_version = 1
    generated_at = (Get-Date).ToUniversalTime().ToString('o')
    state = "OFFICIAL_ARCHIVE_DOWNLOADED_ENVELOPE_PASS_STRICT_INNER_VALIDATION_PENDING"
    slot_id = $SlotId
    source_url = $SourceUrl
    expected_outer_filename = $ExpectedOuterFile
    archive_path = $ArchivePath
    archive_available = $true
    download_performed = $true
    bytes = $Validation.bytes
    entry_count = $Validation.entry_count
    r2_named_entry_count = $Validation.r2_named_entry_count
    sha256 = $Validation.sha256
    required_inner_revision = $RequiredInnerRevision
    strict_inner_validation_deferred_to_014 = $true
    duplicate_task_created = $false
    second_runner_started = $false
    final_ready = $false
}
$Audit | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $AuditPath -Encoding UTF8
$Audit | ConvertTo-Json -Depth 6
