[CmdletBinding()]
param(
  [string]$RepoRoot = "C:\AAYS_WT\AAYS_REPAIR_20260706_1738"
)

$ErrorActionPreference = "Stop"

$runnerPath = Join-Path $RepoRoot "docs\chatgpt_status\_shared\automation\RUN_SINGLE_AAYS_MULTI_PAGE_QUEUE_RUNNER_V5_20260706.ps1"
if (-not (Test-Path -LiteralPath $runnerPath)) {
  throw "Runner V5 script not found: $runnerPath"
}

$content = Get-Content -Raw -LiteralPath $runnerPath

$oldPull = '& git -C $script:RepoRoot pull --rebase origin main'
$newPull = @'
  $currentBranch = (& git -C $script:RepoRoot branch --show-current 2>&1 | Out-String).Trim()
  if ([string]::IsNullOrWhiteSpace($currentBranch)) {
    $currentBranch = (& git -C $script:RepoRoot rev-parse --abbrev-ref HEAD 2>&1 | Out-String).Trim()
  }
  if ([string]::IsNullOrWhiteSpace($currentBranch) -or $currentBranch -eq "HEAD") {
    return [pscustomobject]@{ push_ok = $false; post_sync_ok = $false; message = "current branch unavailable" }
  }
  & git -C $script:RepoRoot pull --rebase origin $currentBranch
'@

$oldPush = '& git -C $script:RepoRoot push origin main'
$newPush = '  & git -C $script:RepoRoot push origin $currentBranch'

if ($content -notlike "*$oldPull*" -or $content -notlike "*$oldPush*") {
  throw "Expected origin main pull/push lines were not found; runner may already be patched or changed."
}

$content = $content.Replace($oldPull, $newPull.TrimEnd())
$content = $content.Replace($oldPush, $newPush)

Set-Content -LiteralPath $runnerPath -Value $content -Encoding UTF8

$verify = Get-Content -Raw -LiteralPath $runnerPath
if ($verify -match 'pull --rebase origin main' -or $verify -match 'push origin main') {
  throw "Patch verification failed: origin main push/pull still present."
}
if ($verify -notmatch 'branch --show-current' -or $verify -notmatch 'push origin \$currentBranch') {
  throw "Patch verification failed: current branch push logic missing."
}

Write-Output "PATCH_APPLIED runner_v5_current_branch_push_safe=true path=$runnerPath"
