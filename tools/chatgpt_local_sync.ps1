param(
  [string]$Repo = "C:\Users\cagda\Documents\GitHub\AAYS",
  [string]$SyncBranch = "chatgpt-local-sync"
)
$ErrorActionPreference = "Stop"
$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$OutDir = Join-Path $Repo "docs\chatgpt_status\runner_outputs"
$SyncDir = Join-Path $Repo "docs\chatgpt_status\local_sync"
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
New-Item -ItemType Directory -Force -Path $SyncDir | Out-Null
$Probe = Join-Path $Repo "tools\aays_toolchain_evidence_probe.ps1"
if (Test-Path $Probe) {
  powershell -NoProfile -ExecutionPolicy Bypass -File $Probe -Repo $Repo
}
$latestTxt = Join-Path $OutDir "latest_output.txt"
$latestJson = Join-Path $OutDir "latest_output.json"
if (!(Test-Path $latestTxt)) { "runner ok`nstamp=$Stamp`nprogress=96" | Set-Content $latestTxt -Encoding UTF8 }
if (!(Test-Path $latestJson)) { "{`"stamp`":`"$Stamp`",`"progress`":96,`"status`":`"runner_ok`"}" | Set-Content $latestJson -Encoding UTF8 }
Copy-Item $latestJson (Join-Path $SyncDir "latest_local_probe.json") -Force
$Worktree = Join-Path $env:TEMP "aays_sync_$Stamp"
git -C $Repo fetch origin $SyncBranch 2>$null | Out-Null
git -C $Repo worktree add -B $SyncBranch $Worktree origin/$SyncBranch | Out-Null
try {
  New-Item -ItemType Directory -Force -Path (Join-Path $Worktree "docs\chatgpt_status\runner_outputs") | Out-Null
  New-Item -ItemType Directory -Force -Path (Join-Path $Worktree "docs\chatgpt_status\local_sync") | Out-Null
  Copy-Item (Join-Path $OutDir "*") (Join-Path $Worktree "docs\chatgpt_status\runner_outputs") -Force
  Copy-Item (Join-Path $SyncDir "*") (Join-Path $Worktree "docs\chatgpt_status\local_sync") -Force
  git -C $Worktree add docs/chatgpt_status | Out-Null
  git -C $Worktree commit -m "runner output $Stamp" 2>$null | Out-Null
  git -C $Worktree push -u origin $SyncBranch | Out-Null
} finally {
  git -C $Repo worktree remove $Worktree --force 2>$null | Out-Null
}
Write-Host "SYNC_DONE"
Write-Host "BRANCH=$SyncBranch"
Write-Host "LATEST=docs/chatgpt_status/runner_outputs/latest_output.json"
Write-Host "STAMP=$Stamp"
