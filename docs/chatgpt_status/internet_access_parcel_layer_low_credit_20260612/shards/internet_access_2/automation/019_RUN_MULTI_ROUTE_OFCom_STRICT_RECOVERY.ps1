param(
    [string]$PortableRoot = $env:AAYS_PORTABLE_ROOT,
    [string]$RepoRoot = $env:AAYS_REPO_ROOT,
    [string]$ArchivePath = "",
    [switch]$StartRunner
)

$ErrorActionPreference = "Stop"
$SlotId = "internet_access_2"
$AllowedHost = "www.ofcom.org.uk"
$Orchestrator = Join-Path $PSScriptRoot "017_RUN_REVIEW_THEN_OPTIONAL_STRICT_REQUEUE.ps1"

if ([string]::IsNullOrWhiteSpace($PortableRoot)) { throw "AAYS_PORTABLE_ROOT_REQUIRED" }
$PortableRoot = [System.IO.Path]::GetFullPath($PortableRoot)
if ([string]::IsNullOrWhiteSpace($RepoRoot)) {
    $RepoRoot = Join-Path $PortableRoot "runner_system\AAYS_WT\AAYS_RUNNER_HEALTHY_20260707"
}
$RepoRoot = [System.IO.Path]::GetFullPath($RepoRoot)
if ([string]::IsNullOrWhiteSpace($ArchivePath)) {
    $ArchivePath = Join-Path $PortableRoot "state\source_cache\ofcom_spring_2026\ofcom_fixed_coverage_202601_v2.zip"
}
$ArchivePath = [System.IO.Path]::GetFullPath($ArchivePath)

if (-not (Test-Path -LiteralPath $Orchestrator -PathType Leaf)) {
    throw "ORCHESTRATOR_017_NOT_FOUND:$Orchestrator"
}
if (-not (Test-Path -LiteralPath $RepoRoot -PathType Container)) {
    throw "REPO_ROOT_NOT_FOUND:$RepoRoot"
}

$ArchiveUrls = @(
    "https://www.ofcom.org.uk/siteassets/resources/documents/research-and-data/multi-sector/infrastructure-research/connected-nations-spring-2026/202601_fixed_broadband_coverage_and_full_fibre_take-up-r1.zip?v=422620",
    "https://www.ofcom.org.uk/siteassets/resources/documents/research-and-data/multi-sector/infrastructure-research/connected-nations-spring-2026/202601_fixed_broadband_coverage_and_full_fibre_take-up-r1.zip"
)
$LandingUrls = @(
    "https://www.ofcom.org.uk/phones-and-broadband/coverage-and-speeds/connected-nations-update-spring-2026",
    "https://www.ofcom.org.uk/cy/phones-and-broadband/coverage-and-speeds/connected-nations-update-spring-2026"
)

$SourceRoutes = New-Object System.Collections.Generic.List[object]
foreach ($ArchiveUrl in $ArchiveUrls) {
    foreach ($LandingUrl in $LandingUrls) {
        $SourceRoutes.Add([ordered]@{
            archive_url = $ArchiveUrl
            landing_url = $LandingUrl
            landing_language = if ($LandingUrl -match "/cy/") { "cy" } else { "en" }
        })
    }
}

foreach ($Route in @($SourceRoutes)) {
    foreach ($OfficialUrl in @([string]$Route.archive_url, [string]$Route.landing_url)) {
        $Uri = $null
        if (-not [System.Uri]::TryCreate($OfficialUrl, [System.UriKind]::Absolute, [ref]$Uri)) {
            throw "OFFICIAL_URL_INVALID:$OfficialUrl"
        }
        if ($Uri.Scheme -ne "https" -or $Uri.Host -ne $AllowedHost) {
            throw "OFFICIAL_URL_SCOPE_VIOLATION:$OfficialUrl"
        }
    }
}

