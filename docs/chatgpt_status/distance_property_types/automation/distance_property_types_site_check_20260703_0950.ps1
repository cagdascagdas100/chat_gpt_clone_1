$ErrorActionPreference = 'Stop'

$TaskId = 'distance_property_types_site_check_20260703_0950'
$PageKey = 'distance_property_types'

$RepoRoot = $env:AAYS_REPO_ROOT
if ([string]::IsNullOrWhiteSpace($RepoRoot)) { $RepoRoot = $env:AAYS_REPAIR_REPO_ROOT }
if ([string]::IsNullOrWhiteSpace($RepoRoot)) { $RepoRoot = (Get-Location).Path }

function Join-RepoPath {
    param([Parameter(Mandatory=$true)][string]$RelativePath)
    $normalized = $RelativePath -replace '/', [System.IO.Path]::DirectorySeparatorChar
    return Join-Path $RepoRoot $normalized
}

function Count-DataRows {
    param([Parameter(Mandatory=$true)][string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) { return 0 }
    $lines = @(Get-Content -LiteralPath $Path -ErrorAction Stop | Where-Object { -not [string]::IsNullOrWhiteSpace($_) })
    if ($lines.Count -le 1) { return 0 }
    return [Math]::Max(0, $lines.Count - 1)
}

$dirs = @(
    'docs/chatgpt_status/distance_property_types/runner_outputs',
    'docs/chatgpt_status/distance_property_types/reports',
    'docs/chatgpt_status/distance_property_types/blocked',
    'docs/chatgpt_status/distance_property_types/status'
)
foreach ($dir in $dirs) {
    New-Item -ItemType Directory -Force -Path (Join-RepoPath $dir) | Out-Null
}

$inputRel = 'docs/chatgpt_status/distance_property_types/inputs/distance_property_types_source_candidates.csv'
$verifiedCsvRel = 'england_map_web/data/distance_property_types/distance_property_types_verified.csv'
$verifiedGeojsonRel = 'england_map_web/data/distance_property_types/distance_property_types_verified.geojson'
$manifestRel = 'england_map_web/data/distance_property_types/distance_property_types_evidence_manifest.json'
$manualReviewRel = 'docs/chatgpt_status/distance_property_types/reports/distance_property_types_manual_review_latest.csv'

$inputPath = Join-RepoPath $inputRel
$verifiedCsvPath = Join-RepoPath $verifiedCsvRel
$verifiedGeojsonPath = Join-RepoPath $verifiedGeojsonRel
$manifestPath = Join-RepoPath $manifestRel
$manualReviewPath = Join-RepoPath $manualReviewRel

$inputExists = Test-Path -LiteralPath $inputPath
$verifiedCsvExists = Test-Path -LiteralPath $verifiedCsvPath
$verifiedGeojsonExists = Test-Path -LiteralPath $verifiedGeojsonPath
$manifestExists = Test-Path -LiteralPath $manifestPath
$manualReviewExists = Test-Path -LiteralPath $manualReviewPath

$evidenceRows = Count-DataRows -Path $inputPath
$verifiedRows = Count-DataRows -Path $verifiedCsvPath

$blockers = New-Object System.Collections.Generic.List[string]
if (-not $inputExists) { $blockers.Add("missing_input_file:$inputRel") }
if ($evidenceRows -le 0) { $blockers.Add('missing_real_evidence_rows') }
if (-not $verifiedCsvExists) { $blockers.Add("missing_output:$verifiedCsvRel") }
if (-not $verifiedGeojsonExists) { $blockers.Add("missing_output:$verifiedGeojsonRel") }
if (-not $manifestExists) { $blockers.Add("missing_output:$manifestRel") }
if (-not $manualReviewExists) { $blockers.Add("missing_output:$manualReviewRel") }

$status = if ($blockers.Count -gt 0) { 'blocked' } else { 'site_check_passed_waiting_final_review' }
$completionPercent = if ($evidenceRows -le 0) { 35 } elseif ($blockers.Count -gt 0) { 70 } else { 90 }
$remainingPercent = 100 - $completionPercent
$now = (Get-Date).ToUniversalTime().ToString('o')

$report = [ordered]@{
    task_id = $TaskId
    page_key = $PageKey
    generated_at = $now
    status = $status
    final_ready = $false
    product_final_ready = $false
    fake_data = $false
    db_write = $false
    ddl = $false
    migration = $false
    production_deploy = $false
    evidence_rows = $evidenceRows
    verified_csv_rows = $verifiedRows
    checked_paths = [ordered]@{
        input = $inputRel
        verified_csv = $verifiedCsvRel
        verified_geojson = $verifiedGeojsonRel
        evidence_manifest = $manifestRel
        manual_review_csv = $manualReviewRel
    }
    blockers = @($blockers)
    completion_percent = $completionPercent
    remaining_percent = $remainingPercent
}

$reportRel = 'docs/chatgpt_status/distance_property_types/runner_outputs/distance_property_types_site_check_20260703_0950.report.json'
$reportPath = Join-RepoPath $reportRel
$report | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $reportPath -Encoding UTF8

$progressRel = 'docs/chatgpt_status/distance_property_types/reports/distance_property_types_progress_latest.md'
$progressPath = Join-RepoPath $progressRel
$progress = @(
    '# Distance Property Types runner progress',
    '',
    "task_id=$TaskId",
    "checked_at=$now",
    "status=$status",
    'final_ready=false',
    'product_final_ready=false',
    "evidence_rows=$evidenceRows",
    "verified_csv_rows=$verifiedRows",
    "completion_percent=$completionPercent",
    "remaining_percent=$remainingPercent",
    "blockers=$($blockers -join ';')",
    '',
    'No fake evidence was generated.'
)
$progress | Set-Content -LiteralPath $progressPath -Encoding UTF8

if ($blockers.Count -gt 0) {
    $blockedRel = 'docs/chatgpt_status/distance_property_types/blocked/distance_property_types_site_check_20260703_0950.blocked.json'
    $blockedPath = Join-RepoPath $blockedRel
    $blocked = [ordered]@{
        page_key = $PageKey
        task_id = $TaskId
        checked_at = $now
        status = 'blocked'
        final_ready = $false
        product_final_ready = $false
        completion_percent = $completionPercent
        remaining_percent = $remainingPercent
        blockers = @($blockers)
        safety = [ordered]@{
            fake_completed_written = $false
            fake_heartbeat_written = $false
            fake_final_ready_written = $false
            fake_percent_100_written = $false
            fake_data = $false
            db_write = $false
            ddl = $false
            migration = $false
            production_deploy = $false
        }
        next_action = 'Provide real evidence-backed source candidates, then process with the single shared runner after the shared runtime blocker is fixed.'
    }
    $blocked | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $blockedPath -Encoding UTF8
}

Write-Output "DISTANCE_PROPERTY_TYPES_SITE_CHECK_STATUS=$status"
Write-Output "DISTANCE_PROPERTY_TYPES_EVIDENCE_ROWS=$evidenceRows"
Write-Output "DISTANCE_PROPERTY_TYPES_FINAL_READY=false"
