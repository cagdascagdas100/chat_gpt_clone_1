$ErrorActionPreference = "Stop"

$repoRoot = "C:\Users\cagda\Documents\GitHub\AAYS"
$baselineCsv = Join-Path $repoRoot "security_accuracy_expansion\audit\live_surface_hashes_20260507.csv"

if (-not (Test-Path -LiteralPath $baselineCsv)) {
  throw "Baseline hash CSV bulunamadi: $baselineCsv"
}

$rows = Import-Csv -LiteralPath $baselineCsv
$failed = @()
$report = foreach ($row in $rows) {
  if (-not (Test-Path -LiteralPath $row.path)) {
    $failed += [pscustomobject]@{
      component = $row.component
      path = $row.path
      expected_sha256 = $row.sha256
      actual_sha256 = "MISSING"
      status = "FAIL"
    }
    continue
  }
  $actual = (Get-FileHash -LiteralPath $row.path -Algorithm SHA256).Hash
  $status = if ($actual -eq $row.sha256) { "PASS" } else { "FAIL" }
  if ($status -eq "FAIL") {
    $failed += [pscustomobject]@{
      component = $row.component
      path = $row.path
      expected_sha256 = $row.sha256
      actual_sha256 = $actual
      status = $status
    }
  }
  [pscustomobject]@{
    component = $row.component
    status = $status
    path = $row.path
    expected_sha256 = $row.sha256
    actual_sha256 = $actual
  }
}

$outDir = Join-Path $repoRoot "security_accuracy_expansion\audit"
$timestamp = (Get-Date).ToString("yyyyMMdd_HHmmss")
$outCsv = Join-Path $outDir ("verify_live_modules_" + $timestamp + ".csv")
$report | Export-Csv -NoTypeInformation -Encoding UTF8 -LiteralPath $outCsv

$report | Format-Table -AutoSize
Write-Host ""
Write-Host ("Report: " + $outCsv)

if ($failed.Count -gt 0) {
  Write-Host ""
  Write-Host "OVERALL=FAIL"
  exit 1
}

Write-Host ""
Write-Host "OVERALL=PASS"
exit 0
