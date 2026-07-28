param(
    [string]$PortableRoot = $env:AAYS_PORTABLE_ROOT,
    [string]$ArchivePath = "",
    [string]$SourceUrl = "https://www.ofcom.org.uk/siteassets/resources/documents/research-and-data/multi-sector/infrastructure-research/connected-nations-spring-2026/202601_fixed_broadband_coverage_and_full_fibre_take-up-r1.zip?v=422620",
    [string]$LandingUrl = "https://www.ofcom.org.uk/phones-and-broadband/coverage-and-speeds/connected-nations-update-spring-2026",
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

function Invoke-CurlOfficialDownload {
    param(
        [Parameter(Mandatory=$true)][string]$CurlExe,
        [Parameter(Mandatory=$true)][string]$Destination,
        [Parameter(Mandatory=$true)][string]$CookiePath,
        [Parameter(Mandatory=$true)][string]$LandingTempPath,
        [Parameter(Mandatory=$true)][System.Collections.Generic.List[string]]$Errors
    )

    $VersionText = ""
    try { $VersionText = (& $CurlExe -V 2>&1 | Out-String).Trim() } catch { $VersionText = $_.Exception.Message }
    $UsesSchannel = $VersionText -match '(?i)Schannel'
    $TlsArgs = @()
    if ($UsesSchannel) { $TlsArgs += '--ssl-no-revoke' }

    $CommonArgs = @(
        '--fail',
        '--location',
        '--silent',
        '--show-error',
        '--http1.1',
        '--compressed',
        '--connect-timeout', '30',
        '--max-time', '300',
        '--retry', ([string][Math]::Max(1, $RetryCount)),
        '--retry-delay', '2',
        '--retry-all-errors',
        '--user-agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 AAYS-Ofcom-Strict-Fetch/2.0',
        '--header', 'Accept: application/zip,application/octet-stream,text/html;q=0.9,*/*;q=0.8'
    )

    $LandingAttempted = $false
    $LandingSucceeded = $false
    if (-not [string]::IsNullOrWhiteSpace($LandingUrl)) {
        $LandingAttempted = $true
        try {
            $LandingArgs = @($CommonArgs + $TlsArgs + @(
                '--cookie-jar', $CookiePath,
                '--output', $LandingTempPath,
                $LandingUrl
            ))
            & $CurlExe @LandingArgs
            if ($LASTEXITCODE -eq 0) {
                $LandingSucceeded = $true
            } else {
                $Errors.Add("curl landing exit $LASTEXITCODE")
            }
        }
        catch {
            $Errors.Add("curl landing: $($_.Exception.Message)")
        }
        finally {
            if (Test-Path -LiteralPath $LandingTempPath -PathType Leaf) {
                Remove-Item -LiteralPath $LandingTempPath -Force
            }
        }
    }

    try {
        $CookieArgs = @('--cookie-jar', $CookiePath)
        if (Test-Path -LiteralPath $CookiePath -PathType Leaf) {
            $CookieArgs = @('--cookie', $CookiePath, '--cookie-jar', $CookiePath)
        }
        $DownloadArgs = @($CommonArgs + $TlsArgs + $CookieArgs + @(
            '--referer', $LandingUrl,
            '--output', $Destination,
            $SourceUrl
        ))
        & $CurlExe @DownloadArgs
        $ExitCode = $LASTEXITCODE
        if ($ExitCode -ne 0) {
            $Errors.Add("curl download exit $ExitCode")
            if (Test-Path -LiteralPath $Destination -PathType Leaf) {
                Remove-Item -LiteralPath $Destination -Force
            }
            return [ordered]@{
                succeeded = $false
                curl_version = $VersionText
                curl_uses_schannel = [bool]$UsesSchannel
                ssl_no_revoke_used = [bool]$UsesSchannel
                landing_attempted = [bool]$LandingAttempted
                landing_succeeded = [bool]$LandingSucceeded
            }
        }

        return [ordered]@{
            succeeded = Test-Path -LiteralPath $Destination -PathType Leaf
            curl_version = $VersionText
            curl_uses_schannel = [bool]$UsesSchannel
            ssl_no_revoke_used = [bool]$UsesSchannel
            landing_attempted = [bool]$LandingAttempted
            landing_succeeded = [bool]$LandingSucceeded
        }
    }
    catch {
        $Errors.Add("curl download: $($_.Exception.Message)")
        if (Test-Path -LiteralPath $Destination -PathType Leaf) {
            Remove-Item -LiteralPath $Destination -Force
        }
        return [ordered]@{
            succeeded = $false
            curl_version = $VersionText
            curl_uses_schannel = [bool]$UsesSchannel
            ssl_no_revoke_used = [bool]$UsesSchannel
            landing_attempted = [bool]$LandingAttempted
            landing_succeeded = [bool]$LandingSucceeded
        }
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
        landing_url = $LandingUrl
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
$CookiePath = "$ArchivePath.cookies.$([guid]::NewGuid().ToString('N')).txt"
$LandingTempPath = "$ArchivePath.landing.$([guid]::NewGuid().ToString('N')).html"
$DownloadErrors = New-Object System.Collections.Generic.List[string]
$Downloaded = $false
$DownloadTransport = $null
$CurlResult = $null

for ($Attempt = 1; $Attempt -le [Math]::Max(1, $RetryCount); $Attempt++) {
    try {
        Invoke-WebRequest -Uri $SourceUrl -OutFile $TempPath -UseBasicParsing -TimeoutSec 300 -Headers @{
            'User-Agent' = 'AAYS-Ofcom-Strict-Fetch/2.0'
            'Accept' = 'application/zip,application/octet-stream,*/*'
            'Referer' = $LandingUrl
        }
        $Downloaded = $true
        $DownloadTransport = "Invoke-WebRequest"
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
            $DownloadTransport = "BITS"
        }
        catch {
            $DownloadErrors.Add("BITS: $($_.Exception.Message)")
            if (Test-Path -LiteralPath $TempPath -PathType Leaf) { Remove-Item -LiteralPath $TempPath -Force }
        }
    }
}

if (-not $Downloaded) {
    $CurlCommand = Get-Command curl.exe -ErrorAction SilentlyContinue
    if ($CurlCommand) {
        $CurlResult = Invoke-CurlOfficialDownload -CurlExe $CurlCommand.Source -Destination $TempPath -CookiePath $CookiePath -LandingTempPath $LandingTempPath -Errors $DownloadErrors
        $Downloaded = [bool]$CurlResult.succeeded
        if ($Downloaded) { $DownloadTransport = "curl" }
    } else {
        $DownloadErrors.Add("curl.exe not found")
    }
}

if (Test-Path -LiteralPath $CookiePath -PathType Leaf) {
    Remove-Item -LiteralPath $CookiePath -Force
}
if (Test-Path -LiteralPath $LandingTempPath -PathType Leaf) {
    Remove-Item -LiteralPath $LandingTempPath -Force
}

if (-not $Downloaded -or -not (Test-Path -LiteralPath $TempPath -PathType Leaf)) {
    $Failure = [ordered]@{
        state = "OFFICIAL_ARCHIVE_DOWNLOAD_BLOCKED"
        slot_id = $SlotId
        source_url = $SourceUrl
        landing_url = $LandingUrl
        expected_outer_filename = $ExpectedOuterFile
        archive_path = $ArchivePath
        archive_available = $false
        download_performed = $false
        download_transport = $DownloadTransport
        download_errors = @($DownloadErrors)
        curl = $CurlResult
        required_inner_revision = $RequiredInnerRevision
        duplicate_task_created = $false
        second_runner_started = $false
        final_ready = $false
    }
    $Failure | ConvertTo-Json -Depth 7
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
    schema_version = 2
    generated_at = (Get-Date).ToUniversalTime().ToString('o')
    state = "OFFICIAL_ARCHIVE_DOWNLOADED_ENVELOPE_PASS_STRICT_INNER_VALIDATION_PENDING"
    slot_id = $SlotId
    source_url = $SourceUrl
    landing_url = $LandingUrl
    expected_outer_filename = $ExpectedOuterFile
    archive_path = $ArchivePath
    archive_available = $true
    download_performed = $true
    download_transport = $DownloadTransport
    download_errors = @($DownloadErrors)
    curl = $CurlResult
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
$Audit | ConvertTo-Json -Depth 7 | Set-Content -LiteralPath $AuditPath -Encoding UTF8
$Audit | ConvertTo-Json -Depth 7
