$ErrorActionPreference = "Continue"
$RepoRoot = "C:\Users\cagda\Documents\GitHub\AAYS"
$Baseline = Join-Path $RepoRoot "security_accuracy_expansion\audit\live_surface_hashes_20260507.csv"
$Index = Join-Path $RepoRoot "england_map_web\index.html"
Write-Output "DIAG=live_index_hash_fail"
Write-Output ("REPO_ROOT=" + $RepoRoot)
Write-Output ("INDEX_EXISTS=" + (Test-Path -LiteralPath $Index))
if (Test-Path -LiteralPath $Index) {
  Write-Output ("INDEX_SHA256_ACTUAL=" + (Get-FileHash -Algorithm SHA256 -LiteralPath $Index).Hash)
  Write-Output ("INDEX_LENGTH_BYTES=" + (Get-Item -LiteralPath $Index).Length)
  Write-Output ("INDEX_LAST_WRITE=" + (Get-Item -LiteralPath $Index).LastWriteTime.ToString("s"))
}
Write-Output ("BASELINE_EXISTS=" + (Test-Path -LiteralPath $Baseline))
if (Test-Path -LiteralPath $Baseline) {
  Import-Csv -LiteralPath $Baseline | Where-Object { $_.component -eq "index_html" -or $_.path -like "*index.html" } | Format-List | Out-String | Write-Output
}
Write-Output "ACTION=No file modified; diagnostic only."