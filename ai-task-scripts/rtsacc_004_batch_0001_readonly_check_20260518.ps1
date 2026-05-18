$ErrorActionPreference = "Stop"
$RunId = Get-Date -Format "yyyyMMdd_HHmmss"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$BridgeRoot = Split-Path -Parent $ScriptDir
$OutDir = Join-Path $BridgeRoot "ai-runner-outputs\rtsacc_004_batch_0001_check_$RunId"
New-Item -ItemType Directory -Force $OutDir | Out-Null
$RunsRoot = Join-Path $BridgeRoot "ready_to_sell_accuracy_runs"
$LatestRun = $null
if (Test-Path -LiteralPath $RunsRoot) {
  $LatestRun = Get-ChildItem -LiteralPath $RunsRoot -Directory -ErrorAction SilentlyContinue |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 1
}
$BatchPath = $null
if ($LatestRun) {
  $Candidate = Join-Path $LatestRun.FullName "batches\batch_0001.csv"
  if (Test-Path -LiteralPath $Candidate) { $BatchPath = $Candidate }
}
$Lines = @()
$Lines += "# RTSACC 004 Batch 0001 Readonly Check"
$Lines += ""
$Lines += "Output dir: $OutDir"
$Lines += "Runs root: $RunsRoot"
$Lines += "Latest run: $($LatestRun.FullName)"
$Lines += "Batch path: $BatchPath"
$Lines += ""
if ($BatchPath) {
  $Rows = Import-Csv -LiteralPath $BatchPath
  $Lines += "Rows: $(@($Rows).Count)"
  if (@($Rows).Count -gt 0) {
    $Columns = $Rows[0].PSObject.Properties.Name
    $Lines += "Columns: $($Columns -join ', ')"
  }
} else {
  $Lines += "Batch not found."
}
$Lines | Set-Content -LiteralPath (Join-Path $OutDir "batch_0001_readonly_check.md") -Encoding UTF8
Write-Host "RTSACC_004_OUTPUT=$OutDir"
