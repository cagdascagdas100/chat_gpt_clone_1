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
$resultPath = Join-Path $PSScriptRoot '012_gas_emissions_3_100_browser_acceptance_local_result_latest.json'
$statusPath = Join-Path $RepoRoot 'england_map_web\data\aays_18_slots\gas_emissions_3\browser_acceptance_runner_status_latest.json'

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
    $resolved = (Resolve-Path -LiteralPath $AbsolutePath).Path
    if (-not $resolved.StartsWith($RepoRoot, [StringComparison]::OrdinalIgnoreCase)) {
        throw "Path is outside repository: $resolved"
    }
    return $resolved.Substring($RepoRoot.Length).TrimStart('\').Replace('\','/')
}

function Write-Json($Value,[string]$Path) {
    $json = $Value | ConvertTo-Json -Depth 16
    [IO.File]::WriteAllText($Path,$json,[Text.UTF8Encoding]::new($false))
}

$activeBranch = Invoke-Git @('rev-parse','--abbrev-ref','HEAD')
if ($activeBranch -ne $Branch) { throw "Active branch mismatch. Expected $Branch, found $activeBranch" }
$remoteBefore = Get-RemoteHead
$localBefore = Invoke-Git @('rev-parse','HEAD')
if ($localBefore -ne $remoteBefore) {
    throw "Local/remote HEAD mismatch before browser execution. local=$localBefore remote=$remoteBefore"
}

& powershell.exe -NoProfile -ExecutionPolicy Bypass -File $coreScript -RepoRoot $RepoRoot -Branch $Branch
$coreExitCode = $LASTEXITCODE
if ($coreExitCode -ne 0) { throw "Core browser acceptance failed with exit code $coreExitCode" }
if (-not (Test-Path -LiteralPath $resultPath)) { throw "Browser proof result was not created: $resultPath" }
if (-not (Test-Path -LiteralPath $statusPath)) { throw "Browser status was not created: $statusPath" }

$result = Get-Content -Raw -LiteralPath $resultPath | ConvertFrom-Json
if ($result.browser_dom_passed -ne $true) { throw 'Browser DOM result is not PASS; proof will not be published.' }

$relativeResult = Get-RepoRelativePath $resultPath
$relativeStatus = Get-RepoRelativePath $statusPath
Invoke-Git @('add','--',$relativeResult,$relativeStatus) | Out-Null
$commitOutput = & git -C $RepoRoot commit -m 'gas_emissions_3: record canonical 100-row browser DOM proof' 2>&1
if ($LASTEXITCODE -ne 0 -and ($commitOutput -join ' ') -notmatch 'nothing to commit') {
    throw ($commitOutput -join [Environment]::NewLine)
}
Invoke-Git @('push','origin',$Branch) | Out-Null
$proofCommit = Invoke-Git @('rev-parse','HEAD')
$proofRemote = Get-RemoteHead
$proofReadbackPassed = $proofCommit -eq $proofRemote
if (-not $proofReadbackPassed) { throw "Proof remote readback failed. local=$proofCommit remote=$proofRemote" }

$result = Get-Content -Raw -LiteralPath $resultPath | ConvertFrom-Json
$result.status = 'BROWSER_100_ACCEPTANCE_PASS_REMOTE_PROOF_READBACK'
$result.browser_acceptance_passed = $true
$result.git.proof_commit = $proofCommit
$result.git.proof_remote_head = $proofRemote
$result.git.proof_remote_readback_passed = $true
Write-Json $result $resultPath

$status = Get-Content -Raw -LiteralPath $statusPath | ConvertFrom-Json
$status.status = 'BROWSER_100_ACCEPTANCE_PASS_REMOTE_PROOF_READBACK'
$status.browser_acceptance_passed = $true
$status.steps[11].state = 'PASS'
$status.steps[11].evidence = "local=$proofCommit remote=$proofRemote"
Write-Json $status $statusPath

Invoke-Git @('add','--',$relativeResult,$relativeStatus) | Out-Null
$readbackCommitOutput = & git -C $RepoRoot commit -m 'gas_emissions_3: record browser proof remote readback' 2>&1
if ($LASTEXITCODE -ne 0 -and ($readbackCommitOutput -join ' ') -notmatch 'nothing to commit') {
    throw ($readbackCommitOutput -join [Environment]::NewLine)
}
Invoke-Git @('push','origin',$Branch) | Out-Null
$finalLocal = Invoke-Git @('rev-parse','HEAD')
$finalRemote = Get-RemoteHead
if ($finalLocal -ne $finalRemote) { throw "Final remote readback failed. local=$finalLocal remote=$finalRemote" }

Write-Output "BROWSER_100_ACCEPTANCE_PASS_REMOTE_PROOF_READBACK SLOT_ID=gas_emissions_3 COMMIT=$finalLocal"
exit 0
