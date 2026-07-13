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

if (-not (Test-Path -LiteralPath $basePath)) { throw "Base automation missing: $baseRelative" }
New-Item -ItemType Directory -Force -Path (Split-Path $tempPath),(Split-Path $logPath) | Out-Null
$template = Get-Content -LiteralPath $basePath -Raw -Encoding UTF8
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
[System.IO.File]::WriteAllText($tempPath,$template,[System.Text.UTF8Encoding]::new($true))
"[$([DateTimeOffset]::UtcNow.ToString('o'))] START $tempRelative" | Set-Content -LiteralPath $logPath -Encoding UTF8
$previousDetached = $env:AAYS_CANONICAL_DETACHED_WORKTREE
try {
  $env:AAYS_CANONICAL_DETACHED_WORKTREE = 'true'
  & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $tempPath *>> $logPath
  $exitCode = $LASTEXITCODE
  if ($null -eq $exitCode) { $exitCode = 0 }
  if ($exitCode -ne 0) { throw "Generated evidence automation failed with exit code $exitCode; log=$logRelative" }
  if (-not (Test-Path -LiteralPath $expectedPath)) { throw "Expected real output missing: $expectedRelative" }
} finally {
  $env:AAYS_CANONICAL_DETACHED_WORKTREE = $previousDetached
}
