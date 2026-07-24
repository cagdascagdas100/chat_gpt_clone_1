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
$v4Wrapper = Join-Path $PSScriptRoot 'publish_gas_emissions_3_100_browser_proof_v4.ps1'
$screenshotScript = Join-Path $PSScriptRoot 'capture_gas_emissions_3_matrix_screenshot.ps1'
$screenshotPath = Join-Path $PSScriptRoot '013_gas_emissions_3_matrix_browser_screenshot_latest.png'
$screenshotMetaPath = Join-Path $PSScriptRoot '013_gas_emissions_3_matrix_browser_screenshot_latest.json'
$resultPath = Join-Path $PSScriptRoot '012_gas_emissions_3_100_browser_acceptance_local_result_latest.json'
$statusPath = Join-Path $RepoRoot 'england_map_web\data\aays_18_slots\gas_emissions_3\browser_acceptance_runner_status_latest.json'
$bundlePath = Join-Path $RepoRoot 'england_map_web\data\aays_18_slots\gas_emissions_3\browser_acceptance_execution_bundle_v5_latest.json'

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
    $json = $Value | ConvertTo-Json -Depth 48
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

foreach ($required in @($v4Wrapper,$screenshotScript,$bundlePath)) {
    if (-not (Test-Path -LiteralPath $required -PathType Leaf)) { throw "Required file not found: $required" }
}

$activeBranch = Invoke-Git @('rev-parse','--abbrev-ref','HEAD')
if ($activeBranch -ne $Branch) { throw "Active branch mismatch. Expected $Branch, found $activeBranch" }
$localBefore = Invoke-Git @('rev-parse','HEAD')
$remoteBefore = Get-RemoteHead
if ($localBefore -ne $remoteBefore) { throw "Local/remote HEAD mismatch before v5 execution. local=$localBefore remote=$remoteBefore" }

$bundle = Read-Json $bundlePath
if ($bundle.slot_id -ne $slotId) { throw "Unexpected bundle slot_id: $($bundle.slot_id)" }
$bundleEntries = @($bundle.launcher,$bundle.wrapper_v5,$bundle.wrapper_v4,$bundle.screenshot,$bundle.core,$bundle.publisher,$bundle.finalizer)
if ($bundleEntries.Count -ne 7) { throw "Expected 7 v5 bundle entries, found $($bundleEntries.Count)" }
$bundlePaths = @($bundleEntries | ForEach-Object { [string]$_.path })
$bundleRelative = Get-RepoRelativePath $bundlePath
$bundleDirty = & git -C $RepoRoot status --porcelain -- @bundlePaths $bundleRelative 2>&1
if ($LASTEXITCODE -ne 0) { throw ($bundleDirty -join [Environment]::NewLine) }
if (-not [string]::IsNullOrWhiteSpace(($bundleDirty -join '').Trim())) {
    throw "V5 bundle or manifest is modified in the working tree: $($bundleDirty -join '; ')"
}

$shaEvidence = @()
foreach ($entry in $bundleEntries) {
    $expected = [string]$entry.blob_sha
    $actual = Invoke-Git @('rev-parse',"HEAD:$($entry.path)")
    if ($actual -ne $expected) { throw "V5 bundle blob SHA mismatch for $($entry.path). expected=$expected actual=$actual" }
    $shaEvidence += "$($entry.path)=$actual"
}

& powershell.exe -NoProfile -ExecutionPolicy Bypass -File $screenshotScript -RepoRoot $RepoRoot
$screenshotExit = $LASTEXITCODE
if ($screenshotExit -ne 0) { throw "Matrix screenshot capture failed with exit code $screenshotExit" }
$screenshotMeta = Read-Json $screenshotMetaPath
if ($screenshotMeta.slot_id -ne $slotId -or $screenshotMeta.passed -ne $true) { throw 'Screenshot metadata is not PASS.' }
if (-not (Test-Path -LiteralPath $screenshotPath -PathType Leaf)) { throw "Screenshot file missing: $screenshotPath" }
$actualScreenshotHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $screenshotPath).Hash.ToLowerInvariant()
if ($actualScreenshotHash -ne [string]$screenshotMeta.screenshot_sha256) { throw 'Screenshot SHA-256 readback mismatch before browser proof.' }

& powershell.exe -NoProfile -ExecutionPolicy Bypass -File $v4Wrapper -RepoRoot $RepoRoot -Branch $Branch
$v4Exit = $LASTEXITCODE
if ($v4Exit -ne 0) { throw "V4 browser proof chain failed with exit code $v4Exit" }

$v4Local = Invoke-Git @('rev-parse','HEAD')
$v4Remote = Get-RemoteHead
if ($v4Local -ne $v4Remote) { throw "V4 final remote readback mismatch. local=$v4Local remote=$v4Remote" }

$result = Read-Json $resultPath
$status = Read-Json $statusPath
if ($result.browser_dom_passed -ne $true -or $result.browser_acceptance_passed -ne $true) { throw 'V4 result is not browser PASS.' }

