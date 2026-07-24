Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$TaskId = 'ready_to_sell_1_automation_167_dom_proof_20260720_01'
$SlotId = 'ready_to_sell_1'
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..\..')).Path
$WorkerPath = Join-Path $RepoRoot 'docs\chatgpt_status\aays1\automation\ready_to_sell_1_automation_167_dom_proof_v11.py'

if (-not (Test-Path -LiteralPath $WorkerPath -PathType Leaf)) {
    throw "WORKER_NOT_FOUND:$WorkerPath"
}

$env:AAYS_TASK_ID = $TaskId
$env:AAYS_SLOT_ID = $SlotId
$pythonCandidates = @(
    @{ Command = 'py'; Arguments = @('-3') },
    @{ Command = 'python'; Arguments = @() },
    @{ Command = 'python3'; Arguments = @() }
)

$selected = $null
foreach ($candidate in $pythonCandidates) {
    if (Get-Command $candidate.Command -ErrorAction SilentlyContinue) {
        $selected = $candidate
        break
    }
}

if ($null -eq $selected) {
    throw 'PYTHON_RUNTIME_NOT_FOUND'
}

Push-Location $RepoRoot
try {
    & $selected.Command @($selected.Arguments) $WorkerPath
    if ($LASTEXITCODE -ne 0) {
        throw "READY_TO_SELL_1_AUTOMATION_167_V11_FAILED_EXIT_$LASTEXITCODE"
    }
}
finally {
    Pop-Location
}
