$RunId = Get-Date -Format "yyyyMMdd_HHmmss"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$BridgeRoot = Split-Path -Parent $ScriptDir
$OutDir = Join-Path $BridgeRoot "ai-runner-outputs\rtsacc_003_batch_verify_$RunId"
New-Item -ItemType Directory -Force $OutDir | Out-Null
$RunRoot = Join-Path $BridgeRoot "ready_to_sell_accuracy_runs"
$Report = @()
$Report += "# RTSACC 003 Batch Verification"
$Report += ""
$Report += "Output dir: $OutDir"
$Report += "Run root: $RunRoot"
$Report += ""
$batchFiles = @()
if (Test-Path -LiteralPath $RunRoot) {
  $batchFiles = @(Get-ChildItem -LiteralPath $RunRoot -Recurse -File -Filter "batch_*.csv" -ErrorAction SilentlyContinue | Select-Object -First 250)
}
$Report += "Batch files found: $($batchFiles.Count)"
$totalRows = 0
foreach ($f in $batchFiles) {
  try {
    $count = @(Import-Csv -LiteralPath $f.FullName).Count
    $totalRows += $count
    $Report += "- $($f.FullName) rows=$count"
  } catch {
    $Report += "- $($f.FullName) error=$($_.Exception.Message)"
  }
}
$Report += ""
$Report += "Total sampled rows: $totalRows"
$Report | Set-Content -LiteralPath (Join-Path $OutDir "rtsacc_003_batch_verify_report.md") -Encoding UTF8
Write-Host "RTSACC_003_OUTPUT=$OutDir"
