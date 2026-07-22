$ErrorActionPreference = 'Stop'
$repoRoot = if ($env:AAYS_REPO_ROOT) { $env:AAYS_REPO_ROOT } else { (Resolve-Path (Join-Path $PSScriptRoot '..\..\..\..')).Path }
$scriptPath = Join-Path $repoRoot 'docs\chatgpt_status\aays1\automation\ready_to_sell_1_automation_167_dom_proof_v28.py'
if (-not (Test-Path -LiteralPath $scriptPath)) { throw "V28 script not found: $scriptPath" }
Push-Location $repoRoot
try {
    & python $scriptPath
    exit $LASTEXITCODE
}
finally {
    Pop-Location
}
