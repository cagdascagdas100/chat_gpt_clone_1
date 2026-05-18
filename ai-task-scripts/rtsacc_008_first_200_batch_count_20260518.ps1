$ErrorActionPreference = "Stop"
$RunId = Get-Date -Format "yyyyMMdd_HHmmss"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$BridgeRoot = Split-Path -Parent $ScriptDir
$OutDir = Join-Path $BridgeRoot "ai-runner-outputs\rtsacc_008_first_200_batch_count_$RunId"
New-Item -ItemType Directory -Force $OutDir | Out-Null
$RunsRoot = Join-Path $BridgeRoot "ready_to_sell_accuracy_runs"
$LatestRun = $null
if (Test-Path -LiteralPath $RunsRoot) {
  $LatestRun = Get-ChildItem -LiteralPath $RunsRoot -Directory -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1
}
$Lines = @("# RTSACC 008 First 200 Batch Count", "", "Output dir: $OutDir", "Runs root: $RunsRoot", "Latest run: $($LatestRun.FullName)", "")
$totalRows = 0
$found = 0
$missing = 0
if ($LatestRun) {
  for ($i = 1; $i -le 200; $i++) {
    $name = "batch_{0:D4}.csv" -f $i
    $path = Join-Path $LatestRun.FullName ("batches\" + $name)
    if (Test-Path -LiteralPath $path) {
      $rows = Import-Csv -LiteralPath $path
      $count = @($rows).Count
      $totalRows += $count
      $found++
    } else {
      $missing++
    }
  }
} else {
  $Lines += "No run folder found."
}
$Lines += "Batch files found: $found"
$Lines += "Batch files missing: $missing"
$Lines += "Total rows checked: $totalRows"
$Lines | Set-Content -LiteralPath (Join-Path $OutDir "first_200_batch_count.md") -Encoding UTF8
Write-Host "RTSACC_008_OUTPUT=$OutDir"
