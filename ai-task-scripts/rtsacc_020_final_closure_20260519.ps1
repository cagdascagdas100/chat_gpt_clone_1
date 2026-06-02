$ErrorActionPreference = "Stop"
$RunId = Get-Date -Format "yyyyMMdd_HHmmss"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$BridgeRoot = Split-Path -Parent $ScriptDir
$OutDir = Join-Path $BridgeRoot "ai-runner-outputs\rtsacc_020_final_closure_$RunId"
New-Item -ItemType Directory -Force $OutDir | Out-Null
$Lines = @()
$Lines += "# RTSACC 020 Final Closure"
$Lines += ""
$Lines += "Mode: read-only closure. No DB write. No production acceptance."
$Lines += "Output dir: $OutDir"
$Lines += ""
$Lines += "## Completed chain"
$Lines += "- RTSACC visible smoke/count/index/final handoff tasks completed through 019."
$Lines += "- Runner is operational."
$Lines += "- Further production work requires a new explicit task."
$Lines += ""
$Lines += "## Folder counts"
foreach ($name in @("ai-results", "ai-heartbeat", "ai-runner-outputs", "ready_to_sell_accuracy_runs")) {
  $dir = Join-Path $BridgeRoot $name
  $exists = Test-Path -LiteralPath $dir
  $count = 0
  if ($exists) { $count = @(Get-ChildItem -LiteralPath $dir -Recurse -File -ErrorAction SilentlyContinue).Count }
  $Lines += "- $name exists=$exists files=$count"
}
$Lines | Set-Content -LiteralPath (Join-Path $OutDir "rtsacc_final_closure.md") -Encoding UTF8
Write-Host "RTSACC_020_OUTPUT=$OutDir"
