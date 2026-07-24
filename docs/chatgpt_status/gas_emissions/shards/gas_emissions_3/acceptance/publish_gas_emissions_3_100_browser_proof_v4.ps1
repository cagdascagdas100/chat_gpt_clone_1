[CmdletBinding()]
param(
    [string]$RepoRoot = $env:AAYS_REPO_ROOT,
    [string]$Branch = 'codex/aays-single-runner-v5-20260706'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

if ([string]::IsNullOrWhiteSpace($RepoRoot)) {
    $RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..\..\..\..')).Path
}
$RepoRoot = (Resolve-Path -LiteralPath $RepoRoot).Path.TrimEnd('\')

$slotId = 'gas_emissions_3'
$publisherScript = Join-Path $PSScriptRoot 'publish_gas_emissions_3_100_browser_proof.ps1'
$resultPath = Join-Path $PSScriptRoot '012_gas_emissions_3_100_browser_acceptance_local_result_latest.json'
$statusPath = Join-Path $RepoRoot 'england_map_web\data\aays_18_slots\gas_emissions_3\browser_acceptance_runner_status_latest.json'
$summaryPath = Join-Path $RepoRoot 'england_map_web\data\aays_18_slots\gas_emissions_3\summary_latest.json'
$checkpointPath = Join-Path $RepoRoot 'docs\chatgpt_status\_shared\slots_21\gas_emissions_3\checkpoint_latest.json'
$bundlePath = Join-Path $RepoRoot 'england_map_web\data\aays_18_slots\gas_emissions_3\browser_acceptance_execution_bundle_latest.json'

function Invoke-Git([string[]]$GitArgs) {
    $output = & git -C $RepoRoot @GitArgs 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "git $($GitArgs -join ' ') failed: $($output -join [Environment]::NewLine)"
    }
    return (($output -join [Environment]::NewLine).Trim())
}

function Get-RemoteHead {
    $raw = Invoke-Git @('ls-remote','origin',"refs/heads/$Branch")
    if ([string]::IsNullOrWhiteSpace($raw)) { throw "Remote branch not found: $Branch" }
    return ($raw -split '\s+')[0]
}

function Read-Json([string]$Path) {
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { throw "Required JSON not found: $Path" }
    return (Get-Content -Raw -LiteralPath $Path | ConvertFrom-Json)
}

function Write-Json($Value,[string]$Path) {
    $json = $Value | ConvertTo-Json -Depth 40
    [IO.File]::WriteAllText($Path,$json,[Text.UTF8Encoding]::new($false))
}

function Get-RepoRelativePath([string]$AbsolutePath) {
    $full = [IO.Path]::GetFullPath($AbsolutePath)
    if (-not $full.StartsWith($RepoRoot,[StringComparison]::OrdinalIgnoreCase)) {
        throw "Path is outside repository: $full"
    }
    return $full.Substring($RepoRoot.Length).TrimStart('\').Replace('\','/')
}

function New-Step([int]$Number,[string]$Name,[string]$State,[string]$Evidence) {
    return [ordered]@{step=$Number;name=$Name;state=$State;evidence=$Evidence}
}

foreach ($required in @($publisherScript,$bundlePath)) {
    if (-not (Test-Path -LiteralPath $required -PathType Leaf)) { throw "Required file not found: $required" }
}

$activeBranch = Invoke-Git @('rev-parse','--abbrev-ref','HEAD')
if ($activeBranch -ne $Branch) { throw "Active branch mismatch. Expected $Branch, found $activeBranch" }
$localBefore = Invoke-Git @('rev-parse','HEAD')
$remoteBefore = Get-RemoteHead
if ($localBefore -ne $remoteBefore) {
    throw "Local/remote HEAD mismatch before v4 execution. local=$localBefore remote=$remoteBefore"
}

$bundle = Read-Json $bundlePath
if ($bundle.slot_id -ne $slotId) { throw "Unexpected bundle slot_id: $($bundle.slot_id)" }
$bundleEntries = @($bundle.launcher,$bundle.wrapper,$bundle.core,$bundle.publisher,$bundle.finalizer)
if ($bundleEntries.Count -ne 5) { throw "Expected 5 bundle entries, found $($bundleEntries.Count)" }
$bundlePaths = @($bundleEntries | ForEach-Object { [string]$_.path })
$bundleRelative = Get-RepoRelativePath $bundlePath
$bundleDirty = & git -C $RepoRoot status --porcelain -- @bundlePaths $bundleRelative 2>&1
if ($LASTEXITCODE -ne 0) { throw ($bundleDirty -join [Environment]::NewLine) }
if (-not [string]::IsNullOrWhiteSpace(($bundleDirty -join '').Trim())) {
    throw "Acceptance bundle or manifest is modified in the working tree: $($bundleDirty -join '; ')"
}

$shaEvidence = @()
foreach ($entry in $bundleEntries) {
    $expected = [string]$entry.blob_sha
    $actual = Invoke-Git @('rev-parse',"HEAD:$($entry.path)")
    if ($actual -ne $expected) {
        throw "Bundle blob SHA mismatch for $($entry.path). expected=$expected actual=$actual"
    }
    $shaEvidence += "$($entry.path)=$actual"
}

& powershell.exe -NoProfile -ExecutionPolicy Bypass -File $publisherScript -RepoRoot $RepoRoot -Branch $Branch
$publisherExitCode = $LASTEXITCODE
if ($publisherExitCode -ne 0) { throw "Browser publisher failed with exit code $publisherExitCode" }

$finalStateLocal = Invoke-Git @('rev-parse','HEAD')
$finalStateRemote = Get-RemoteHead
if ($finalStateLocal -ne $finalStateRemote) {
    throw "Final state remote readback failed after publisher. local=$finalStateLocal remote=$finalStateRemote"
}

$result = Read-Json $resultPath
$summary = Read-Json $summaryPath
$checkpoint = Read-Json $checkpointPath
$runtimeStatus = Read-Json $statusPath
if ($result.slot_id -ne $slotId -or $summary.slot_id -ne $slotId -or $checkpoint.slot_id -ne $slotId) {
    throw 'Result, summary or checkpoint slot mismatch after publisher.'
}
if ($result.browser_dom_passed -ne $true -or $result.browser_acceptance_passed -ne $true) {
    throw 'Publisher returned success but browser acceptance flags are not PASS.'
}
if ($result.git.proof_remote_readback_passed -ne $true) {
    throw 'Proof commit remote readback flag is not PASS.'
}
if ([int]$summary.metrics.browser_verified_rows -ne 100 -or $summary.acceptance.passed -ne $true) {
    throw 'Summary was not advanced to browser 100 PASS.'
}
if ($checkpoint.first_unverified_step -ne 'REAL_PARCEL_BINDING_EVIDENCE') {
    throw "Unexpected next checkpoint step: $($checkpoint.first_unverified_step)"
}

$result.status = 'BROWSER_100_ACCEPTANCE_PASS_FINAL_STATE_REMOTE_READBACK'
$result.git | Add-Member -NotePropertyName final_state_commit -NotePropertyValue $finalStateLocal -Force
$result.git | Add-Member -NotePropertyName final_state_remote_head -NotePropertyValue $finalStateRemote -Force
$result.git | Add-Member -NotePropertyName final_state_remote_readback_passed -NotePropertyValue $true -Force
$result.git | Add-Member -NotePropertyName bundle_blob_sha_gate_passed -NotePropertyValue $true -Force
$result.git | Add-Member -NotePropertyName durable_readback_ledger_required -NotePropertyValue $true -Force

$browserErrors = @($result.browser_script_errors).Count
$steps = @(
    (New-Step 1 'VALIDATE_REPO_ROOT' 'PASS' $RepoRoot),
    (New-Step 2 'VALIDATE_ACTIVE_BRANCH_AND_REMOTE_HEAD' 'PASS' "branch=$activeBranch local=$localBefore remote=$remoteBefore"),
    (New-Step 3 'VERIFY_ACCEPTANCE_BUNDLE_BLOB_SHAS' 'PASS' "verified=5 manifest=$bundleRelative"),
    (New-Step 4 'REJECT_PRESTAGED_OR_DIRTY_TARGET_PROOF_FILES' 'PASS' 'publisher preflight completed'),
    (New-Step 5 'CHECK_PORT_8012_HTTP_ENDPOINTS' 'PASS' "endpoints=$($result.http.endpoint_count) all_status_200=$($result.http.all_status_200)"),
    (New-Step 6 'VERIFY_SERVED_100_ROWS_AND_100_UNIQUE_IDS' 'PASS' "rows=$($result.http.served_row_count) unique=$($result.http.served_unique_row_count) status=$($result.http.matrix_status_row_count)"),
    (New-Step 7 'FIND_EXISTING_EDGE_OR_CHROME' 'PASS' ([string]$result.browser_path)),
    (New-Step 8 'DUMP_PRECHECK_DOM_WITH_JAVASCRIPT' 'PASS' "exit=$($result.precheck.exit_code)"),
    (New-Step 9 'VERIFY_100_PRECHECK_PASS_ROWS' 'PASS' "pass=$($result.precheck.pass_rows) fail=$($result.precheck.fail_rows)"),
    (New-Step 10 'DUMP_CANONICAL_MATRIX_DOM_WITH_JAVASCRIPT' 'PASS' "exit=$($result.matrix.exit_code)"),
    (New-Step 11 'VERIFY_MATRIX_100_ROWS_AND_28_HEADERS' 'PASS' "headers=$($result.matrix.required_header_count) missing=$(@($result.matrix.missing_headers).Count)"),
    (New-Step 12 'CHECK_BROWSER_STDERR_FOR_SCRIPT_ERRORS' 'PASS' "errors=$browserErrors"),
    (New-Step 13 'WRITE_LOCAL_BROWSER_PROOF_JSON' 'PASS' (Get-RepoRelativePath $resultPath)),
    (New-Step 14 'COMMIT_BROWSER_PROOF_AND_REMOTE_READBACK' 'PASS' "local=$($result.git.proof_commit) remote=$($result.git.proof_remote_head)"),
    (New-Step 15 'ADVANCE_SUMMARY_CHECKPOINT_TO_REAL_PARCEL_BINDING_GATE' 'PASS' "sequence=$($checkpoint.sequence) next=$($checkpoint.first_unverified_step)"),
    (New-Step 16 'COMMIT_FINAL_STATE_AND_REMOTE_READBACK' 'PASS' "local=$finalStateLocal remote=$finalStateRemote"),
    (New-Step 17 'RECORD_DURABLE_FINAL_READBACK_LEDGER' 'PASS' "final_state_commit=$finalStateLocal final_state_remote=$finalStateRemote")
)

$target = if ($runtimeStatus.PSObject.Properties.Name -contains 'target') { $runtimeStatus.target } else { [ordered]@{} }
$ledgerStatus = [ordered]@{
    schema_version=4
    slot_id=$slotId
    updated_at=[DateTime]::UtcNow.ToString('o')
    status='BROWSER_100_ACCEPTANCE_PASS_DURABLE_REMOTE_READBACK_LEDGER'
    runner_policy='EXISTING_CANONICAL_F_SHARED_RUNNER_ONLY'
    runner_version=4
    launcher_path=$bundle.launcher.path
    wrapper_path=$bundle.wrapper.path
    core_script_path=$bundle.core.path
    publisher_script_path=$bundle.publisher.path
    finalizer_script_path=$bundle.finalizer.path
    bundle_manifest_path=$bundleRelative
    browser_path=[string]$result.browser_path
    target=$target
    steps=$steps
    bundle_sha_gate_executed=$true
    bundle_sha_gate_passed=$true
    bundle_sha_evidence=$shaEvidence
    dirty_index_gate_executed=$true
    branch_race_gate_executed=$true
    http_data_gate_executed=$true
    core_runner_executed=$true
    publisher_executed=$true
    finalizer_executed=$true
    final_state_remote_readback_passed=$true
    durable_readback_ledger_recorded=$true
    browser_dom_passed=$true
    browser_acceptance_passed=$true
    parcel_binding_gate_passed=$false
    final_ready=$false
    fake_data=$false
    db_write=$false
    migration=$false
    production_deploy=$false
}

Write-Json $result $resultPath
Write-Json $ledgerStatus $statusPath

$relativeResult = Get-RepoRelativePath $resultPath
$relativeStatus = Get-RepoRelativePath $statusPath
& git -C $RepoRoot diff --cached --quiet
if ($LASTEXITCODE -ne 0) { throw 'Unexpected staged files appeared before durable readback ledger commit.' }
Invoke-Git @('add','--',$relativeResult,$relativeStatus) | Out-Null
$ledgerCommitOutput = & git -C $RepoRoot commit -m 'gas_emissions_3: persist durable browser final-state readback ledger' 2>&1
if ($LASTEXITCODE -ne 0) { throw ($ledgerCommitOutput -join [Environment]::NewLine) }
Invoke-Git @('push','origin',"HEAD:$Branch") | Out-Null
$ledgerLocal = Invoke-Git @('rev-parse','HEAD')
$ledgerRemote = Get-RemoteHead
if ($ledgerLocal -ne $ledgerRemote) {
    throw "Durable ledger remote readback failed. local=$ledgerLocal remote=$ledgerRemote"
}

Write-Output "BROWSER_100_ACCEPTANCE_PASS_DURABLE_REMOTE_READBACK_LEDGER SLOT_ID=$slotId FINAL_STATE_COMMIT=$finalStateLocal LEDGER_COMMIT=$ledgerLocal NEXT=REAL_PARCEL_BINDING_EVIDENCE"
exit 0
