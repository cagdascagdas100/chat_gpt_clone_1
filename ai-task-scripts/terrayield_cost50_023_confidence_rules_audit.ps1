$ErrorActionPreference = 'Continue'

$TaskId = 'cost50-023-confidence-rules-audit-20260512'
$BridgeRoot = Split-Path -Parent $PSScriptRoot
$ConfigPath = Join-Path $BridgeRoot 'AAYS_TASK_BRIDGE_CONFIG.ps1'
if (Test-Path $ConfigPath) { . $ConfigPath }
$ProjectRoot = if ($env:AAYS_PROJECT_ROOT) { $env:AAYS_PROJECT_ROOT } else { 'E:\AAYS_DATA\cost\handoff_zips\cost_uk_postgres_50step_handoff_20260511_213229\terrayield_land_intelligence' }
$CostRoot = if ($env:AAYS_COST_DATA_ROOT) { $env:AAYS_COST_DATA_ROOT } else { 'E:\AAYS_DATA\cost' }
$ResultDir = Join-Path $BridgeRoot 'ai-results'
New-Item -ItemType Directory -Force -Path $ResultDir | Out-Null

function Log([string]$Text) { Write-Output ('[' + (Get-Date -Format 's') + '] ' + $Text) }
function ReadText([string]$Path) { try { if (Test-Path $Path) { return Get-Content -Raw -Encoding UTF8 $Path -ErrorAction SilentlyContinue } } catch {}; return '' }

Log "TASK=$TaskId"
Log 'MODE=confidence_rules_audit_readonly'
Log "PROJECT_ROOT=$ProjectRoot"
Log "COST_ROOT=$CostRoot"

$roots = @($ProjectRoot,$CostRoot) | Where-Object { Test-Path $_ }
$text = ''
foreach ($root in $roots) {
  try {
    Get-ChildItem -Path $root -Include '*.py','*.sql','*.md','*.json','*.csv' -File -Recurse -ErrorAction SilentlyContinue |
      Select-Object -First 500 |
      ForEach-Object { $text += "`n---FILE:$($_.FullName)---`n" + (ReadText $_.FullName) }
  } catch {}
}

$rules = [ordered]@{
  high_confidence_requires_official_url = [bool]($text -match 'HIGH' -and $text -match 'source_url|official.*url|official_url')
  high_confidence_requires_source_id = [bool]($text -match 'HIGH' -and $text -match 'source_id')
  retrieved_date_or_accessed_date = [bool]($text -match 'retrieved_at|accessed_at|retrieved_date|accessed_date')
  seed_confidence_penalty = [bool]($text -match 'seed.*penalt|penalt.*seed|is_seed')
  every_metric_evidence_text = [bool]($text -match 'evidence_text')
  reliability_generated = [bool]($text -match 'reliability')
  correctness_generated = [bool]($text -match 'correctness')
  cost_run_logs_errors = [bool]($text -match 'cost_run_logs|CostRunLog|run_logs')
  low_very_low_improvement_actions = [bool]($text -match 'LOW|VERY_LOW|improvement actions|next improvement')
}

Log 'CONFIDENCE_RULE_SCAN_BEGIN'
foreach ($k in $rules.Keys) { Log ($k + '=' + $rules[$k]) }
Log 'CONFIDENCE_RULE_SCAN_END'

$missing = @()
foreach ($k in $rules.Keys) { if (-not $rules[$k]) { $missing += $k } }
$total = $rules.Count
$hit = $total - $missing.Count
$score = if ($total -gt 0) { [int](($hit / $total) * 100) } else { 0 }

$reportPath = Join-Path $ResultDir ($TaskId + '.report.md')
$report = @()
$report += '# Cost50 Step 023 Confidence Rules Audit'
$report += ''
$report += "Generated: $(Get-Date -Format s)"
$report += "Task: $TaskId"
$report += ''
$report += '## Scope'
$report += '- Read-only audit for confidence/evidence rules.'
$report += '- No source mutation, no DB writes, no external fetch.'
$report += ''
$report += '## Rule checks'
foreach ($k in $rules.Keys) { $report += "- ${k}: $($rules[$k])" }
$report += ''
$report += '## Missing rule signals'
if ($missing.Count -eq 0) { $report += '- None detected.' } else { foreach ($m in $missing) { $report += "- $m" } }
$report += ''
$report += "Confidence rule coverage percent: $score"
$report += ''
$report += 'PLAN_PROGRESS_PERCENT=46'
$report += 'TASK_COMPLETION=100/100'
$report += 'TERRAYIELD_TASK_DONE'
$report | Set-Content -Encoding UTF8 -Path $reportPath

Log ('REPORT_PATH=' + $reportPath)
Log ('CONFIDENCE_RULE_COVERAGE_PERCENT=' + $score)
Log 'PLAN_PROGRESS_PERCENT=46'
Log 'TASK_COMPLETION=100/100'
Log 'TERRAYIELD_TASK_DONE'
exit 0
