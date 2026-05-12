$ErrorActionPreference = 'Continue'

$TaskId = 'cost50-025-required-outputs-presence-audit-20260512'
$BridgeRoot = Split-Path -Parent $PSScriptRoot
$ConfigPath = Join-Path $BridgeRoot 'AAYS_TASK_BRIDGE_CONFIG.ps1'
if (Test-Path $ConfigPath) { . $ConfigPath }
$ProjectRoot = if ($env:AAYS_PROJECT_ROOT) { $env:AAYS_PROJECT_ROOT } else { 'E:\AAYS_DATA\cost\handoff_zips\cost_uk_postgres_50step_handoff_20260511_213229\terrayield_land_intelligence' }
$CostRoot = if ($env:AAYS_COST_DATA_ROOT) { $env:AAYS_COST_DATA_ROOT } else { 'E:\AAYS_DATA\cost' }
$ResultDir = Join-Path $BridgeRoot 'ai-results'
New-Item -ItemType Directory -Force -Path $ResultDir | Out-Null

function Log([string]$Text) { Write-Output ('[' + (Get-Date -Format 's') + '] ' + $Text) }
function CountFiles([string]$Root,[string]$Pattern) { try { if (Test-Path $Root) { return @(Get-ChildItem -Path $Root -Filter $Pattern -File -Recurse -ErrorAction SilentlyContinue).Count } } catch {}; return 0 }

Log "TASK=$TaskId"
Log 'MODE=required_outputs_presence_audit_readonly'
Log "PROJECT_ROOT=$ProjectRoot"
Log "COST_ROOT=$CostRoot"

$roots = @($ProjectRoot,$CostRoot) | Where-Object { Test-Path $_ }
$required = [ordered]@{
  source_fetch_manifest_latest_json = 'source_fetch_manifest_latest.json'
  source_fetch_manifest_latest_csv = 'source_fetch_manifest_latest.csv'
  source_facts_extracted_csv = 'source_facts_extracted_*.csv'
  source_facts_scored_csv = 'source_facts_scored.csv'
  source_facts_scored_summary_json = 'source_facts_scored_summary.json'
  aays_cost_menu_payload_latest_json = 'aays_cost_menu_payload_latest.json'
  aays_cost_material_lines_latest_json = 'aays_cost_material_lines_latest.json'
}

$hits = [ordered]@{}
Log 'REQUIRED_OUTPUT_SCAN_BEGIN'
foreach ($k in $required.Keys) {
  $count = 0
  foreach ($r in $roots) { $count += CountFiles $r $required[$k] }
  $hits[$k] = ($count -gt 0)
  Log ($k + '=' + $hits[$k] + ' count=' + $count + ' pattern=' + $required[$k])
}
Log 'REQUIRED_OUTPUT_SCAN_END'

$missing = @()
foreach ($k in $hits.Keys) { if (-not $hits[$k]) { $missing += $k } }
$total = $hits.Count
$ok = $total - $missing.Count
$score = if ($total -gt 0) { [int](($ok / $total) * 100) } else { 0 }

$reportPath = Join-Path $ResultDir ($TaskId + '.report.md')
$report = @()
$report += '# Cost50 Step 025 Required Outputs Presence Audit'
$report += ''
$report += "Generated: $(Get-Date -Format s)"
$report += "Task: $TaskId"
$report += ''
$report += '## Scope'
$report += '- Read-only audit after cleanup.'
$report += '- Checks required demo and UI output artifacts are still present.'
$report += '- No source mutation, no DB writes, no external fetch.'
$report += ''
$report += '## Output checks'
foreach ($k in $hits.Keys) { $report += "- ${k}: $($hits[$k]) :: $($required[$k])" }
$report += ''
$report += '## Missing outputs'
if ($missing.Count -eq 0) { $report += '- None detected.' } else { foreach ($m in $missing) { $report += "- $m" } }
$report += ''
$report += "Required output presence score: $score"
$report += ''
$report += 'PLAN_PROGRESS_PERCENT=50'
$report += 'TASK_COMPLETION=100/100'
$report += 'TERRAYIELD_TASK_DONE'
$report | Set-Content -Encoding UTF8 -Path $reportPath

Log ('REPORT_PATH=' + $reportPath)
Log ('REQUIRED_OUTPUT_PRESENCE_SCORE=' + $score)
Log 'PLAN_PROGRESS_PERCENT=50'
Log 'TASK_COMPLETION=100/100'
Log 'TERRAYIELD_TASK_DONE'
exit 0