$Attempts = New-Object System.Collections.Generic.List[object]
$SelectedRoute = $null
$Completed = $false
$RunnerRequested = [bool]$StartRunner

foreach ($Route in @($SourceRoutes)) {
    $ArchiveUrl = [string]$Route.archive_url
    $LandingUrl = [string]$Route.landing_url
    $StartedAt = (Get-Date).ToUniversalTime()
    try {
        if ($StartRunner) {
            $Output = (& $Orchestrator -PortableRoot $PortableRoot -RepoRoot $RepoRoot -ArchivePath $ArchivePath -OfficialArchiveUrl $ArchiveUrl -OfficialLandingUrl $LandingUrl -StartRunner | Out-String).Trim()
        } else {
            $Output = (& $Orchestrator -PortableRoot $PortableRoot -RepoRoot $RepoRoot -ArchivePath $ArchivePath -OfficialArchiveUrl $ArchiveUrl -OfficialLandingUrl $LandingUrl | Out-String).Trim()
        }
        $ArchiveAvailable = Test-Path -LiteralPath $ArchivePath -PathType Leaf
        $Attempts.Add([ordered]@{
            archive_url = $ArchiveUrl
            landing_url = $LandingUrl
            landing_language = [string]$Route.landing_language
            started_at = $StartedAt.ToString('o')
            finished_at = (Get-Date).ToUniversalTime().ToString('o')
            archive_available = [bool]$ArchiveAvailable
            orchestrator_output = $Output
            runner_start_requested = $RunnerRequested
            duplicate_task_created = $false
            second_runner_started = $false
        })
        if ($ArchiveAvailable) {
            $SelectedRoute = $Route
            $Completed = $true
            break
        }
    }
    catch {
        $Attempts.Add([ordered]@{
            archive_url = $ArchiveUrl
            landing_url = $LandingUrl
            landing_language = [string]$Route.landing_language
            started_at = $StartedAt.ToString('o')
            finished_at = (Get-Date).ToUniversalTime().ToString('o')
            archive_available = (Test-Path -LiteralPath $ArchivePath -PathType Leaf)
            error = $_.Exception.Message
            runner_start_requested = $RunnerRequested
            duplicate_task_created = $false
            second_runner_started = $false
        })
        if (Test-Path -LiteralPath $ArchivePath -PathType Leaf) {
            throw "STRICT_CHAIN_FAILED_WITH_ARCHIVE_PRESENT:$($_.Exception.Message)"
        }
    }
}

$Result = [ordered]@{
    schema_version = 3
    generated_at = (Get-Date).ToUniversalTime().ToString('o')
    slot_id = $SlotId
    state = if ($Completed) { "MULTI_ROUTE_OFFICIAL_ARCHIVE_STRICT_RECOVERY_COMPLETE" } else { "MULTI_ROUTE_OFFICIAL_ARCHIVE_STILL_BLOCKED" }
    archive_urls = $ArchiveUrls
    landing_urls = $LandingUrls
    source_routes = @($SourceRoutes)
    selected_archive_url = if ($SelectedRoute) { [string]$SelectedRoute.archive_url } else { $null }
    selected_landing_url = if ($SelectedRoute) { [string]$SelectedRoute.landing_url } else { $null }
    selected_landing_language = if ($SelectedRoute) { [string]$SelectedRoute.landing_language } else { $null }
    archive_path = $ArchivePath
    archive_available = (Test-Path -LiteralPath $ArchivePath -PathType Leaf)
    attempts = @($Attempts)
    same_task_retained = $true
    duplicate_task_created = $false
    second_runner_started = $false
    runner_start_requested = $RunnerRequested
    runner_start_guarded_by_014_lease_checks = $true
    strict_chain = "017_TO_018_TO_014"
    final_ready = $false
}

$Result | ConvertTo-Json -Depth 9
if (-not $Completed) {
    throw "MULTI_ROUTE_OFFICIAL_ARCHIVE_STILL_BLOCKED"
}
