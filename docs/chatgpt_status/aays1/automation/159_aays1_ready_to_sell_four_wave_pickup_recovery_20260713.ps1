$ErrorActionPreference = 'Continue'
Set-StrictMode -Off

$repoRoot = if ($env:AAYS_REPO_ROOT) { $env:AAYS_REPO_ROOT } else { (& git rev-parse --show-toplevel 2>$null).Trim() }
$taskId = 'aays1-ready-to-sell-four-wave-pickup-recovery-20260713'
$childScriptRelative = 'docs/chatgpt_status/aays1/automation/158_aays1_ready_to_sell_double_wave_and_site_sync_20260713.ps1'
$childStatusRelative = 'docs/chatgpt_status/aays1/status/158_aays1_ready_to_sell_double_wave_and_site_sync_latest.json'
$childReportRelative = 'docs/chatgpt_status/aays1/reports/158_aays1_ready_to_sell_double_wave_and_site_sync_report.md'
$statusRelative = 'docs/chatgpt_status/aays1/status/159_aays1_ready_to_sell_four_wave_pickup_recovery_latest.json'
$reportRelative = 'docs/chatgpt_status/aays1/reports/159_aays1_ready_to_sell_four_wave_pickup_recovery_report.md'
$logRelative = 'docs/chatgpt_status/aays1/runner_outputs/159_four_wave_pickup_recovery.log'

$childScriptPath = Join-Path $repoRoot $childScriptRelative
$childStatusPath = Join-Path $repoRoot $childStatusRelative
$childReportPath = Join-Path $repoRoot $childReportRelative
$statusPath = Join-Path $repoRoot $statusRelative
$reportPath = Join-Path $repoRoot $reportRelative
$logPath = Join-Path $repoRoot $logRelative
New-Item -ItemType Directory -Force -Path (Split-Path $statusPath),(Split-Path $reportPath),(Split-Path $logPath) | Out-Null

function Read-JsonSafe([string]$path) {
  if (-not (Test-Path -LiteralPath $path)) { return $null }
  try {
    $text = Get-Content -LiteralPath $path -Raw -Encoding UTF8
    if ($text.Length -gt 0 -and [int]$text[0] -eq 65279) { $text = $text.Substring(1) }
    return ($text | ConvertFrom-Json)
  } catch { return $null }
}

$startedAt = [DateTimeOffset]::UtcNow.ToString('o')
$previousDetached = $env:AAYS_CANONICAL_DETACHED_WORKTREE
$childExitCode = 1
try {
  if (-not (Test-Path -LiteralPath $childScriptPath)) { throw ('missing_child_script:' + $childScriptRelative) }
  "[$startedAt] START $childScriptRelative" | Set-Content -LiteralPath $logPath -Encoding UTF8
  $env:AAYS_CANONICAL_DETACHED_WORKTREE = 'true'
  & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $childScriptPath *>> $logPath
  $childExitCode = $LASTEXITCODE
  if ($null -eq $childExitCode) { $childExitCode = 0 }
} catch {
  $_.Exception.ToString() | Add-Content -LiteralPath $logPath -Encoding UTF8
} finally {
  $env:AAYS_CANONICAL_DETACHED_WORKTREE = $previousDetached
}

$child = Read-JsonSafe $childStatusPath
if ($child) {
  $child | Add-Member -NotePropertyName continuation_task_id -NotePropertyValue $taskId -Force
  $child | Add-Member -NotePropertyName continuation_of -NotePropertyValue 'aays1-ready-to-sell-double-wave-continuation-20260713' -Force
  $child | Add-Member -NotePropertyName pickup_recovery_child_exit_code -NotePropertyValue $childExitCode -Force
  $child.task_id = $taskId
  $child.final_ready = $false
  $child.product_final_ready = $false
  $child.fake_data = $false
  $child.db_write = $false
  $child.migration = $false
  $child.production_deploy = $false
  $child | ConvertTo-Json -Depth 60 | Set-Content -LiteralPath $statusPath -Encoding UTF8
  $lines = [System.Collections.Generic.List[string]]::new()
  $lines.Add('# AAYS1 ReadyToSell Four-Wave Pickup Recovery')
  $lines.Add('')
  $lines.Add('- Child status: ' + [string]$child.status)
  $lines.Add('- Child exit code: ' + [string]$childExitCode)
  $lines.Add('- Jobs completed with output: ' + [string]$child.jobs_completed_with_output + ' / ' + [string]$child.jobs_total)
  $lines.Add('- Source verified delta: ' + [string]$child.source_verified_delta)
  $lines.Add('- Photo delta: ' + [string]$child.photo_rows_delta)
  $lines.Add('- Polygon delta: ' + [string]$child.polygon_rows_delta)
  $lines.Add('- Evidence-ready delta: ' + [string]$child.evidence_ready_delta)
  $lines.Add('- Site visibility verified: ' + [string]$child.site_visibility_verified)
  if (Test-Path -LiteralPath $childReportPath) {
    $lines.Add('')
    $lines.Add('## Child report')
    foreach ($line in @(Get-Content -LiteralPath $childReportPath -Encoding UTF8)) { $lines.Add($line) }
  }
  $lines.Add('')
  $lines.Add('`final_ready=false`; `product_final_ready=false`; `fake_data=false`; `db_write=false`; `migration=false`; `production_deploy=false`.')
  [System.IO.File]::WriteAllLines($reportPath,$lines,[System.Text.UTF8Encoding]::new($false))
  exit 0
}

$status = [ordered]@{
  task_id = $taskId
  page_key = 'aays1'
  status = 'FOUR_WAVE_PICKUP_RECOVERY_CHILD_OUTPUT_MISSING'
  child_script = $childScriptRelative
  child_exit_code = $childExitCode
  blockers = @('child_status_missing:' + $childStatusRelative)
  started_at = $startedAt
  finished_at = [DateTimeOffset]::UtcNow.ToString('o')
  final_ready = $false
  product_final_ready = $false
  fake_data = $false
  db_write = $false
  migration = $false
  production_deploy = $false
}
$status | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath $statusPath -Encoding UTF8
[System.IO.File]::WriteAllLines($reportPath,@('# AAYS1 ReadyToSell Four-Wave Pickup Recovery','',('- Status: ' + $status.status),('- Child exit code: ' + $childExitCode),('- Blocker: child status missing.'),'','`final_ready=false`; `product_final_ready=false`; `fake_data=false`; `db_write=false`; `migration=false`; `production_deploy=false`.'),[System.Text.UTF8Encoding]::new($false))
exit 1
