[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$slotId = 'gas_emissions_3'
$pageKey = 'gas_emissions'
$branch = 'codex/aays-single-runner-v5-20260706'
$repoRoot = (Get-Location).Path.TrimEnd('\')
$portableRoot = [string]$env:AAYS_PORTABLE_ROOT
$wrapperRelative = 'docs/chatgpt_status/gas_emissions/shards/gas_emissions_3/automation/021_gas_emissions_3_queue_runtime_token_wrapper.ps1'
$carrierRelative = 'docs/chatgpt_status/gas_emissions/shards/gas_emissions_3/automation/020_gas_emissions_3_coordinator_browser_acceptance_carrier.ps1'
$harnessRelative = 'england_map_web/data/aays_18_slots/gas_emissions_3/canonical_matrix_100_browser_harness.html'
$carrierPath = Join-Path $repoRoot ($carrierRelative.Replace('/','\'))
$runtimeProofRoot = Join-Path $repoRoot 'docs\chatgpt_status\gas_emissions\shards\gas_emissions_3\acceptance\020_coordinator_browser_runtime_latest'
$tokenUrl = 'http://127.0.0.1:8012/england_map_web/data/aays_18_slots/gas_emissions_3/runner_runtime_token_latest.json'
$expectedTokenId = 'gas_emissions_3_v11_queue_20260721_001'
$expectedTaskId = 'gas_emissions_3_coordinator_browser_acceptance_v11_20260721_01'
$virtualTimeBudgetMs = 180000
$httpTimeoutSeconds = 45
$remoteTrackingRef = "refs/remotes/origin/$branch"

function Resolve-PortableRoot([string]$StartPath) {
    if (-not [string]::IsNullOrWhiteSpace($portableRoot) -and (Test-Path -LiteralPath $portableRoot -PathType Container)) { return $portableRoot.TrimEnd('\') }
    $cursor = [System.IO.Path]::GetFullPath($StartPath).TrimEnd('\')
    while (-not [string]::IsNullOrWhiteSpace($cursor)) {
        if ((Split-Path -Leaf $cursor) -eq 'runner_system') { return (Split-Path -Parent $cursor) }
        $parent = Split-Path -Parent $cursor
        if ([string]::IsNullOrWhiteSpace($parent) -or $parent -eq $cursor) { break }
        $cursor = $parent
    }
    throw "AAYS portable root could not be resolved from $StartPath"
}
$portableRoot = Resolve-PortableRoot $repoRoot

$gitCandidates = @(
    (Join-Path $portableRoot 'runtime\git\cmd\git.exe'),
    (Join-Path $portableRoot 'runtime\git\bin\git.exe')
)
$gitCommand = Get-Command git.exe -ErrorAction SilentlyContinue
if (-not $gitCommand) { $gitCommand = Get-Command git -ErrorAction SilentlyContinue }
if ($gitCommand) { $gitCandidates += $gitCommand.Source }
$gitExe = $gitCandidates | Where-Object { $_ -and (Test-Path -LiteralPath $_ -PathType Leaf) } | Select-Object -Unique | Select-Object -First 1
if (-not $gitExe) { throw 'Portable or system git executable was not found.' }
$gitExe = [string]$gitExe

function Invoke-Git([string[]]$GitArgs) {
    $output = & $gitExe -C $repoRoot @GitArgs 2>&1
    if ($LASTEXITCODE -ne 0) { throw "$gitExe $($GitArgs -join ' ') failed: $($output -join [Environment]::NewLine)" }
    return (($output -join [Environment]::NewLine).Trim())
}
function Sync-RemoteTrackingHead {
    $fetchArgs = @('-c','pack.windowMemory=8m','-c','pack.packSizeLimit=20m','-c','pack.threads=1','-c','core.compression=0','fetch','--no-tags','--depth=64','origin',("+refs/heads/$branch`:$remoteTrackingRef"))
    [void](Invoke-Git $fetchArgs)
    return Invoke-Git @('rev-parse',$remoteTrackingRef)
}
function Assert-RemoteBlobParity([string]$Path,[string]$LocalRef,[string]$RemoteRef) {
    $localBlob = Invoke-Git @('rev-parse',"$LocalRef`:$Path")
    $remoteBlob = Invoke-Git @('rev-parse',"$RemoteRef`:$Path")
    if ($localBlob -ne $remoteBlob) { throw "Remote blob changed for $Path. local=$localBlob remote=$remoteBlob" }
    return $localBlob
}
function Remove-BrowserProfiles {
    foreach ($name in @('profile_precheck','profile_matrix','profile_screenshot')) {
        Remove-Item -Recurse -Force -LiteralPath (Join-Path $runtimeProofRoot $name) -ErrorAction SilentlyContinue
    }
}

if (-not [string]::IsNullOrWhiteSpace([string]$env:AAYS_TASK_ID) -and [string]$env:AAYS_TASK_ID -ne $expectedTaskId) { throw "AAYS_TASK_ID mismatch: $env:AAYS_TASK_ID" }
if (-not [string]::IsNullOrWhiteSpace([string]$env:AAYS_PAGE_KEY) -and [string]$env:AAYS_PAGE_KEY -ne $pageKey) { throw "AAYS_PAGE_KEY mismatch: $env:AAYS_PAGE_KEY" }
if (-not [string]::IsNullOrWhiteSpace([string]$env:AAYS_TARGET_BRANCH) -and [string]$env:AAYS_TARGET_BRANCH -ne $branch) { throw "AAYS_TARGET_BRANCH mismatch: $env:AAYS_TARGET_BRANCH" }
if (-not [string]::IsNullOrWhiteSpace([string]$env:AAYS_SLOT_ID) -and [string]$env:AAYS_SLOT_ID -ne $slotId) { throw "AAYS_SLOT_ID mismatch: $env:AAYS_SLOT_ID" }
if (-not [string]::IsNullOrWhiteSpace([string]$env:AAYS_CHILD_DIRECT_PUSH_FORBIDDEN) -and [string]$env:AAYS_CHILD_DIRECT_PUSH_FORBIDDEN -ne 'true') { throw 'Coordinator child direct-push guard conflicts with queue contract.' }
if (-not (Test-Path -LiteralPath $carrierPath -PathType Leaf)) { throw "Carrier missing: $carrierPath" }

$localHead = Invoke-Git @('rev-parse','HEAD')
$remoteHead = Sync-RemoteTrackingHead
$mergeBase = Invoke-Git @('merge-base',$localHead,$remoteHead)
if ($mergeBase -ne $localHead) { throw "Detached child HEAD is not an ancestor of remote HEAD. local=$localHead remote=$remoteHead merge_base=$mergeBase" }
$remoteAheadCount = [int](Invoke-Git @('rev-list','--count',"$localHead..$remoteHead"))
$wrapperBlob = Assert-RemoteBlobParity $wrapperRelative 'HEAD' $remoteTrackingRef
$carrierBlob = Assert-RemoteBlobParity $carrierRelative 'HEAD' $remoteTrackingRef
$harnessBlob = Assert-RemoteBlobParity $harnessRelative 'HEAD' $remoteTrackingRef

$response = Invoke-WebRequest -Uri $tokenUrl -UseBasicParsing -TimeoutSec 30 -Headers @{'Cache-Control'='no-cache'}
if ([int]$response.StatusCode -ne 200) { throw "Runtime token HTTP status is $($response.StatusCode)" }
$token = [string]$response.Content | ConvertFrom-Json
if ($token.slot_id -ne $slotId) { throw "Runtime token slot mismatch: $($token.slot_id)" }
if ($token.token_id -ne $expectedTokenId) { throw "Runtime token id mismatch: $($token.token_id)" }
if ($token.task_id -ne $expectedTaskId) { throw "Runtime token task mismatch: $($token.task_id)" }
if ($token.wrapper_path -ne $wrapperRelative -or $token.wrapper_blob_sha -ne $wrapperBlob) { throw 'Served runtime token wrapper contract mismatch.' }
if ($token.carrier_path -ne $carrierRelative -or $token.carrier_blob_sha -ne $carrierBlob) { throw 'Served runtime token carrier contract mismatch.' }
if ($token.harness_path -ne $harnessRelative -or $token.harness_blob_sha -ne $harnessBlob) { throw 'Served runtime token harness contract mismatch.' }
if ([int]$token.virtual_time_budget_ms -ne $virtualTimeBudgetMs -or [int]$token.http_timeout_seconds -ne $httpTimeoutSeconds) { throw 'Runtime token time budget contract mismatch.' }
if ($token.two_phase_remote_parity_required -ne $true -or $token.png_signature_required -ne $true -or [int]$token.screenshot_width -ne 1920 -or [int]$token.screenshot_height -ne 1080) { throw 'Runtime token v11 parity or PNG contract mismatch.' }
if ($token.final_ready -ne $false -or $token.fake_data -ne $false -or $token.db_write -ne $false -or $token.migration -ne $false -or $token.production_deploy -ne $false) { throw 'Runtime token safety flags are invalid.' }

Write-Output "GAS_EMISSIONS_3_RUNTIME_TOKEN_PASS token=$expectedTokenId task=$expectedTaskId local=$localHead remote=$remoteHead remote_ahead=$remoteAheadCount wrapper=$wrapperBlob carrier=$carrierBlob harness=$harnessBlob two_phase_remote_parity=true png=1920x1080"
$carrierExitCode = 1
$oldValues = @{}
foreach ($name in @('AAYS_SLOT_ID','AAYS_CHILD_DIRECT_PUSH_FORBIDDEN','AAYS_PORTABLE_ROOT','AAYS_VALIDATED_LOCAL_HEAD','AAYS_VALIDATED_REMOTE_HEAD','AAYS_REMOTE_HEAD_RELATION','AAYS_REMOTE_BLOB_PARITY')) { $oldValues[$name] = [Environment]::GetEnvironmentVariable($name,'Process') }
try {
    $env:AAYS_SLOT_ID = $slotId
    $env:AAYS_CHILD_DIRECT_PUSH_FORBIDDEN = 'true'
    $env:AAYS_PORTABLE_ROOT = $portableRoot
    $env:AAYS_VALIDATED_LOCAL_HEAD = $localHead
    $env:AAYS_VALIDATED_REMOTE_HEAD = $remoteHead
    $env:AAYS_REMOTE_HEAD_RELATION = 'LOCAL_ANCESTOR_OF_REMOTE'
    $env:AAYS_REMOTE_BLOB_PARITY = 'true'
    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $carrierPath -VirtualTimeBudgetMs $virtualTimeBudgetMs -HttpTimeoutSeconds $httpTimeoutSeconds
    $carrierExitCode = $LASTEXITCODE
}
finally {
    foreach ($name in $oldValues.Keys) {
        if ($null -eq $oldValues[$name]) { Remove-Item "Env:$name" -ErrorAction SilentlyContinue } else { [Environment]::SetEnvironmentVariable($name,[string]$oldValues[$name],'Process') }
    }
    Remove-BrowserProfiles
}
exit $carrierExitCode
