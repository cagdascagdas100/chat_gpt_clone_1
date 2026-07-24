[CmdletBinding()]
param(
  [string]$RepoRoot = "C:\AAYS_WT\AAYS_REPAIR_20260706_1738",
  [string]$RunnerPath = "docs\chatgpt_status\_shared\automation\RUN_SINGLE_AAYS_MULTI_PAGE_QUEUE_RUNNER_V5_20260706.ps1"
)

$ErrorActionPreference = "Stop"
$fullPath = Join-Path $RepoRoot $RunnerPath
if (!(Test-Path -LiteralPath $fullPath)) {
  throw "Runner file not found: $fullPath"
}

Set-Location $RepoRoot
$currentBranch = (& git branch --show-current).Trim()
if ([string]::IsNullOrWhiteSpace($currentBranch)) {
  throw "Current git branch could not be resolved."
}

$text = Get-Content -Raw -LiteralPath $fullPath
$text = $text.Replace('& git -C $script:RepoRoot pull --rebase origin main', '& git -C $script:RepoRoot pull --rebase origin $currentBranch')
$text = $text.Replace('& git -C $script:RepoRoot push origin main', '& git -C $script:RepoRoot push origin HEAD:$currentBranch')
Set-Content -LiteralPath $fullPath -Value $text -Encoding UTF8

Write-Output "PATCHED_RUNNER_PUSH_BRANCH=$currentBranch"
Write-Output "PATCHED_FILE=$fullPath"
