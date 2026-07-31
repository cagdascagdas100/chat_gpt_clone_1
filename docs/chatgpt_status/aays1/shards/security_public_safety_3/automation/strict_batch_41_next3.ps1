$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$slotId = if ($env:AAYS_SLOT_ID) { [string]$env:AAYS_SLOT_ID } else { 'security_public_safety_3' }
$taskId = if ($env:AAYS_TASK_ID) { [string]$env:AAYS_TASK_ID } else { 'security-public-safety-3-next-3-20260731-021' }
$continuationKey = '144fe9f8effb839738eeb578e3d1fed906afc2365b3ee53b38aa97f0bfc004fa'
if ($slotId -ne 'security_public_safety_3') {
    Write-Error "SLOT_ID_MISMATCH:$slotId"
    exit 2
}

$repoRoot = (& git -C $PSScriptRoot rev-parse --show-toplevel 2>$null).Trim()
if (-not $repoRoot) {
    Write-Error 'REPO_ROOT_UNAVAILABLE'
    exit 2
}
$scriptRelative = 'docs/chatgpt_status/aays1/shards/security_public_safety_3/automation/strict_batch_41_next3.py'
$scriptPath = Join-Path $repoRoot $scriptRelative
if (-not (Test-Path -LiteralPath $scriptPath)) {
    Write-Error "WORKER_MISSING:$scriptRelative"
    exit 2
}

$env:AAYS_REPO_ROOT = $repoRoot
$env:AAYS_SLOT_ID = $slotId
$env:AAYS_TASK_ID = $taskId
$env:AAYS_CONTINUATION_KEY = $continuationKey

$python = Get-Command python -ErrorAction SilentlyContinue
if ($python -and $python.Source) {
    & $python.Source $scriptPath
    exit [int]$LASTEXITCODE
}
$py = Get-Command py -ErrorAction SilentlyContinue
if ($py -and $py.Source) {
    & $py.Source -3 $scriptPath
    exit [int]$LASTEXITCODE
}
Write-Error 'PYTHON3_UNAVAILABLE'
exit 2
