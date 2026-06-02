$ErrorActionPreference = "Stop"
$RunId = Get-Date -Format "yyyyMMdd_HHmmss"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$BridgeRoot = Split-Path -Parent $ScriptDir
$OutDir = Join-Path $BridgeRoot "ai-runner-outputs\rtsacc_018_final_decision_report_$RunId"
New-Item -ItemType Directory -Force $OutDir | Out-Null
$Lines = @()
$Lines += "# RTSACC 018 Final Decision Report"
$Lines += ""
$Lines += "Mode: read-only decision report. No DB write. No production acceptance."
$Lines += "Output dir: $OutDir"
$Lines += ""
$Lines += "## Decision"
$Lines += "- Runner protocol is working."
$Lines += "- RTSACC batch/output indexing chain has completed through 017."
$Lines += "- Next production-affecting work must be a separate task with explicit approval."
$Lines += ""
$Lines += "## Evidence folders"
$Targets = @("ai-results", "ai-heartbeat", "ready_to_sell_accuracy_runs", "ai-runner-outputs")
foreach ($t in $Targets) {
  $dir = Join-Path $BridgeRoot $t
  $Lines += "### $t"
  $Lines += "Exists: $(Test-Path -LiteralPath $dir)"
  if (Test-Path -LiteralPath $dir) {
    $count = @(Get-ChildItem -LiteralPath $dir -Recurse -File -ErrorAction SilentlyContinue).Count
    $Lines += "File count: $count"
  }
  $Lines += ""
}
$Lines | Set-Content -LiteralPath (Join-Path $OutDir "rtsacc_final_decision_report.md") -Encoding UTF8
Write-Host "RTSACC_018_OUTPUT=$OutDir"
