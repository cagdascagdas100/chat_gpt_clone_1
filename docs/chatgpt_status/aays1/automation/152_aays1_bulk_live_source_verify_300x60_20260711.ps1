$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$repoRoot = if ($env:AAYS_REPO_ROOT) { $env:AAYS_REPO_ROOT } else { (& git rev-parse --show-toplevel 2>$null).Trim() }
$baseRelative = 'docs/chatgpt_status/aays1/automation/149_aays1_bulk_live_source_verify_120x25_20260711.ps1'
$basePath = Join-Path $repoRoot $baseRelative
$tempRelative = 'docs/chatgpt_status/aays1/runner_outputs/152_generated_bulk_live_source_verify_300x60.ps1'
$tempPath = Join-Path $repoRoot $tempRelative
$logRelative = 'docs/chatgpt_status/aays1/runner_outputs/152_bulk_live_source_verify_300x60.log'
$logPath = Join-Path $repoRoot $logRelative
$expectedRelative = 'docs/chatgpt_status/aays1/status/152_aays1_bulk_live_source_verify_300x60_latest.json'
$expectedPath = Join-Path $repoRoot $expectedRelative

function Replace-Once([string]$text, [string]$pattern, [string]$replacement, [string]$failureCode) {
  $regex = [regex]::new($pattern, [System.Text.RegularExpressions.RegexOptions]::Multiline -bor [System.Text.RegularExpressions.RegexOptions]::IgnoreCase)
  if (-not $regex.IsMatch($text)) { throw $failureCode }
  return $regex.Replace($text,$replacement,1)
}

if (-not (Test-Path -LiteralPath $basePath)) { throw "Base automation missing: $baseRelative" }
New-Item -ItemType Directory -Force -Path (Split-Path $tempPath),(Split-Path $logPath),(Split-Path $expectedPath) | Out-Null
$template = (Get-Content -LiteralPath $basePath -Raw -Encoding UTF8) -replace "`r`n","`n"
$replacements = [ordered]@{
  'aays1-ready-to-sell-bulk-live-source-verify-120x25-20260711' = 'aays1-ready-to-sell-bulk-live-source-verify-300x60-20260711'
  '$maxCandidates = 120' = '$maxCandidates = 300'
  '$maxVerified = 25' = '$maxVerified = 60'
  '149_bulk_live_verify_20260711' = '152_bulk_live_verify_300x60_20260711'
  '149_aays1_bulk_live_source_verify_latest.json' = '152_aays1_bulk_live_source_verify_300x60_latest.json'
  '149_aays1_bulk_live_source_verify_report.md' = '152_aays1_bulk_live_source_verify_300x60_report.md'
  'ReadyToSell Bulk Live Source Verification 120x25' = 'ReadyToSell Bulk Live Source Verification 300x60'
  'Bulk verify ReadyToSell live source rows' = 'Bulk verify ReadyToSell live source rows 300x60'
  'Record ReadyToSell bulk source verification proof' = 'Record ReadyToSell bulk source verification 300x60 proof'
}
foreach ($entry in $replacements.GetEnumerator()) { $template = $template.Replace([string]$entry.Key,[string]$entry.Value) }

if ($template -notmatch '\$detachedCanonical') {
  $branchPattern = '^\s*\$branch\s*=\s*\(&\s*git\s+-C\s+\$repoRoot\s+rev-parse\s+--abbrev-ref\s+HEAD\s+2>\$null\)\.Trim\(\)\s*\n\s*if\s*\(\$branch\s+-ne\s+\$targetBranch\)\s*\{\s*\$blockers\.Add\("wrong_branch:\$branch"\)\s*\}'
  $branchReplacement = '$branch = (& git -C $repoRoot rev-parse --abbrev-ref HEAD 2>$null).Trim()' + "`n" + '$detachedCanonical = ($branch -eq ''HEAD'' -and $env:AAYS_CANONICAL_DETACHED_WORKTREE -eq ''true'')' + "`n" + 'if ($branch -ne $targetBranch -and -not $detachedCanonical) { $blockers.Add("wrong_branch:$branch") }'
  $template = Replace-Once $template $branchPattern $branchReplacement '152_detached_branch_guard_not_found'
}

$blockedPattern = '^\s*\$blocked\s*=\s*\$plain\s+-match\s+''[^''\r\n]*''\s*$'
$blockedReplacement = '$titleSignal = (-not [string]::IsNullOrWhiteSpace([string]$title)) -and ($title -match ''(?i)(land for sale|plot for sale|development land|building plot|development site|agricultural land)'')' + "`n" + '$challengeSignal = (($title -match ''(?i)(captcha|access denied|cloudflare|verify you are human)'') -or ($plain -match ''(?i)(captcha|access denied|unusual traffic|verify you are human)''))'
$template = Replace-Once $template $blockedPattern $blockedReplacement '152_blocked_signal_line_not_found'
$landPattern = '^\s*\$landSignal\s*=\s*\$plain\s+-match\s+''[^''\r\n]*''\s*$'
$landReplacement = '$bodySignal = $plain -match ''(?i)(land for sale|plot for sale|development land|building plot|building plots|development site|agricultural land|parcel of land)''' + "`n" + '$landSignal = ($titleSignal -or $bodySignal)' + "`n" + '$blocked = ($challengeSignal -and -not $titleSignal)'
$template = Replace-Once $template $landPattern $landReplacement '152_land_signal_line_not_found'

# Child scripts must never own commit/push in a detached shared-runner worktree.
$workGitPattern = '(?s)\$workPushStatus\s*=\s*''not_attempted''.*?(?=\$afterVerified\s*=)'
$template = Replace-Once $template $workGitPattern ('$workPushStatus = ''outer_runner_promotion''; $workCommit = $null' + "`n") '152_work_git_block_not_found'
$proofGitPattern = '(?s)\ntry\s*\{\s*\n\s*& git -C \$repoRoot add -- \$statusRelative.*\z'
$template = Replace-Once $template $proofGitPattern ("`n# Outer canonical runner owns status/report commit, push and remote readback.`n") '152_proof_git_block_not_found'

[System.IO.File]::WriteAllText($tempPath,$template,[System.Text.UTF8Encoding]::new($true))
"[$([DateTimeOffset]::UtcNow.ToString('o'))] START $tempRelative" | Set-Content -LiteralPath $logPath -Encoding UTF8
$previousDetached = $env:AAYS_CANONICAL_DETACHED_WORKTREE
try {
  $env:AAYS_CANONICAL_DETACHED_WORKTREE = 'true'
  & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $tempPath *>> $logPath
  $exitCode = $LASTEXITCODE
  if ($null -eq $exitCode) { $exitCode = 0 }
  if (-not (Test-Path -LiteralPath $expectedPath)) { throw "Expected real output missing after child exit ${exitCode}: $expectedRelative; log=$logRelative" }
  if ($exitCode -ne 0) { "Child returned $exitCode but expected status exists; outer runner will judge real before/after progress." | Add-Content -LiteralPath $logPath -Encoding UTF8 }
  exit 0
} finally {
  $env:AAYS_CANONICAL_DETACHED_WORKTREE = $previousDetached
}
