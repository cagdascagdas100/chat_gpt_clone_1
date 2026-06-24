param(
  [string]$Worktree = 'F:\chatgpt\AAYS_WORKTREES\aays-runner-v17-icon-work-20260603-232706',
  [string]$Branch = 'aays-runner-v17-icon-work-20260603-232706',
  [string]$PageKey = 'AAYS_REAL_TOPOGRAPHY_PRODUCT'
)

$ErrorActionPreference = 'Continue'
$PageRoot = Join-Path $Worktree "docs\chatgpt_status\$PageKey"
$Reports = Join-Path $PageRoot 'reports'
New-Item -ItemType Directory -Force -Path $Reports | Out-Null
$Stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$Out = Join-Path $Reports "chatgpt_remote_sync_diagnostic_$Stamp.txt"

function Add-Line([string]$Line) {
  Add-Content -Encoding UTF8 -Path $Out -Value $Line
}

'' | Set-Content -Encoding UTF8 $Out
Add-Line "PAGE_KEY=$PageKey"
Add-Line "WORKTREE=$Worktree"
Add-Line "BRANCH=$Branch"

try {
  $current = git -C $Worktree branch --show-current
  Add-Line "CURRENT_BRANCH=$current"
} catch {
  Add-Line "CURRENT_BRANCH=FAIL"
}

try {
  git -C $Worktree fetch origin $Branch 2>&1 | ForEach-Object { Add-Line "FETCH=$_"}
} catch {
  Add-Line "FETCH_ERROR=$($_.Exception.Message)"
}

try {
  $local = git -C $Worktree rev-parse HEAD
  Add-Line "LOCAL_HEAD=$local"
} catch {
  Add-Line "LOCAL_HEAD=FAIL"
}

try {
  $remote = git -C $Worktree rev-parse "origin/$Branch"
  Add-Line "REMOTE_HEAD=$remote"
} catch {
  Add-Line "REMOTE_HEAD=FAIL"
}

try {
  git -C $Worktree status --short | ForEach-Object { Add-Line "STATUS=$_"}
} catch {
  Add-Line "STATUS_ERROR=$($_.Exception.Message)"
}

try {
  git -C $Worktree log --oneline --decorate -5 | ForEach-Object { Add-Line "LOG=$_"}
} catch {
  Add-Line "LOG_ERROR=$($_.Exception.Message)"
}

Add-Line "SAFE_NEXT_STEP=If dirty worktree or non-fast-forward exists, do not auto-push. Resolve divergence first."
Write-Host "WROTE=$Out"
