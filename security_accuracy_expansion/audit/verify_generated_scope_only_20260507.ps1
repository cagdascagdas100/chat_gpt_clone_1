$ErrorActionPreference = "Continue"
$RepoRoot = "C:\Users\cagda\Documents\GitHub\AAYS"
$AllowedRoot = Join-Path $RepoRoot "security_accuracy_expansion"
$Manifest = Join-Path $AllowedRoot "audit\generated_artifact_manifest_20260507.csv"
Write-Output "VERIFY=generated_scope_only"
Write-Output ("ALLOWED_ROOT=" + $AllowedRoot)
if (-not (Test-Path -LiteralPath $AllowedRoot)) { Write-Output "GENERATED_SCOPE=FAIL missing allowed root"; exit 2 }
$bad = @()
if (Test-Path -LiteralPath $Manifest) {
  $rows = Import-Csv -LiteralPath $Manifest
  foreach ($r in $rows) {
    if (-not $r.relative_path.StartsWith("security_accuracy_expansion/")) { $bad += $r.relative_path }
    $p = Join-Path $RepoRoot ($r.relative_path -replace "/", "\")
    if (-not (Test-Path -LiteralPath $p)) { $bad += ("missing:" + $r.relative_path); continue }
    $h = (Get-FileHash -Algorithm SHA256 -LiteralPath $p).Hash.ToUpperInvariant()
    if ($h -ne $r.sha256.ToUpperInvariant()) { $bad += ("hash:" + $r.relative_path) }
  }
} else {
  Write-Output "MANIFEST=MISSING; checking filesystem scope only"
}
$liveDiff = git diff --name-only -- england_map_web 2>&1 | Out-String
if (-not [string]::IsNullOrWhiteSpace($liveDiff)) { $bad += "live-diff:england_map_web"; Write-Output $liveDiff }
if ($bad.Count -gt 0) { Write-Output "GENERATED_SCOPE=FAIL"; $bad | Write-Output; exit 3 }
Write-Output "GENERATED_SCOPE=PASS"
exit 0