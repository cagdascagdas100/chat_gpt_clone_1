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
$coreScript = Join-Path $PSScriptRoot 'run_gas_emissions_3_100_browser_acceptance.ps1'
$finalizerScript = Join-Path $PSScriptRoot 'finalize_gas_emissions_3_after_browser_proof.ps1'
$resultPath = Join-Path $PSScriptRoot '012_gas_emissions_3_100_browser_acceptance_local_result_latest.json'
$statusPath = Join-Path $RepoRoot 'england_map_web\data\aays_18_slots\gas_emissions_3\browser_acceptance_runner_status_latest.json'
$summaryPath = Join-Path $RepoRoot 'england_map_web\data\aays_18_slots\gas_emissions_3\summary_latest.json'
$checkpointPath = Join-Path $RepoRoot 'docs\chatgpt_status\_shared\slots_21\gas_emissions_3\checkpoint_latest.json'

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

function Get-RepoRelativePath([string]$AbsolutePath) {
    $resolvedParent = Split-Path -Parent $AbsolutePath
    if (-not (Test-Path -LiteralPath $resolvedParent)) { throw "Parent path not found: $resolvedParent" }
    $full = [IO.Path]::GetFullPath($AbsolutePath)
    if (-not $full.StartsWith($RepoRoot, [StringComparison]::OrdinalIgnoreCase)) {
        throw "Path is outside repository: $full"
    }
    return $full.Substring($RepoRoot.Length).TrimStart('\').Replace('\','/')
}

function Write-Json($Value,[string]$Path) {
    $json = $Value | ConvertTo-Json -Depth 32
    [IO.File]::WriteAllText($Path,$json,[Text.UTF8Encoding]::new($false))
}

foreach ($required in @($coreScript,$finalizerScript)) {
    if (-not (Test-Path -LiteralPath $required -PathType Leaf)) { throw "Required script not found: $required" }
}

$relativeResult = Get-RepoRelativePath $resultPath
$relativeStatus = Get-RepoRelativePath $statusPath
$relativeSummary = Get-RepoRelativePath $summaryPath
$relativeCheckpoint = Get-RepoRelativePath $checkpointPath
$targetPaths = @($relativeResult,$relativeStatus,$relativeSummary,$relativeCheckpoint)

$activeBranch = Invoke-Git @('rev-parse','--abbrev-ref','HEAD')
if ($activeBranch -ne $Branch) { throw "Active branch mismatch. Expected $Branch, found $activeBranch" }
$remoteBefore = Get-RemoteHead
$localBefore = Invoke-Git @('rev-parse','HEAD')
if ($localBefore -ne $remoteBefore) {
    throw "Local/remote HEAD mismatch before browser execution. local=$localBefore remote=$remoteBefore"
}

& git -C $RepoRoot diff --cached --quiet
if ($LASTEXITCODE -ne 0) { throw 'Git index contains staged changes; refusing to publish shared-runner proof.' }
$targetStatusBefore = & git -C $RepoRoot status --porcelain -- @targetPaths 2>&1
if ($LASTEXITCODE -ne 0) { throw ($targetStatusBefore -join [Environment]::NewLine) }
if (-not [string]::IsNullOrWhiteSpace(($targetStatusBefore -join '').Trim())) {
    throw "Target proof/state files are already modified before execution: $($targetStatusBefore -join '; ')"
}

& powershell.exe -NoProfile -ExecutionPolicy Bypass -File $coreScript -RepoRoot $RepoRoot -Branch $Branch
$coreExitCode = $LASTEXITCODE
if ($coreExitCode -ne 0) { throw "Core browser acceptance failed with exit code $coreExitCode" }
if (-not (Test-Path -LiteralPath $resultPath)) { throw "Browser proof result was not created: $resultPath" }
if (-not (Test-Path -LiteralPath $statusPath)) { throw "Browser status was not created: $statusPath" }

$localAfterRun = Invoke-Git @('rev-parse','HEAD')
$remoteAfterRun = Get-RemoteHead
if ($localAfterRun -ne $localBefore -or $remoteAfterRun -ne $remoteBefore -or $localAfterRun -ne $remoteAfterRun) {
    throw "Branch moved during browser execution. before=$localBefore local_after=$localAfterRun remote_after=$remoteAfterRun"
}

$result = Get-Content -Raw -LiteralPath $resultPath | ConvertFrom-Json
if ($result.slot_id -ne 'gas_emissions_3') { throw "Unexpected proof slot_id: $($result.slot_id)" }
if ($result.browser_dom_passed -ne $true) { throw 'Browser DOM result is not PASS; proof will not be published.' }

Invoke-Git @('add','--',$relativeResult,$relativeStatus) | Out-Null
$commitOutput = & git -C $RepoRoot commit -m 'gas_emissions_3: record canonical 100-row browser DOM proof' 2>&1
if ($LASTEXITCODE -ne 0) { throw ($commitOutput -join [Environment]::NewLine) }
Invoke-Git @('push','origin',"HEAD:$Branch") | Out-Null
$proofCommit = Invoke-Git @('rev-parse','HEAD')
$proofRemote = Get-RemoteHead
if ($proofCommit -ne $proofRemote) { throw "Proof remote readback failed. local=$proofCommit remote=$proofRemote" }

$result = Get-Content -Raw -LiteralPath $resultPath | ConvertFrom-Json
$result.status = 'BROWSER_100_ACCEPTANCE_PASS_REMOTE_PROOF_READBACK'
$result.browser_acceptance_passed = $true
$result.git.proof_remote_readback_passed = $true
$result.git | Add-Member -NotePropertyName proof_commit -NotePropertyValue $proofCommit -Force
$result.git | Add-Member -NotePropertyName proof_remote_head -NotePropertyValue $proofRemote -Force
Write-Json $result $resultPath

$status = Get-Content -Raw -LiteralPath $statusPath | ConvertFrom-Json
$status.status = 'BROWSER_100_ACCEPTANCE_PASS_REMOTE_PROOF_READBACK'
$status.browser_acceptance_passed = $true
$status.publisher_executed = $true
if (@($status.steps).Count -ge 12) {
    $status.steps[11].state = 'PASS'
    $status.steps[11].evidence = "proof_local=$proofCommit proof_remote=$proofRemote"
}
Write-Json $status $statusPath

& powershell.exe -NoProfile -ExecutionPolicy Bypass -File $finalizerScript -RepoRoot $RepoRoot -ResultPath $resultPath
if ($LASTEXITCODE -ne 0) { throw "Post-browser finalizer failed with exit code $LASTEXITCODE" }

& git -C $RepoRoot diff --cached --quiet
if ($LASTEXITCODE -ne 0) { throw 'Unexpected staged files appeared before final state commit.' }
Invoke-Git @('add','--',$relativeResult,$relativeStatus,$relativeSummary,$relativeCheckpoint) | Out-Null
$finalCommitOutput = & git -C $RepoRoot commit -m 'gas_emissions_3: finalize browser proof and advance to parcel binding gate' 2>&1
if ($LASTEXITCODE -ne 0) { throw ($finalCommitOutput -join [Environment]::NewLine) }
Invoke-Git @('push','origin',"HEAD:$Branch") | Out-Null
$finalLocal = Invoke-Git @('rev-parse','HEAD')
$finalRemote = Get-RemoteHead
if ($finalLocal -ne $finalRemote) { throw "Final remote readback failed. local=$finalLocal remote=$finalRemote" }

Write-Output "BROWSER_100_ACCEPTANCE_PASS_REMOTE_PROOF_READBACK SLOT_ID=gas_emissions_3 PROOF_COMMIT=$proofCommit FINAL_COMMIT=$finalLocal NEXT=REAL_PARCEL_BINDING_EVIDENCE"
exit 0
