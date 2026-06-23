[CmdletBinding()]
param(
  [string]$Worktree = 'F:\chatgpt\AAYS_WORKTREES\aays-runner-v17-icon-work-20260603-232706',
  [string]$Branch = 'aays-runner-v17-icon-work-20260603-232706',
  [string]$Remote = 'origin',
  [string]$PageKey = 'AAYS_REAL_TOPOGRAPHY_PRODUCT'
)
$ErrorActionPreference = 'Continue'
$ts = Get-Date -Format 'yyyyMMdd_HHmmss'
$pageRoot = Join-Path $Worktree "docs\chatgpt_status\$PageKey"
$reportDir = Join-Path $pageRoot 'reports'
New-Item -ItemType Directory -Force -Path $reportDir | Out-Null
$out = Join-Path $reportDir "topography_remote_sync_diagnostic_$ts.txt"
function Run-Git($args) {
  $old = Get-Location
  try { Set-Location $Worktree; $x = & git @args 2>&1; return ($x -join "`n") } finally { Set-Location $old }
}
if (-not (Test-Path $Worktree)) { "WORKTREE_MISSING=$Worktree" | Set-Content $out -Encoding UTF8; exit 1 }
$status = Run-Git @('status','-sb')
$branchNow = Run-Git @('branch','--show-current')
$head = Run-Git @('rev-parse','HEAD')
$remoteHead = Run-Git @('ls-remote','--heads',$Remote,$Branch)
@"
AAYS_TOPOGRAPHY_REMOTE_SYNC_DIAGNOSTIC
PAGE_KEY=$PageKey
REQUESTED_BRANCH=$Branch
CURRENT_BRANCH=$branchNow
HEAD=$head
REMOTE_HEAD=$remoteHead
STATUS_SB=$status
DIAGNOSTIC_ONLY=true
SAFE_NOTE=no push, no force, no merge, no rebase executed
"@ | Set-Content -LiteralPath $out -Encoding UTF8
Write-Host "Wrote $out"
exit 0
