$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$slotId = if ($env:AAYS_SLOT_ID) { [string]$env:AAYS_SLOT_ID } else { 'security_public_safety_3' }
$taskId = if ($env:AAYS_TASK_ID) { [string]$env:AAYS_TASK_ID } else { 'security-public-safety-3-resume-9147406c4a5f' }
$continuationKey = '9147406c4a5fb6fbd06910dddf2b38c200878a801d5bb0907aaf395f6170d1da'
if ($slotId -ne 'security_public_safety_3') { Write-Error "SLOT_ID_MISMATCH:$slotId"; exit 2 }

$repoRoot = (& git rev-parse --show-toplevel 2>$null).Trim()
if (-not $repoRoot) { Write-Error 'REPO_ROOT_UNAVAILABLE'; exit 2 }

$innerWorker = Join-Path $repoRoot 'docs/chatgpt_status/aays1/shards/security_public_safety_3/runtime_browser_acceptance_worker.ps1'
$statusPath = Join-Path $repoRoot 'docs/chatgpt_status/aays1/shards/security_public_safety_3/status/runtime_browser_acceptance_latest.json'
$operationPath = Join-Path $repoRoot 'england_map_web/data/aays_21_slots/security_public_safety_3/runtime_browser_acceptance_latest.json'
if (-not (Test-Path -LiteralPath $innerWorker)) { Write-Error 'INNER_WORKER_NOT_FOUND'; exit 2 }

& $innerWorker
$innerExitCode = [int]$LASTEXITCODE
if (-not (Test-Path -LiteralPath $statusPath)) { Write-Error 'INNER_STATUS_NOT_CREATED'; exit 2 }

$status = Get-Content -LiteralPath $statusPath -Raw -Encoding UTF8 | ConvertFrom-Json
$renderedTableRows = 0
if ($null -ne $status.browser_dom_evidence -and $null -ne $status.browser_dom_evidence.renderedTableRows) {
    $renderedTableRows = [int]$status.browser_dom_evidence.renderedTableRows
}

$blockers = [Collections.Generic.List[string]]::new()
foreach ($item in @($status.blockers)) {
    if ($item -and -not $blockers.Contains([string]$item)) { $blockers.Add([string]$item) }
}
if ($renderedTableRows -ne 300) {
    $blocker = "BROWSER_RENDERED_TABLE_ROW_COUNT_MISMATCH:$renderedTableRows/300"
    if (-not $blockers.Contains($blocker)) { $blockers.Add($blocker) }
}

$pass = ($innerExitCode -eq 0 -and [bool]$status.acceptance_pass -and $renderedTableRows -eq 300 -and $blockers.Count -eq 0)
$status.acceptance_pass = [bool]$pass
$status.status = if ($pass) { 'RUNTIME_BROWSER_ACCEPTANCE_VERIFIED' } else { 'RUNTIME_BROWSER_ACCEPTANCE_BLOCKED' }
$status.blockers = @($blockers)
$status | Add-Member -NotePropertyName rendered_table_row_count -NotePropertyValue $renderedTableRows -Force
$status | Add-Member -NotePropertyName required_rendered_table_row_count -NotePropertyValue 300 -Force
$status | Add-Member -NotePropertyName rendered_table_contract_pass -NotePropertyValue ($renderedTableRows -eq 300) -Force
$status | Add-Member -NotePropertyName inner_worker_exit_code -NotePropertyValue $innerExitCode -Force
$status | Add-Member -NotePropertyName worker_contract_version -NotePropertyValue 'v2_state_and_rendered_rows' -Force
$status | Add-Member -NotePropertyName final_ready -NotePropertyValue $false -Force
[IO.File]::WriteAllText($statusPath, (($status | ConvertTo-Json -Depth 80) + "`n"), [Text.UTF8Encoding]::new($false))

if (Test-Path -LiteralPath $operationPath) {
    $operation = Get-Content -LiteralPath $operationPath -Raw -Encoding UTF8 | ConvertFrom-Json
    $entry = @($operation.operations) | Select-Object -First 1
    if ($null -ne $entry) {
        $entry | Add-Member -NotePropertyName rendered_table_row_count -NotePropertyValue $renderedTableRows -Force
        $entry | Add-Member -NotePropertyName required_rendered_table_row_count -NotePropertyValue 300 -Force
        $entry | Add-Member -NotePropertyName rendered_table_contract_pass -NotePropertyValue ($renderedTableRows -eq 300) -Force
        $entry | Add-Member -NotePropertyName worker_contract_version -NotePropertyValue 'v2_state_and_rendered_rows' -Force
        if (-not $pass) {
            $entry.status = 'blocked'
            $entry.confidence_score = 0
            $entry.result = 'RUNTIME_BROWSER_ACCEPTANCE_BLOCKED'
            $entry.needs_manual_review = $true
        }
    }
    [IO.File]::WriteAllText($operationPath, (($operation | ConvertTo-Json -Depth 80) + "`n"), [Text.UTF8Encoding]::new($false))
}

if ($pass) { exit 0 } else { exit 1 }
