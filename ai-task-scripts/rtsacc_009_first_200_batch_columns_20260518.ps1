$ErrorActionPreference = "Stop"
$RunId = Get-Date -Format "yyyyMMdd_HHmmss"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$BridgeRoot = Split-Path -Parent $ScriptDir
$OutDir = Join-Path $BridgeRoot "ai-runner-outputs\rtsacc_009_first_200_batch_columns_$RunId"
New-Item -ItemType Directory -Force $OutDir | Out-Null
$RunsRoot = Join-Path $BridgeRoot "ready_to_sell_accuracy_runs"
$LatestRun = $null
if (Test-Path -LiteralPath $RunsRoot) {
  $LatestRun = Get-ChildItem -LiteralPath $RunsRoot -Directory -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1
}
$Columns = New-Object System.Collections.Generic.HashSet[string]
$totalRows = 0
$found = 0
$missing = 0
if ($LatestRun) {
  for ($i = 1; $i -le 200; $i++) {
    $name = "batch_{0:D4}.csv" -f $i
    $path = Join-Path $LatestRun.FullName ("batches\" + $name)
    if (Test-Path -LiteralPath $path) {
      $rows = Import-Csv -LiteralPath $path
      $found++
      $totalRows += @($rows).Count
      if (@($rows).Count -gt 0) {
        foreach ($c in $rows[0].PSObject.Properties.Name) { [void]$Columns.Add($c) }
      }
    } else {
      $missing++
    }
  }
}
$Lines = @("# RTSACC 009 First 200 Batch Columns", "", "Output dir: $OutDir", "Runs root: $RunsRoot", "Latest run: $($LatestRun.FullName)", "", "Batch files found: $found", "Batch files missing: $missing", "Total rows checked: $totalRows", "", "## Columns")
foreach ($c in ($Columns | Sort-Object)) { $Lines += "- $c" }
$Lines | Set-Content -LiteralPath (Join-Path $OutDir "first_200_batch_columns.md") -Encoding UTF8
Write-Host "RTSACC_009_OUTPUT=$OutDir"
