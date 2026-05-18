$ErrorActionPreference = "Stop"
$RunId = Get-Date -Format "yyyyMMdd_HHmmss"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$BridgeRoot = Split-Path -Parent $ScriptDir
$OutDir = Join-Path $BridgeRoot "ai-runner-outputs\rtsacc_006_first_50_batch_count_$RunId"
New-Item -ItemType Directory -Force $OutDir | Out-Null
$RunsRoot = Join-Path $BridgeRoot "ready_to_sell_accuracy_runs"
$LatestRun = $null
if (Test-Path -LiteralPath $RunsRoot) {
  $LatestRun = Get-ChildItem -LiteralPath $RunsRoot -Directory -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1
}
$Lines = @("# RTSACC 006 First 50 Batch Count", "", "Output dir: $OutDir", "Runs root: $RunsRoot", "Latest run: $($LatestRun.FullName)", "")
$totalRows = 0
$found = 0
$missing = 0
if ($LatestRun) {
  for ($i = 1; $i -le 50; $i++) {
    $name = "batch_{0:D4}.csv" -f $i
    $path = Join-Path $LatestRun.FullName ("batches\" + $name)
    if (Test-Path -LiteralPath $path) {
      $rows = Import-Csv -LiteralPath $path
      $count = @($rows).Count
      $totalRows += $count
      $found++
      $Lines += "- $name rows=$count"
    } else {
      $missing++
      $Lines += "- $name missing"
    }
  }
} else {
  $Lines += "No run folder found."
}
$Lines += ""
$Lines += "Batch files found: $found"
$Lines += "Batch files missing: $missing"
$Lines += "Total rows checked: $totalRows"
$Lines | Set-Content -LiteralPath (Join-Path $OutDir "first_50_batch_count.md") -Encoding UTF8
Write-Host "RTSACC_006_OUTPUT=$OutDir"
