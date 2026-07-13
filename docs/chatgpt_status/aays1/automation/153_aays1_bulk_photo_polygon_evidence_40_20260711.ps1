$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$repoRoot = if ($env:AAYS_REPO_ROOT) { $env:AAYS_REPO_ROOT } else { (& git rev-parse --show-toplevel 2>$null).Trim() }
$baseRelative = 'docs/chatgpt_status/aays1/automation/150_aays1_bulk_photo_polygon_evidence_20_20260711.ps1'
$basePath = Join-Path $repoRoot $baseRelative
$tempRelative = 'docs/chatgpt_status/aays1/runner_outputs/153_generated_bulk_photo_polygon_evidence_40.ps1'
$tempPath = Join-Path $repoRoot $tempRelative
$logRelative = 'docs/chatgpt_status/aays1/runner_outputs/153_bulk_photo_polygon_evidence_40.log'
$logPath = Join-Path $repoRoot $logRelative
$expectedRelative = 'docs/chatgpt_status/aays1/status/153_aays1_bulk_photo_polygon_evidence_40_latest.json'
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
  'aays1-ready-to-sell-bulk-photo-polygon-evidence-20-20260711' = 'aays1-ready-to-sell-bulk-photo-polygon-evidence-40-20260711'
  '$maxRows = 20' = '$maxRows = 40'
  '150_bulk_evidence_20260711' = '153_bulk_evidence_40_20260711'
  '150_aays1_bulk_photo_polygon_evidence_latest.json' = '153_aays1_bulk_photo_polygon_evidence_40_latest.json'
  '150_aays1_bulk_photo_polygon_evidence_report.md' = '153_aays1_bulk_photo_polygon_evidence_40_report.md'
  'ReadyToSell Bulk Photo and Polygon Evidence - 20 Rows' = 'ReadyToSell Bulk Photo and Polygon Evidence - 40 Rows'
  'Prepare bulk ReadyToSell photo and polygon evidence' = 'Prepare bulk ReadyToSell photo and polygon evidence 40'
  'Record ReadyToSell bulk evidence preparation proof' = 'Record ReadyToSell bulk evidence preparation 40 proof'
}
foreach ($entry in $replacements.GetEnumerator()) { $template = $template.Replace([string]$entry.Key,[string]$entry.Value) }

# Child scripts must never own commit/push in a detached shared-runner worktree.
$workGitPattern = '(?s)\$workPushStatus\s*=\s*''not_attempted''.*?(?=\$afterPhotoEvidence\s*=)'
$template = Replace-Once $template $workGitPattern ('$workPushStatus = ''outer_runner_promotion''; $workCommit = $null' + "`n") '153_work_git_block_not_found'
$proofGitPattern = '(?s)\ntry\s*\{\s*\n\s*& git -C \$repoRoot add -- \$statusRelative.*\z'
$template = Replace-Once $template $proofGitPattern ("`n# Outer canonical runner owns status/report commit, push and remote readback.`n") '153_proof_git_block_not_found'

[System.IO.File]::WriteAllText($tempPath,$template,[System.Text.UTF8Encoding]::new($true))
"[$([DateTimeOffset]::UtcNow.ToString('o'))] START $tempRelative" | Set-Content -LiteralPath $logPath -Encoding UTF8
$previousDetached = $env:AAYS_CANONICAL_DETACHED_WORKTREE
try {
  $env:AAYS_CANONICAL_DETACHED_WORKTREE = 'true'
  & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $tempPath *>> $logPath
  $exitCode = $LASTEXITCODE
  if ($null -eq $exitCode) { $exitCode = 0 }
  if (-not (Test-Path -LiteralPath $expectedPath)) { throw "Expected real output missing after child exit $exitCode: $expectedRelative; log=$logRelative" }
  if ($exitCode -ne 0) { "Child returned $exitCode but expected status exists; outer runner will judge real before/after progress." | Add-Content -LiteralPath $logPath -Encoding UTF8 }
  exit 0
} finally {
  $env:AAYS_CANONICAL_DETACHED_WORKTREE = $previousDetached
}
