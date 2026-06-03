$ErrorActionPreference = "Stop"
$RunId = Get-Date -Format "yyyyMMdd_HHmmss"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$BridgeRoot = Split-Path -Parent $ScriptDir
$OutDir = Join-Path $BridgeRoot "ai-runner-outputs\rtsacc_015_final_summary_$RunId"
New-Item -ItemType Directory -Force $OutDir | Out-Null
$Lines = @()
$Lines += "# RTSACC 015 Final Summary Handoff"
$Lines += ""
$Lines += "Output dir: $OutDir"
$Lines += "Mode: read-only summary; no DB write; no production acceptance."
$Lines += ""
$Targets = @("ai-results", "ai-heartbeat", "ready_to_sell_accuracy_runs", "ai-runner-outputs")
foreach ($t in $Targets) {
  $dir = Join-Path $BridgeRoot $t
  $Lines += "## $t"
  $Lines += "Exists: $(Test-Path -LiteralPath $dir)"
  if (Test-Path -LiteralPath $dir) {
    $files = Get-ChildItem -LiteralPath $dir -Recurse -File -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 40
    foreach ($f in $files) { $Lines += "- $($f.FullName) size=$($f.Length) updated=$($f.LastWriteTime.ToString('s'))" }
  }
  $Lines += ""
}
$Lines | Set-Content -LiteralPath (Join-Path $OutDir "rtsacc_final_summary_handoff.md") -Encoding UTF8
Write-Host "RTSACC_015_OUTPUT=$OutDir"
