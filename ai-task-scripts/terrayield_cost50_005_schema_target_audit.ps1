$ErrorActionPreference = 'Continue'

$TaskId = 'cost50-005-schema-target-audit-20260512'
$BridgeRoot = Split-Path -Parent $PSScriptRoot
$ConfigPath = Join-Path $BridgeRoot 'AAYS_TASK_BRIDGE_CONFIG.ps1'
if (Test-Path $ConfigPath) { . $ConfigPath }
$ProjectRoot = if ($env:AAYS_PROJECT_ROOT) { $env:AAYS_PROJECT_ROOT } else { 'E:\AAYS_DATA\cost\handoff_zips\cost_uk_postgres_50step_handoff_20260511_213229\terrayield_land_intelligence' }
$ResultDir = Join-Path $BridgeRoot 'ai-results'
New-Item -ItemType Directory -Force -Path $ResultDir | Out-Null

function OutLine([string]$Text) { Write-Output ('[' + (Get-Date -Format 's') + '] ' + $Text) }
function ReadText([string]$Path) { try { if (Test-Path $Path) { return Get-Content -Raw -Encoding UTF8 $Path -ErrorAction SilentlyContinue } } catch {}; return '' }

OutLine "TASK=$TaskId"
OutLine 'MODE=cost50_schema_target_audit_readonly'
OutLine "BRIDGE_ROOT=$BridgeRoot"
OutLine "PROJECT_ROOT=$ProjectRoot"

$files = @(
  'app\db\models.py',
  'alembic\env.py',
  'app\main.py',
  'docs\chatgpt_handoff\cost_uk_postgres_50step\COST50_01_MASTER_PLAN_50_STEPS_TR.md',
  'docs\chatgpt_handoff\cost_uk_postgres_50step\COST50_12_COMMAND_RUNBOOK_TR.txt'
)

$combined = ''
$found = [ordered]@{}
OutLine 'READ_FILES_BEGIN'
foreach ($rel in $files) {
  $full = Join-Path $ProjectRoot $rel
  $exists = Test-Path $full
  $found[$rel] = $exists
  OutLine ($rel + '=' + $exists)
  if ($exists) { $combined += "`n---FILE:$rel---`n" + (ReadText $full) }
}
OutLine 'READ_FILES_END'

$requiredEntities = @(
  'cost_sources',
  'cost_source_fetch_runs',
  'cost_facts',
  'cost_fact_scores',
  'cost_estimates',
  'cost_estimate_lines',
  'cost_run_logs'
)

OutLine 'TARGET_ENTITY_SCAN_BEGIN'
$entityHits = [ordered]@{}
foreach ($e in $requiredEntities) {
  $hit = [bool]($combined -match [regex]::Escape($e))
  $entityHits[$e] = $hit
  OutLine ($e + '=' + $hit)
}
OutLine 'TARGET_ENTITY_SCAN_END'

$qualityRules = [ordered]@{
  official_source_url = [bool]($combined -match 'source_url|official.*url|GOV|ONS|DBT|HMRC|HMLR')
  source_id = [bool]($combined -match 'source_id')
  confidence = [bool]($combined -match 'confidence')
  seed_penalty = [bool]($combined -match 'seed')
  evidence_text = [bool]($combined -match 'evidence_text')
  reliability = [bool]($combined -match 'reliability')
  correctness = [bool]($combined -match 'correctness')
  cost_run_logs = [bool]($combined -match 'cost_run_logs')
}

OutLine 'QUALITY_RULE_SCAN_BEGIN'
foreach ($k in $qualityRules.Keys) { OutLine ($k + '=' + $qualityRules[$k]) }
OutLine 'QUALITY_RULE_SCAN_END'

$hitCount = 0
$total = $requiredEntities.Count + $qualityRules.Count
foreach ($e in $requiredEntities) { if ($entityHits[$e]) { $hitCount++ } }
foreach ($k in $qualityRules.Keys) { if ($qualityRules[$k]) { $hitCount++ } }
$readiness = if ($total -gt 0) { [int](($hitCount / $total) * 100) } else { 0 }

$reportPath = Join-Path $ResultDir ($TaskId + '.report.md')
$report = @()
$report += '# Cost50 Step 005 Schema Target Audit'
$report += ''
$report += "Generated: $(Get-Date -Format s)"
$report += "Task: $TaskId"
$report += ''
$report += '## Scope'
$report += '- Read-only audit before PostgreSQL migration draft.'
$report += '- No source mutation and no DB writes.'
$report += ''
$report += '## Required files'
foreach ($rel in $found.Keys) { $report += "- ${rel}: $($found[$rel])" }
$report += ''
$report += '## Target entities mentioned'
foreach ($e in $requiredEntities) { $report += "- ${e}: $($entityHits[$e])" }
$report += ''
$report += '## Quality rule signals'
foreach ($k in $qualityRules.Keys) { $report += "- ${k}: $($qualityRules[$k])" }
$report += ''
$report += "Schema readiness score: $readiness"
$report += ''
$report += '## Next recommendation'
$report += '- Step 006 should create a migration draft for missing cost tables only after confirming model/alembic conventions.'
$report += ''
$report += 'PLAN_PROGRESS_PERCENT=10'
$report += 'TASK_COMPLETION=100/100'
$report += 'TERRAYIELD_TASK_DONE'
$report | Set-Content -Encoding UTF8 -Path $reportPath

OutLine ('REPORT_PATH=' + $reportPath)
OutLine ('SCHEMA_READINESS_SCORE=' + $readiness)
OutLine 'PLAN_PROGRESS_PERCENT=10'
OutLine 'TASK_COMPLETION=100/100'
OutLine 'TERRAYIELD_TASK_DONE'
exit 0
