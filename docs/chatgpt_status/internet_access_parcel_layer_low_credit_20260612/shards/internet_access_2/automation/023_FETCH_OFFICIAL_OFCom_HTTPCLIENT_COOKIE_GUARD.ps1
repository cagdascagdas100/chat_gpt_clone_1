param(
    [string]$PortableRoot = $env:AAYS_PORTABLE_ROOT,
    [string]$ArchivePath = "",
    [string]$SourceUrl = "https://www.ofcom.org.uk/siteassets/resources/documents/research-and-data/multi-sector/infrastructure-research/connected-nations-spring-2026/202601_fixed_broadband_coverage_and_full_fibre_take-up-r1.zip?v=422620",
    [string]$LandingUrl = "https://www.ofcom.org.uk/phones-and-broadband/coverage-and-speeds/connected-nations-update-spring-2026",
    [int64]$MinimumBytes = 30000000,
    [int64]$MaximumBytes = 100000000,
    [int]$RetryCount = 2
)

$ErrorActionPreference = "Stop"
$SlotId = "internet_access_2"
$AllowedHost = "www.ofcom.org.uk"
$ExpectedOuterFile = "202601_fixed_broadband_coverage_and_full_fibre_take-up-r1.zip"
$RequiredInnerRevision = "r2"
$LegacyDownloader = Join-Path $PSScriptRoot "018_FETCH_OFFICIAL_OFCom_SPRING_2026_ZIP.ps1"

if ([string]::IsNullOrWhiteSpace($PortableRoot)) { throw "AAYS_PORTABLE_ROOT_REQUIRED" }
$PortableRoot = [System.IO.Path]::GetFullPath($PortableRoot)
if ([string]::IsNullOrWhiteSpace($ArchivePath)) {
    $ArchivePath = Join-Path $PortableRoot "state\source_cache\ofcom_spring_2026\ofcom_fixed_coverage_202601_v2.zip"
}
$ArchivePath = [System.IO.Path]::GetFullPath($ArchivePath)
if ($RetryCount -lt 1 -or $RetryCount -gt 4) { throw "RETRY_COUNT_OUT_OF_RANGE" }
if ($MinimumBytes -lt 1000000 -or $MaximumBytes -le $MinimumBytes) { throw "ARCHIVE_SIZE_RANGE_INVALID" }
if (-not (Test-Path -LiteralPath $LegacyDownloader -PathType Leaf)) { throw "LEGACY_DOWNLOADER_NOT_FOUND:$LegacyDownloader" }

$ValidatedUris = @{}
foreach ($Pair in @(@("source", $SourceUrl), @("landing", $LandingUrl))) {
    $Name = [string]$Pair[0]
    $Value = [string]$Pair[1]
    $Uri = $null
    if (-not [System.Uri]::TryCreate($Value, [System.UriKind]::Absolute, [ref]$Uri)) {
        throw "OFFICIAL_${Name}_URL_INVALID:$Value"
    }
    if ($Uri.Scheme -ne "https" -or $Uri.Host -ne $AllowedHost) {
        throw "OFFICIAL_${Name}_URL_SCOPE_VIOLATION:$Value"
    }
    $ValidatedUris[$Name] = $Uri
}

$ArchiveDirectory = Split-Path -Parent $ArchivePath
if (-not (Test-Path -LiteralPath $ArchiveDirectory -PathType Container)) {
    New-Item -ItemType Directory -Path $ArchiveDirectory -Force | Out-Null
}

Add-Type -AssemblyName System.IO.Compression.FileSystem
Add-Type -AssemblyName System.Net.Http
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
        if ($R2EntryCount -lt 1) { throw "ARCHIVE_HAS_NO_R2_NAMED_ENTRY" }
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

