[CmdletBinding()]
param(
    [string]$RepoRoot = $env:AAYS_REPO_ROOT,
    [string]$ResultPath
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

if ([string]::IsNullOrWhiteSpace($RepoRoot)) {
    $RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..\..\..\..')).Path
}
$RepoRoot = (Resolve-Path -LiteralPath $RepoRoot).Path.TrimEnd('\')
if ([string]::IsNullOrWhiteSpace($ResultPath)) {
    $ResultPath = Join-Path $PSScriptRoot '012_gas_emissions_3_100_browser_acceptance_local_result_latest.json'
}

$summaryPath = Join-Path $RepoRoot 'england_map_web\data\aays_18_slots\gas_emissions_3\summary_latest.json'
$statusPath = Join-Path $RepoRoot 'england_map_web\data\aays_18_slots\gas_emissions_3\browser_acceptance_runner_status_latest.json'
$checkpointPath = Join-Path $RepoRoot 'docs\chatgpt_status\_shared\slots_21\gas_emissions_3\checkpoint_latest.json'

function Read-Json([string]$Path) {
    if (-not (Test-Path -LiteralPath $Path)) { throw "Required JSON not found: $Path" }
    return (Get-Content -Raw -LiteralPath $Path | ConvertFrom-Json)
}

function Write-Json($Value, [string]$Path) {
    $json = $Value | ConvertTo-Json -Depth 32
    [IO.File]::WriteAllText($Path, $json, [Text.UTF8Encoding]::new($false))
}

$result = Read-Json $ResultPath
if ($result.slot_id -ne 'gas_emissions_3') { throw "Unexpected slot_id in browser proof: $($result.slot_id)" }
if ($result.browser_dom_passed -ne $true) { throw 'Browser DOM proof is not PASS.' }
if ($result.browser_acceptance_passed -ne $true) { throw 'Remote browser proof readback is not PASS.' }
if ($result.git.proof_remote_readback_passed -ne $true) { throw 'Browser proof commit remote readback is not PASS.' }

$summary = Read-Json $summaryPath
$checkpoint = Read-Json $checkpointPath
$runnerStatus = Read-Json $statusPath
if ($summary.slot_id -ne 'gas_emissions_3' -or $checkpoint.slot_id -ne 'gas_emissions_3') {
    throw 'Summary or checkpoint slot mismatch.'
}

$now = [DateTime]::UtcNow.ToString('o')
$nextCompleted = [int]$checkpoint.operations_completed + 1
$nextTotal = [int]$checkpoint.operations_total + 1
$nextProgress = [Math]::Round((100.0 * $nextCompleted / $nextTotal), 2)
$increase = [Math]::Round($nextProgress - [double]$checkpoint.shard_progress_percent, 2)

$summary.updated_at = $now
$summary.status = 'BROWSER_100_ACCEPTANCE_PASS_PARCEL_BINDING_BLOCKED'
$summary.metrics.operations_completed = $nextCompleted
$summary.metrics.operations_total = $nextTotal
$summary.metrics.shard_progress_percent = $nextProgress
$summary.metrics.progress_increase_points = $increase
$summary.metrics.browser_verified_rows = 100
$summary.metrics.browser_acceptance_percent = 100
$summary.metrics.browser_remaining_rows = 0
$summary.acceptance.last_proven_dom_rows = 100
$summary.acceptance.remaining_dom_rows = 0
$summary.acceptance.passed = $true
$summary.browser_runner.executed = $true
$summary.browser_runner.browser_dom_passed = $true
$summary.browser_runner.browser_acceptance_passed = $true
$summary.remaining_operation = 'REAL_PARCEL_BINDING_EVIDENCE'
$summary.blocker = 'PARCEL_BINDING_GATE_FALSE; OFFICIAL_REAL_GEOMETRY_AND_PARCEL_BINDING_EVIDENCE_REQUIRED'
$summary.final_ready = $false
$summary.fake_data = $false
$summary.db_write = $false
$summary.migration = $false
$summary.production_deploy = $false

$completedSteps = @($checkpoint.completed_steps)
if ($completedSteps -notcontains '100_OF_100_BROWSER_ACCEPTANCE') {
    $completedSteps += '100_OF_100_BROWSER_ACCEPTANCE'
}
$checkpoint.sequence = [int]$checkpoint.sequence + 1
$checkpoint.task_id = 'aays1-gas-emissions-3-browser-100-proof-readback-then-parcel-binding-20260721'
$checkpoint.completed_steps = $completedSteps
$checkpoint.first_unverified_step = 'REAL_PARCEL_BINDING_EVIDENCE'
$checkpoint.blocker = 'PARCEL_BINDING_GATE_FALSE; OFFICIAL_REAL_GEOMETRY_AND_PARCEL_BINDING_EVIDENCE_REQUIRED'
$checkpoint.acceptance_request_last_proven_dom_rows = 100
$checkpoint.acceptance_request_remaining_dom_rows = 0
$checkpoint.browser_acceptance_runner_executed = $true
$checkpoint.browser_verified_rows = 100
$checkpoint.operations_completed = $nextCompleted
$checkpoint.operations_total = $nextTotal
$checkpoint.shard_progress_percent = $nextProgress
$checkpoint.progress_increase_points = $increase
$checkpoint.updated_at = $now
$checkpoint.final_ready = $false
$checkpoint.fake_data = $false
$checkpoint.db_write = $false
$checkpoint.migration = $false
$checkpoint.production_deploy = $false

$runnerStatus.status = 'BROWSER_100_ACCEPTANCE_PASS_REMOTE_PROOF_READBACK'
$runnerStatus.updated_at = $now
$runnerStatus.core_runner_executed = $true
$runnerStatus.publisher_executed = $true
$runnerStatus.browser_dom_passed = $true
$runnerStatus.browser_acceptance_passed = $true
$runnerStatus.parcel_binding_gate_passed = $false
$runnerStatus.final_ready = $false

Write-Json $summary $summaryPath
Write-Json $checkpoint $checkpointPath
Write-Json $runnerStatus $statusPath

Write-Output "POST_BROWSER_FINALIZER_READY SLOT_ID=gas_emissions_3 SEQUENCE=$($checkpoint.sequence) PROGRESS=$nextProgress NEXT=REAL_PARCEL_BINDING_EVIDENCE"
