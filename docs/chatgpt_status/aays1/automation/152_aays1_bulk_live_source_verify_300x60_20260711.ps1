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

if (-not (Test-Path -LiteralPath $basePath)) { throw "Base automation missing: $baseRelative" }
New-Item -ItemType Directory -Force -Path (Split-Path $tempPath),(Split-Path $logPath) | Out-Null
$template = Get-Content -LiteralPath $basePath -Raw -Encoding UTF8
$replacements = [ordered]@{
  "aays1-ready-to-sell-bulk-live-source-verify-120x25-20260711" = "aays1-ready-to-sell-bulk-live-source-verify-300x60-20260711"
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
[System.IO.File]::WriteAllText($tempPath,$template,[System.Text.UTF8Encoding]::new($false))
"[$([DateTimeOffset]::UtcNow.ToString('o'))] START $tempRelative" | Set-Content -LiteralPath $logPath -Encoding UTF8
& powershell.exe -NoProfile -ExecutionPolicy Bypass -File $tempPath *>> $logPath
$exitCode = $LASTEXITCODE
if ($null -eq $exitCode) { $exitCode = 0 }
if ($exitCode -ne 0) { throw "Generated bulk source automation failed with exit code $exitCode; log=$logRelative" }
if (-not (Test-Path -LiteralPath $expectedPath)) { throw "Expected real output missing: $expectedRelative" }