function Invoke-HttpClientCookieDownload {
    param(
        [Parameter(Mandatory=$true)][string]$Destination,
        [Parameter(Mandatory=$true)][System.Collections.Generic.List[string]]$Errors
    )

    $Handler = $null
    $Client = $null
    $LandingResponse = $null
    $DownloadRequest = $null
    $DownloadResponse = $null
    $FileStream = $null
    try {
        $Handler = New-Object System.Net.Http.HttpClientHandler
        $Handler.AllowAutoRedirect = $true
        $Handler.UseCookies = $true
        $Handler.CookieContainer = New-Object System.Net.CookieContainer
        $Handler.AutomaticDecompression = [System.Net.DecompressionMethods]::GZip -bor [System.Net.DecompressionMethods]::Deflate

        $Client = New-Object System.Net.Http.HttpClient($Handler)
        $Client.Timeout = [TimeSpan]::FromSeconds(300)
        $Client.DefaultRequestHeaders.UserAgent.ParseAdd("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AAYS-Ofcom-Strict-Fetch/3.0")
        [void]$Client.DefaultRequestHeaders.TryAddWithoutValidation("Accept-Language", "en-GB,en;q=0.9,cy;q=0.7")

        $LandingResponse = $Client.GetAsync($ValidatedUris["landing"], [System.Net.Http.HttpCompletionOption]::ResponseHeadersRead).GetAwaiter().GetResult()
        if (-not $LandingResponse.IsSuccessStatusCode) {
            throw "HTTPCLIENT_LANDING_STATUS:$([int]$LandingResponse.StatusCode)"
        }
        $LandingFinalUri = $LandingResponse.RequestMessage.RequestUri
        if (-not $LandingFinalUri -or $LandingFinalUri.Scheme -ne "https" -or $LandingFinalUri.Host -ne $AllowedHost) {
            throw "HTTPCLIENT_LANDING_REDIRECT_SCOPE_VIOLATION:$LandingFinalUri"
        }
        $LandingResponse.Dispose()
        $LandingResponse = $null

        $DownloadRequest = New-Object System.Net.Http.HttpRequestMessage([System.Net.Http.HttpMethod]::Get, $ValidatedUris["source"])
        $DownloadRequest.Headers.Referrer = $ValidatedUris["landing"]
        [void]$DownloadRequest.Headers.TryAddWithoutValidation("Accept", "application/zip,application/octet-stream,*/*")
        $DownloadResponse = $Client.SendAsync($DownloadRequest, [System.Net.Http.HttpCompletionOption]::ResponseHeadersRead).GetAwaiter().GetResult()
        if (-not $DownloadResponse.IsSuccessStatusCode) {
            throw "HTTPCLIENT_DOWNLOAD_STATUS:$([int]$DownloadResponse.StatusCode)"
        }
        $DownloadFinalUri = $DownloadResponse.RequestMessage.RequestUri
        if (-not $DownloadFinalUri -or $DownloadFinalUri.Scheme -ne "https" -or $DownloadFinalUri.Host -ne $AllowedHost) {
            throw "HTTPCLIENT_DOWNLOAD_REDIRECT_SCOPE_VIOLATION:$DownloadFinalUri"
        }

        $FileStream = New-Object System.IO.FileStream($Destination, [System.IO.FileMode]::CreateNew, [System.IO.FileAccess]::Write, [System.IO.FileShare]::None)
        $DownloadResponse.Content.CopyToAsync($FileStream).GetAwaiter().GetResult()
        $FileStream.Flush($true)
        $FileStream.Dispose()
        $FileStream = $null

        return [ordered]@{
            succeeded = (Test-Path -LiteralPath $Destination -PathType Leaf)
            landing_status = [int]200
            landing_final_uri = [string]$LandingFinalUri
            download_status = [int]$DownloadResponse.StatusCode
            download_final_uri = [string]$DownloadFinalUri
            cookies_observed = @($Handler.CookieContainer.GetCookies($ValidatedUris["landing"])).Count
        }
    }
    catch {
        $Errors.Add("HttpClientCookie: $($_.Exception.Message)")
        if (Test-Path -LiteralPath $Destination -PathType Leaf) {
            Remove-Item -LiteralPath $Destination -Force
        }
        return [ordered]@{
            succeeded = $false
            error = $_.Exception.Message
        }
    }
    finally {
        if ($FileStream) { $FileStream.Dispose() }
        if ($DownloadResponse) { $DownloadResponse.Dispose() }
        if ($DownloadRequest) { $DownloadRequest.Dispose() }
        if ($LandingResponse) { $LandingResponse.Dispose() }
        if ($Client) { $Client.Dispose() }
        if ($Handler) { $Handler.Dispose() }
    }
}