$screenshotRecord = [ordered]@{
    path=Get-RepoRelativePath $screenshotPath
    metadata_path=Get-RepoRelativePath $screenshotMetaPath
    sha256=$actualScreenshotHash
    bytes=[int64]$screenshotMeta.screenshot_bytes
    browser_exit_code=[int]$screenshotMeta.browser_exit_code
    passed=$true
}
$result | Add-Member -NotePropertyName screenshot -NotePropertyValue $screenshotRecord -Force
$result.status = 'BROWSER_100_ACCEPTANCE_PASS_SCREENSHOT_REMOTE_LEDGER_PENDING'
$result.git | Add-Member -NotePropertyName v5_bundle_sha_gate_passed -NotePropertyValue $true -Force
$result.git | Add-Member -NotePropertyName screenshot_remote_readback_required -NotePropertyValue $true -Force

$steps = @($status.steps)
$steps += (New-Step 18 'CAPTURE_CANONICAL_MATRIX_SCREENSHOT_AND_SHA256' 'PASS' "path=$($screenshotRecord.path) sha256=$actualScreenshotHash bytes=$($screenshotRecord.bytes)")
$steps += (New-Step 19 'COMMIT_SCREENSHOT_LEDGER_AND_REMOTE_READBACK' 'PENDING' "v4_commit=$v4Local")
$status.schema_version = 5
$status.runner_version = 5
$status.status = 'BROWSER_100_ACCEPTANCE_PASS_SCREENSHOT_REMOTE_LEDGER_PENDING'
$status.steps = $steps
$status | Add-Member -NotePropertyName screenshot -NotePropertyValue $screenshotRecord -Force
$status | Add-Member -NotePropertyName v5_bundle_sha_gate_executed -NotePropertyValue $true -Force
$status | Add-Member -NotePropertyName v5_bundle_sha_evidence -NotePropertyValue $shaEvidence -Force
Write-Json $result $resultPath
Write-Json $status $statusPath

$relativeResult = Get-RepoRelativePath $resultPath
$relativeStatus = Get-RepoRelativePath $statusPath
$relativeScreenshot = Get-RepoRelativePath $screenshotPath
$relativeScreenshotMeta = Get-RepoRelativePath $screenshotMetaPath
& git -C $RepoRoot diff --cached --quiet
if ($LASTEXITCODE -ne 0) { throw 'Unexpected staged files before screenshot ledger commit.' }
Invoke-Git @('add','--',$relativeResult,$relativeStatus,$relativeScreenshot,$relativeScreenshotMeta) | Out-Null
$commitOutput = & git -C $RepoRoot commit -m 'gas_emissions_3: persist canonical matrix screenshot proof ledger' 2>&1
if ($LASTEXITCODE -ne 0) { throw ($commitOutput -join [Environment]::NewLine) }
Invoke-Git @('push','origin',"HEAD:$Branch") | Out-Null
$ledgerLocal = Invoke-Git @('rev-parse','HEAD')
$ledgerRemote = Get-RemoteHead
if ($ledgerLocal -ne $ledgerRemote) { throw "Screenshot ledger remote readback failed. local=$ledgerLocal remote=$ledgerRemote" }

$result = Read-Json $resultPath
$result.status = 'BROWSER_100_ACCEPTANCE_PASS_SCREENSHOT_DURABLE_REMOTE_READBACK'
$result.git | Add-Member -NotePropertyName screenshot_ledger_commit -NotePropertyValue $ledgerLocal -Force
$result.git | Add-Member -NotePropertyName screenshot_ledger_remote_head -NotePropertyValue $ledgerRemote -Force
$result.git | Add-Member -NotePropertyName screenshot_remote_readback_passed -NotePropertyValue $true -Force
$status = Read-Json $statusPath
$status.status = 'BROWSER_100_ACCEPTANCE_PASS_SCREENSHOT_DURABLE_REMOTE_READBACK'
$status.steps[18].state = 'PASS'
$status.steps[18].evidence = "local=$ledgerLocal remote=$ledgerRemote"
$status | Add-Member -NotePropertyName screenshot_remote_readback_passed -NotePropertyValue $true -Force
Write-Json $result $resultPath
Write-Json $status $statusPath

Invoke-Git @('add','--',$relativeResult,$relativeStatus) | Out-Null
$finalOutput = & git -C $RepoRoot commit -m 'gas_emissions_3: record screenshot ledger remote readback' 2>&1
if ($LASTEXITCODE -ne 0) { throw ($finalOutput -join [Environment]::NewLine) }
Invoke-Git @('push','origin',"HEAD:$Branch") | Out-Null
$finalLocal = Invoke-Git @('rev-parse','HEAD')
$finalRemote = Get-RemoteHead
if ($finalLocal -ne $finalRemote) { throw "Final screenshot readback status mismatch. local=$finalLocal remote=$finalRemote" }

Write-Output "BROWSER_100_ACCEPTANCE_PASS_SCREENSHOT_DURABLE_REMOTE_READBACK SLOT_ID=$slotId SCREENSHOT_SHA256=$actualScreenshotHash LEDGER_COMMIT=$ledgerLocal FINAL_COMMIT=$finalLocal NEXT=REAL_PARCEL_BINDING_EVIDENCE"
exit 0
