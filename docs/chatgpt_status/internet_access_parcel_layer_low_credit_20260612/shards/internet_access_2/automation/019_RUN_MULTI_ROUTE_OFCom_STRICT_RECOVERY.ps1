param(
    [string]$PortableRoot = $env:AAYS_PORTABLE_ROOT,
    [string]$RepoRoot = $env:AAYS_REPO_ROOT,
    [string]$ArchivePath = ""
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

$SourceCandidates = @(
    "https://www.ofcom.org.uk/siteassets/resources/documents/research-and-data/multi-sector/infrastructure-research/connected-nations-spring-2026/202601_fixed_broadband_coverage_and_full_fibre_take-up-r1.zip?v=422620",
    "https://www.ofcom.org.uk/siteassets/resources/documents/research-and-data/multi-sector/infrastructure-research/connected-nations-spring-2026/202601_fixed_broadband_coverage_and_full_fibre_take-up-r1.zip"
)

foreach ($Source in $SourceCandidates) {
    $Uri = $null
    if (-not [System.Uri]::TryCreate($Source, [System.UriKind]::Absolute, [ref]$Uri)) {
        throw "OFFICIAL_URL_INVALID:$Source"
    }
    if ($Uri.Scheme -ne "https" -or $Uri.Host -ne $AllowedHost) {
        throw "OFFICIAL_URL_SCOPE_VIOLATION:$Source"
    }
}

$Attempts = New-Object System.Collections.Generic.List[object]
$SelectedSource = $null
$Completed = $false

foreach ($Source in $SourceCandidates) {
    if (Test-Path -LiteralPath $ArchivePath -PathType Leaf) {
        $SelectedSource = $Source
        $Completed = $true
        break
    }

    $StartedAt = (Get-Date).ToUniversalTime()
    try {
        $Output = (& $Orchestrator -PortableRoot $PortableRoot -RepoRoot $RepoRoot -ArchivePath $ArchivePath -OfficialArchiveUrl $Source | Out-String).Trim()
        $ArchiveAvailable = Test-Path -LiteralPath $ArchivePath -PathType Leaf
        $Attempts.Add([ordered]@{
            source_url = $Source
            started_at = $StartedAt.ToString('o')
            finished_at = (Get-Date).ToUniversalTime().ToString('o')
            archive_available = [bool]$ArchiveAvailable
            orchestrator_output = $Output
            duplicate_task_created = $false
            second_runner_started = $false
        })
        if ($ArchiveAvailable) {
            $SelectedSource = $Source
            $Completed = $true
            break
        }
    }
    catch {
        $Attempts.Add([ordered]@{
            source_url = $Source
            started_at = $StartedAt.ToString('o')
            finished_at = (Get-Date).ToUniversalTime().ToString('o')
            archive_available = (Test-Path -LiteralPath $ArchivePath -PathType Leaf)
            error = $_.Exception.Message
            duplicate_task_created = $false
            second_runner_started = $false
        })
        if (Test-Path -LiteralPath $ArchivePath -PathType Leaf) {
            $SelectedSource = $Source
            $Completed = $true
            break
        }
    }
}

$Result = [ordered]@{
    schema_version = 1
    generated_at = (Get-Date).ToUniversalTime().ToString('o')
    slot_id = $SlotId
    state = if ($Completed) { "MULTI_ROUTE_OFFICIAL_ARCHIVE_STRICT_RECOVERY_COMPLETE" } else { "MULTI_ROUTE_OFFICIAL_ARCHIVE_STILL_BLOCKED" }
    source_candidates = $SourceCandidates
    selected_source_url = $SelectedSource
    archive_path = $ArchivePath
    archive_available = (Test-Path -LiteralPath $ArchivePath -PathType Leaf)
    attempts = @($Attempts)
    same_task_retained = $true
    duplicate_task_created = $false
    second_runner_started = $false
    runner_started = $false
    strict_chain = "017_TO_018_TO_014"
    final_ready = $false
}

$Result | ConvertTo-Json -Depth 9
if (-not $Completed) {
    throw "MULTI_ROUTE_OFFICIAL_ARCHIVE_STILL_BLOCKED"
}
