$ErrorActionPreference = 'Continue'

$TaskId = 'cost50-012-db-model-gap-audit-20260512'
$BridgeRoot = Split-Path -Parent $PSScriptRoot
$ConfigPath = Join-Path $BridgeRoot 'AAYS_TASK_BRIDGE_CONFIG.ps1'
if (Test-Path $ConfigPath) { . $ConfigPath }
$ProjectRoot = if ($env:AAYS_PROJECT_ROOT) { $env:AAYS_PROJECT_ROOT } else { 'E:\AAYS_DATA\cost\handoff_zips\cost_uk_postgres_50step_handoff_20260511_213229\terrayield_land_intelligence' }
$ResultDir = Join-Path $BridgeRoot 'ai-results'
New-Item -ItemType Directory -Force -Path $ResultDir | Out-Null

function Log([string]$Text) { Write-Output ('[' + (Get-Date -Format 's') + '] ' + $Text) }
function ReadText([string]$Path) { try { if (Test-Path $Path) { return Get-Content -Raw -Encoding UTF8 $Path -ErrorAction SilentlyContinue } } catch {}; return '' }

Log "TASK=$TaskId"
Log 'MODE=db_model_gap_audit_readonly'
Log "PROJECT_ROOT=$ProjectRoot"

$modelPath = Join-Path $ProjectRoot 'app\db\models.py'
$alembicDir = Join-Path $ProjectRoot 'alembic\versions'
$modelText = ReadText $modelPath
$migrationText = ''
try {
  if (Test-Path $alembicDir) {
    Get-ChildItem -Path $alembicDir -Filter '*.py' -File -ErrorAction SilentlyContinue | ForEach-Object {
      $migrationText += "`n---MIGRATION:$($_.Name)---`n" + (ReadText $_.FullName)
    }
  }
} catch {}

$requiredTables = [ordered]@{
  cost_sources = 'official source registry with URL, source_id, priority, source_type'
  cost_source_fetch_runs = 'source fetch manifest run tracking'
  cost_facts = 'extracted source facts using template schema fields'
  cost_fact_scores = 'reliability, correctness, confidence, seed penalty scoring'
  cost_estimates = 'estimate header per parcel/run'
  cost_estimate_lines = 'itemized cost lines and material quantities'
  cost_run_logs = 'error and audit log for every failure path'
}

$tableHits = [ordered]@{}
Log 'TABLE_GAP_SCAN_BEGIN'
foreach ($t in $requiredTables.Keys) {
  $hit = [bool](($modelText + $migrationText) -match [regex]::Escape($t))
  $tableHits[$t] = $hit
  Log ($t + '=' + $hit + ' purpose=' + $requiredTables[$t])
}
Log 'TABLE_GAP_SCAN_END'

$fieldSignals = [ordered]@{
  source_id = [bool](($modelText + $migrationText) -match 'source_id')
  source_url = [bool](($modelText + $migrationText) -match 'source_url|url')
  evidence_text = [bool](($modelText + $migrationText) -match 'evidence_text')
  reliability = [bool](($modelText + $migrationText) -match 'reliability')
  correctness = [bool](($modelText + $migrationText) -match 'correctness')
  confidence = [bool](($modelText + $migrationText) -match 'confidence')
  is_seed = [bool](($modelText + $migrationText) -match 'seed|is_seed')
  material_quantity = [bool](($modelText + $migrationText) -match 'material.*quantity|quantity.*material|material_qty')
}

Log 'FIELD_SIGNAL_SCAN_BEGIN'
foreach ($k in $fieldSignals.Keys) { Log ($k + '=' + $fieldSignals[$k]) }
Log 'FIELD_SIGNAL_SCAN_END'

$missingTables = @()
foreach ($t in $tableHits.Keys) { if (-not $tableHits[$t]) { $missingTables += $t } }
$missingFields = @()
foreach ($f in $fieldSignals.Keys) { if (-not $fieldSignals[$f]) { $missingFields += $f } }

$score = 0
$total = $tableHits.Count + $fieldSignals.Count
foreach ($t in $tableHits.Keys) { if ($tableHits[$t]) { $score++ } }
foreach ($f in $fieldSignals.Keys) { if ($fieldSignals[$f]) { $score++ } }
$coverage = if ($total -gt 0) { [int](($score / $total) * 100) } else { 0 }

$reportPath = Join-Path $ResultDir ($TaskId + '.report.md')
$report = @()
$report += '# Cost50 Step 012 DB Model Gap Audit'
$report += ''
$report += "Generated: $(Get-Date -Format s)"
$report += "Task: $TaskId"
$report += ''
$report += '## Scope'
$report += '- Read-only DB model and migration gap audit.'
$report += '- No source mutation, no DB writes, no external fetch.'
$report += ''
$report += '## Required tables'
foreach ($t in $requiredTables.Keys) { $report += "- ${t}: $($tableHits[$t]) :: $($requiredTables[$t])" }
$report += ''
$report += '## Required field signals'
foreach ($f in $fieldSignals.Keys) { $report += "- ${f}: $($fieldSignals[$f])" }
$report += ''
$report += '## Missing tables'
if ($missingTables.Count -eq 0) { $report += '- None detected.' } else { foreach ($m in $missingTables) { $report += "- $m" } }
$report += ''
$report += '## Missing field signals'
if ($missingFields.Count -eq 0) { $report += '- None detected.' } else { foreach ($m in $missingFields) { $report += "- $m" } }
$report += ''
$report += "DB model coverage percent: $coverage"
$report += ''
$report += 'PLAN_PROGRESS_PERCENT=24'
$report += 'TASK_COMPLETION=100/100'
$report += 'TERRAYIELD_TASK_DONE'
$report | Set-Content -Encoding UTF8 -Path $reportPath

Log ('REPORT_PATH=' + $reportPath)
Log ('DB_MODEL_COVERAGE_PERCENT=' + $coverage)
Log 'PLAN_PROGRESS_PERCENT=24'
Log 'TASK_COMPLETION=100/100'
Log 'TERRAYIELD_TASK_DONE'
exit 0
