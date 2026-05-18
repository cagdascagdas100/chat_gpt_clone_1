$ErrorActionPreference = "Stop"
$RunId = Get-Date -Format "yyyyMMdd_HHmmss"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$BridgeRoot = Split-Path -Parent $ScriptDir
$OutDir = Join-Path $BridgeRoot "ai-runner-outputs\rtsacc_013_results_index_$RunId"
New-Item -ItemType Directory -Force $OutDir | Out-Null
$Targets = @("ai-results", "ai-heartbeat", "ready_to_sell_accuracy_runs")
$Lines = @("# RTSACC 013 Results Index", "", "Output dir: $OutDir", "")
foreach ($t in $Targets) {
  $dir = Join-Path $BridgeRoot $t
  $Lines += "## $t"
  $Lines += "Path: $dir"
  $Lines += "Exists: $(Test-Path -LiteralPath $dir)"
  if (Test-Path -LiteralPath $dir) {
    $files = Get-ChildItem -LiteralPath $dir -Recurse -File -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 80
    foreach ($f in $files) { $Lines += "- $($f.FullName) size=$($f.Length) updated=$($f.LastWriteTime.ToString('s'))" }
  }
  $Lines += ""
}
$Lines | Set-Content -LiteralPath (Join-Path $OutDir "rtsacc_results_index.md") -Encoding UTF8
Write-Host "RTSACC_013_OUTPUT=$OutDir"