if (Test-Path -LiteralPath $ArchivePath -PathType Leaf) {
    & $LegacyDownloader -PortableRoot $PortableRoot -ArchivePath $ArchivePath -SourceUrl $SourceUrl -LandingUrl $LandingUrl -MinimumBytes $MinimumBytes -MaximumBytes $MaximumBytes -RetryCount $RetryCount
    if ($LASTEXITCODE -ne 0) { throw "EXISTING_ARCHIVE_LEGACY_VALIDATION_FAILED:$LASTEXITCODE" }
    return
}

$TempPath = "$ArchivePath.httpcookie.partial.$([guid]::NewGuid().ToString('N'))"
$Errors = New-Object System.Collections.Generic.List[string]
$HttpResult = $null
$Validation = $null

for ($Attempt = 1; $Attempt -le $RetryCount; $Attempt++) {
    $HttpResult = Invoke-HttpClientCookieDownload -Destination $TempPath -Errors $Errors
    if ([bool]$HttpResult.succeeded) { break }
    if ($Attempt -lt $RetryCount) { Start-Sleep -Seconds ([Math]::Min(8, [Math]::Pow(2, $Attempt))) }
}

if ($HttpResult -and [bool]$HttpResult.succeeded) {
    try {
        $Validation = Test-ZipEnvelope -Path $TempPath
        if (Test-Path -LiteralPath $ArchivePath -PathType Leaf) { throw "ARCHIVE_TARGET_RACE_DETECTED" }
        [System.IO.File]::Move($TempPath, $ArchivePath)

        $Audit = [ordered]@{
            schema_version = 1
            generated_at = (Get-Date).ToUniversalTime().ToString('o')
            state = "OFFICIAL_ARCHIVE_HTTPCLIENT_COOKIE_DOWNLOADED_ENVELOPE_PASS_STRICT_INNER_VALIDATION_PENDING"
            slot_id = $SlotId
            source_url = $SourceUrl
            landing_url = $LandingUrl
            expected_outer_filename = $ExpectedOuterFile
            required_inner_revision = $RequiredInnerRevision
            archive_path = $ArchivePath
            archive_available = $true
            download_transport = "HttpClientCookieSession"
            http = $HttpResult
            bytes = $Validation.bytes
            entry_count = $Validation.entry_count
            r2_named_entry_count = $Validation.r2_named_entry_count
            sha256 = $Validation.sha256
            strict_inner_validation_deferred_to_014 = $true
            duplicate_task_created = $false
            second_runner_started = $false
            final_ready = $false
        }
        $AuditPath = "$ArchivePath.httpcookie.download.json"
        $Audit | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $AuditPath -Encoding UTF8
        $Audit | ConvertTo-Json -Depth 8
        return
    }
    catch {
        if (Test-Path -LiteralPath $TempPath -PathType Leaf) {
            $Stamp = (Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssZ')
            Move-Item -LiteralPath $TempPath -Destination "$TempPath.failed.$Stamp" -Force
        }
        throw
    }
}

$LegacyOutput = $null
try {
    $LegacyOutput = (& $LegacyDownloader -PortableRoot $PortableRoot -ArchivePath $ArchivePath -SourceUrl $SourceUrl -LandingUrl $LandingUrl -MinimumBytes $MinimumBytes -MaximumBytes $MaximumBytes -RetryCount $RetryCount | Out-String).Trim()
    if ($LASTEXITCODE -ne 0) { throw "LEGACY_DOWNLOADER_NONZERO:$LASTEXITCODE" }
    if (-not (Test-Path -LiteralPath $ArchivePath -PathType Leaf)) { throw "LEGACY_DOWNLOADER_RETURNED_WITHOUT_ARCHIVE" }

    [ordered]@{
        schema_version = 1
        generated_at = (Get-Date).ToUniversalTime().ToString('o')
        state = "HTTPCLIENT_COOKIE_ROUTE_FAILED_LEGACY_OFFICIAL_ROUTE_SUCCEEDED"
        slot_id = $SlotId
        source_url = $SourceUrl
        landing_url = $LandingUrl
        httpclient_errors = @($Errors)
        legacy_output = $LegacyOutput
        archive_path = $ArchivePath
        archive_available = $true
        same_task_retained = $true
        duplicate_task_created = $false
        second_runner_started = $false
        final_ready = $false
    } | ConvertTo-Json -Depth 8
}
catch {
    throw "ALL_OFFICIAL_DOWNLOAD_ROUTES_BLOCKED:httpclient=$([string]::Join(' | ', @($Errors))) legacy=$($_.Exception.Message)"
}
