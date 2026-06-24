$ErrorActionPreference = "Stop"

$preferred = "F:\AAYS_WORK\internet_access_final_20260616"
$fallback = "D:\AAYS_WORK\internet_access_final_20260616"

$root = if (Test-Path "F:\") { $preferred } elseif (Test-Path "D:\") { $fallback } else { throw "Neither F: nor D: is available." }

$subdirs = @(
  "raw",
  "processed",
  "reports",
  "diagnostics",
  "repo_patch",
  "handoff",
  "logs"
)

foreach ($subdir in $subdirs) {
  New-Item -ItemType Directory -Force -Path (Join-Path $root $subdir) | Out-Null
}

Write-Output "heavy_root=$root"
Write-Output "status=ready"

