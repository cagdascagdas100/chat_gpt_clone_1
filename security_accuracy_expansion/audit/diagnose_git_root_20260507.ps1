$ErrorActionPreference = "Continue"
$RepoRoot = "C:\Users\cagda\Documents\GitHub\AAYS"
Set-Location $RepoRoot
Write-Output "DIAG=git_root"
$root = git rev-parse --show-toplevel 2>&1 | Out-String
Write-Output ("GIT_ROOT=" + $root.Trim())
Write-Output "STATUS_AAYS_SECURITY_ONLY_BEGIN"
git status --short -- security_accuracy_expansion 2>&1 | Out-String | Write-Output
Write-Output "STATUS_AAYS_SECURITY_ONLY_END"
Write-Output "STATUS_LIVE_SURFACE_BEGIN"
git status --short -- england_map_web 2>&1 | Out-String | Write-Output
Write-Output "STATUS_LIVE_SURFACE_END"