$ErrorActionPreference = "Stop"
$RunId = Get-Date -Format "yyyyMMdd_HHmmss"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$BridgeRoot = Split-Path -Parent $ScriptDir
$OutDir = Join-Path $BridgeRoot "ai-runner-outputs\rtsacc_010_all_batch_columns_$RunId"
New-Item -ItemType Directory -Force $OutDir | Out-Null
$RunsRoot = Join-Path $BridgeRoot "ready_to_sell_accuracy_runs"
$LatestRun = $null
if (Test-Path -LiteralPath $RunsRoot) {
  $LatestRun = Get-ChildItem -LiteralPath $RunsRoot -Directory -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1
}
$Columns = New-Object System.Collections.Generic.HashSet[string]
$totalRows = 0
$found = 0
if ($LatestRun) {
  $BatchDir = Join-Path $LatestRun.FullName "batches"
  if (Test-Path -LiteralPath $BatchDir) {
    $files = Get-ChildItem -LiteralPath $BatchDir -Filter "batch_*.csv" -File -ErrorAction SilentlyContinue | Sort-Object Name
    foreach ($f in $files) {
      $rows = Import-Csv -LiteralPath $f.FullName
      $found++
      $totalRows += @($rows).Count
      if (@($rows).Count -gt 0) {
        foreach ($c in $rows[0].PSObject.Properties.Name) { [void]$Columns.Add($c) }
      }
    }
  }
}
$Lines = @("# RTSACC 010 All Batch Columns", "", "Output dir: $OutDir", "Runs root: $RunsRoot", "Latest run: $($LatestRun.FullName)", "Batch files found: $found", "Total rows checked: $totalRows", "", "## Columns")
foreach ($c in ($Columns | Sort-Object)) { $Lines += "- $c" }
$Lines | Set-Content -LiteralPath (Join-Path $OutDir "all_batch_columns.md") -Encoding UTF8
Write-Host "RTSACC_010_OUTPUT=$OutDir"
