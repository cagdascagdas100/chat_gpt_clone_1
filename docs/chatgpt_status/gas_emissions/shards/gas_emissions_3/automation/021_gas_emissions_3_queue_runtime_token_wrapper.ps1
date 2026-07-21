[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$slotId = 'gas_emissions_3'
$branch = 'codex/aays-single-runner-v5-20260706'
$repoRoot = (Get-Location).Path.TrimEnd('\')
$portableRoot = [string]$env:AAYS_PORTABLE_ROOT
$wrapperRelative = 'docs/chatgpt_status/gas_emissions/shards/gas_emissions_3/automation/021_gas_emissions_3_queue_runtime_token_wrapper.ps1'
$carrierRelative = 'docs/chatgpt_status/gas_emissions/shards/gas_emissions_3/automation/020_gas_emissions_3_coordinator_browser_acceptance_carrier.ps1'
$harnessRelative = 'england_map_web/data/aays_18_slots/gas_emissions_3/canonical_matrix_100_browser_harness.html'
$carrierPath = Join-Path $repoRoot ($carrierRelative.Replace('/','\'))
$runtimeProofRoot = Join-Path $repoRoot 'docs\chatgpt_status\gas_emissions\shards\gas_emissions_3\acceptance\020_coordinator_browser_runtime_latest'
$tokenUrl = 'http://127.0.0.1:8012/england_map_web/data/aays_18_slots/gas_emissions_3/runner_runtime_token_latest.json'
$expectedTokenId = 'gas_emissions_3_v7_queue_20260721_001'
$expectedTaskId = 'gas_emissions_3_coordinator_browser_acceptance_v7_20260721_01'

$gitCandidates = @()
if (-not [string]::IsNullOrWhiteSpace($portableRoot)) {
    $gitCandidates += (Join-Path $portableRoot 'runtime\git\cmd\git.exe')
    $gitCandidates += (Join-Path $portableRoot 'runtime\git\bin\git.exe')
}
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

function Get-RemoteHead {
    $raw = Invoke-Git @('ls-remote','origin',"refs/heads/$branch")
    if ([string]::IsNullOrWhiteSpace($raw)) { throw "Remote branch not found: $branch" }
    return ($raw -split '\s+')[0]
}

function Remove-BrowserProfiles {
    foreach ($name in @('profile_precheck','profile_matrix','profile_screenshot')) {
        $path = Join-Path $runtimeProofRoot $name
        Remove-Item -Recurse -Force -LiteralPath $path -ErrorAction SilentlyContinue
    }
}

if ([string]$env:AAYS_SLOT_ID -ne $slotId) { throw "AAYS_SLOT_ID mismatch: $env:AAYS_SLOT_ID" }
if ([string]$env:AAYS_CHILD_DIRECT_PUSH_FORBIDDEN -ne 'true') { throw 'Coordinator child direct-push guard is not active.' }
if (-not (Test-Path -LiteralPath $carrierPath -PathType Leaf)) { throw "Carrier missing: $carrierPath" }

$localHead = Invoke-Git @('rev-parse','HEAD')
$remoteHead = Get-RemoteHead
if ($localHead -ne $remoteHead) { throw "Detached child HEAD does not match remote HEAD. local=$localHead remote=$remoteHead" }
$wrapperBlob = Invoke-Git @('rev-parse',"HEAD:$wrapperRelative")
$carrierBlob = Invoke-Git @('rev-parse',"HEAD:$carrierRelative")
$harnessBlob = Invoke-Git @('rev-parse',"HEAD:$harnessRelative")

$response = Invoke-WebRequest -Uri $tokenUrl -UseBasicParsing -TimeoutSec 30 -Headers @{'Cache-Control'='no-cache'}
if ([int]$response.StatusCode -ne 200) { throw "Runtime token HTTP status is $($response.StatusCode)" }
$token = [string]$response.Content | ConvertFrom-Json
if ($token.slot_id -ne $slotId) { throw "Runtime token slot mismatch: $($token.slot_id)" }
if ($token.token_id -ne $expectedTokenId) { throw "Runtime token id mismatch: $($token.token_id)" }
if ($token.task_id -ne $expectedTaskId) { throw "Runtime token task mismatch: $($token.task_id)" }
if ($token.wrapper_path -ne $wrapperRelative) { throw "Runtime token wrapper path mismatch: $($token.wrapper_path)" }
if ($token.wrapper_blob_sha -ne $wrapperBlob) { throw "Served runtime token wrapper SHA mismatch. token=$($token.wrapper_blob_sha) local=$wrapperBlob" }
if ($token.carrier_path -ne $carrierRelative) { throw "Runtime token carrier path mismatch: $($token.carrier_path)" }
if ($token.carrier_blob_sha -ne $carrierBlob) { throw "Served runtime token carrier SHA mismatch. token=$($token.carrier_blob_sha) local=$carrierBlob" }
if ($token.harness_path -ne $harnessRelative) { throw "Runtime token harness path mismatch: $($token.harness_path)" }
if ($token.harness_blob_sha -ne $harnessBlob) { throw "Served runtime token harness SHA mismatch. token=$($token.harness_blob_sha) local=$harnessBlob" }
if ($token.final_ready -ne $false -or $token.fake_data -ne $false -or $token.db_write -ne $false -or $token.migration -ne $false -or $token.production_deploy -ne $false) {
    throw 'Runtime token safety flags are invalid.'
}

Write-Output "GAS_EMISSIONS_3_RUNTIME_TOKEN_PASS token=$expectedTokenId local=$localHead remote=$remoteHead git=$gitExe wrapper=$wrapperBlob carrier=$carrierBlob harness=$harnessBlob"
$carrierExitCode = 1
try {
    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $carrierPath
    $carrierExitCode = $LASTEXITCODE
}
finally {
    Remove-BrowserProfiles
}
exit $carrierExitCode
